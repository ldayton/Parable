function range(start: number, end?: number, step?: number): number[] {
  if (end === undefined) { end = start; start = 0; }
  if (step === undefined) { step = 1; }
  const result: number[] = [];
  if (step > 0) {
    for (let i = start; i < end; i += step) result.push(i);
  } else {
    for (let i = start; i > end; i += step) result.push(i);
  }
  return result;
}
const ANSI_C_ESCAPES: Map<string, number> = new Map([["a", 7], ["b", 8], ["e", 27], ["E", 27], ["f", 12], ["n", 10], ["r", 13], ["t", 9], ["v", 11], ["\\", 92], ["\"", 34], ["?", 63]]);
const TokenType_EOF: number = 0;
const TokenType_WORD: number = 1;
const TokenType_NEWLINE: number = 2;
const TokenType_SEMI: number = 10;
const TokenType_PIPE: number = 11;
const TokenType_AMP: number = 12;
const TokenType_LPAREN: number = 13;
const TokenType_RPAREN: number = 14;
const TokenType_LBRACE: number = 15;
const TokenType_RBRACE: number = 16;
const TokenType_LESS: number = 17;
const TokenType_GREATER: number = 18;
const TokenType_AND_AND: number = 30;
const TokenType_OR_OR: number = 31;
const TokenType_SEMI_SEMI: number = 32;
const TokenType_SEMI_AMP: number = 33;
const TokenType_SEMI_SEMI_AMP: number = 34;
const TokenType_LESS_LESS: number = 35;
const TokenType_GREATER_GREATER: number = 36;
const TokenType_LESS_AMP: number = 37;
const TokenType_GREATER_AMP: number = 38;
const TokenType_LESS_GREATER: number = 39;
const TokenType_GREATER_PIPE: number = 40;
const TokenType_LESS_LESS_MINUS: number = 41;
const TokenType_LESS_LESS_LESS: number = 42;
const TokenType_AMP_GREATER: number = 43;
const TokenType_AMP_GREATER_GREATER: number = 44;
const TokenType_PIPE_AMP: number = 45;
const TokenType_IF: number = 50;
const TokenType_THEN: number = 51;
const TokenType_ELSE: number = 52;
const TokenType_ELIF: number = 53;
const TokenType_FI: number = 54;
const TokenType_CASE: number = 55;
const TokenType_ESAC: number = 56;
const TokenType_FOR: number = 57;
const TokenType_WHILE: number = 58;
const TokenType_UNTIL: number = 59;
const TokenType_DO: number = 60;
const TokenType_DONE: number = 61;
const TokenType_IN: number = 62;
const TokenType_FUNCTION: number = 63;
const TokenType_SELECT: number = 64;
const TokenType_COPROC: number = 65;
const TokenType_TIME: number = 66;
const TokenType_BANG: number = 67;
const TokenType_LBRACKET_LBRACKET: number = 68;
const TokenType_RBRACKET_RBRACKET: number = 69;
const TokenType_ASSIGNMENT_WORD: number = 80;
const TokenType_NUMBER: number = 81;
const ParserStateFlags_NONE: number = 0;
const ParserStateFlags_PST_CASEPAT: number = 1;
const ParserStateFlags_PST_CMDSUBST: number = 2;
const ParserStateFlags_PST_CASESTMT: number = 4;
const ParserStateFlags_PST_CONDEXPR: number = 8;
const ParserStateFlags_PST_COMPASSIGN: number = 16;
const ParserStateFlags_PST_ARITH: number = 32;
const ParserStateFlags_PST_HEREDOC: number = 64;
const ParserStateFlags_PST_REGEXP: number = 128;
const ParserStateFlags_PST_EXTPAT: number = 256;
const ParserStateFlags_PST_SUBSHELL: number = 512;
const ParserStateFlags_PST_REDIRLIST: number = 1024;
const ParserStateFlags_PST_COMMENT: number = 2048;
const ParserStateFlags_PST_EOFTOKEN: number = 4096;
const DolbraceState_NONE: number = 0;
const DolbraceState_PARAM: number = 1;
const DolbraceState_OP: number = 2;
const DolbraceState_WORD: number = 4;
const DolbraceState_QUOTE: number = 64;
const DolbraceState_QUOTE2: number = 128;
const MatchedPairFlags_NONE: number = 0;
const MatchedPairFlags_DQUOTE: number = 1;
const MatchedPairFlags_DOLBRACE: number = 2;
const MatchedPairFlags_COMMAND: number = 4;
const MatchedPairFlags_ARITH: number = 8;
const MatchedPairFlags_ALLOWESC: number = 16;
const MatchedPairFlags_EXTGLOB: number = 32;
const MatchedPairFlags_FIRSTCLOSE: number = 64;
const MatchedPairFlags_ARRAYSUB: number = 128;
const MatchedPairFlags_BACKQUOTE: number = 256;
const ParseContext_NORMAL: number = 0;
const ParseContext_COMMAND_SUB: number = 1;
const ParseContext_ARITHMETIC: number = 2;
const ParseContext_CASE_PATTERN: number = 3;
const ParseContext_BRACE_EXPANSION: number = 4;
const RESERVED_WORDS: Set<string> = new Set(["if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"]);
const COND_UNARY_OPS: Set<string> = new Set(["-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"]);
const COND_BINARY_OPS: Set<string> = new Set(["==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"]);
const COMPOUND_KEYWORDS: Set<string> = new Set(["while", "until", "for", "if", "case", "select"]);
const ASSIGNMENT_BUILTINS: Set<string> = new Set(["alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"]);
const _SMP_LITERAL: number = 1;
const _SMP_PAST_OPEN: number = 2;
const WORD_CTX_NORMAL: number = 0;
const WORD_CTX_COND: number = 1;
const WORD_CTX_REGEX: number = 2;

interface Node {
  kind: string;
  getKind(): string;
  toSexp(): string;
}

class ParseError {
  message: string;
  pos: number;
  line: number;

  constructor(message: string = "", pos: number = 0, line: number = 0) {
    this.message = message;
    this.pos = pos;
    this.line = line;
  }

  FormatMessage(): string {
    if (this.line !== 0 && this.pos !== 0) {
      return `Parse error at line %v, position %v: %v`;
    } else {
      if (this.pos !== 0) {
        return `Parse error at position %v: %v`;
      }
    }
    return `Parse error: %v`;
  }
}

class MatchedPairError {
}

class TokenType {
}

class Token {
  typeName: number;
  value: string;
  pos: number;
  parts: Node[];
  word: Word;

  constructor(typeName: number = 0, value: string = "", pos: number = 0, parts: Node[] = [], word: Word = null) {
    this.typeName = typeName;
    this.value = value;
    this.pos = pos;
    this.parts = parts;
    this.word = word;
  }

  Repr(): string {
    if (this.word !== null) {
      return `Token(%v, %v, %v, word=%v)`;
    }
    if (this.parts.length > 0) {
      return `Token(%v, %v, %v, parts=%v)`;
    }
    return `Token(%v, %v, %v)`;
  }
}

class ParserStateFlags {
}

class DolbraceState {
}

class MatchedPairFlags {
}

class SavedParserState {
  parserState: number;
  dolbraceState: number;
  pendingHeredocs: Node[];
  ctxStack: ParseContext[];
  eofToken: string;

  constructor(parserState: number = 0, dolbraceState: number = 0, pendingHeredocs: Node[] = [], ctxStack: ParseContext[] = [], eofToken: string = "") {
    this.parserState = parserState;
    this.dolbraceState = dolbraceState;
    this.pendingHeredocs = pendingHeredocs;
    this.ctxStack = ctxStack;
    this.eofToken = eofToken;
  }
}

class QuoteState {
  single: boolean;
  double: boolean;
  Stack: [boolean, boolean][];

  constructor(single: boolean = false, double: boolean = false, Stack: [boolean, boolean][] = []) {
    this.single = single;
    this.double = double;
    this.Stack = Stack;
  }

  push(): void {
    this.Stack.push([this.single, this.double]);
    this.single = false;
    this.double = false;
  }

  pop(): void {
    if (this.Stack.length > 0) {
      {
        var Entry: any = this.Stack[this.Stack.length - 1];
        this.Stack = this.Stack.slice(0, this.Stack.length - 1);
        this.single = Entry[0];
        this.double = Entry[1];
      }
    }
  }

  inQuotes(): boolean {
    return this.single || this.double;
  }

  copy(): QuoteState {
    var qs: any = newQuoteState();
    qs.single = this.single;
    qs.double = this.double;
    qs.Stack = this.Stack.slice();
    return qs;
  }

  outerDouble(): boolean {
    if (this.Stack.length === 0) {
      return false;
    }
    return this.Stack[this.Stack.length - 1][1];
  }
}

class ParseContext {
  kind: number;
  parenDepth: number;
  braceDepth: number;
  bracketDepth: number;
  caseDepth: number;
  arithDepth: number;
  arithParenDepth: number;
  quote: QuoteState;

  constructor(kind: number = 0, parenDepth: number = 0, braceDepth: number = 0, bracketDepth: number = 0, caseDepth: number = 0, arithDepth: number = 0, arithParenDepth: number = 0, quote: QuoteState = null) {
    this.kind = kind;
    this.parenDepth = parenDepth;
    this.braceDepth = braceDepth;
    this.bracketDepth = bracketDepth;
    this.caseDepth = caseDepth;
    this.arithDepth = arithDepth;
    this.arithParenDepth = arithParenDepth;
    this.quote = quote;
  }

  copy(): ParseContext {
    var ctx: any = newParseContext(this.kind);
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
  Stack: ParseContext[];

  constructor(Stack: ParseContext[] = []) {
    this.Stack = Stack;
  }

  getCurrent(): ParseContext {
    return this.Stack[this.Stack.length - 1];
  }

  push(kind: number): void {
    this.Stack.push(newParseContext(kind));
  }

  pop(): ParseContext {
    if (this.Stack.length > 1) {
      return this.Stack.pop();
    }
    return this.Stack[0];
  }

  copyStack(): ParseContext[] {
    var result: any = [];
    for (const ctx of this.Stack) {
      result.push(ctx.copy());
    }
    return result;
  }

  restoreFrom(savedStack: ParseContext[]): void {
    var result: any = [];
    for (const ctx of savedStack) {
      result.push(ctx.copy());
    }
    this.Stack = result;
  }
}

class Lexer {
  RESERVED_WORDS: Map<string, number>;
  source: string;
  pos: number;
  length: number;
  quote: QuoteState;
  TokenCache: Token | null;
  ParserState: number;
  DolbraceState: number;
  PendingHeredocs: Node[];
  Extglob: boolean;
  Parser: Parser | null;
  EofToken: string;
  LastReadToken: Token | null;
  WordContext: number;
  AtCommandStart: boolean;
  InArrayLiteral: boolean;
  InAssignBuiltin: boolean;
  PostReadPos: number;
  CachedWordContext: number;
  CachedAtCommandStart: boolean;
  CachedInArrayLiteral: boolean;
  CachedInAssignBuiltin: boolean;

  constructor(RESERVED_WORDS: Map<string, number> = new Map(), source: string = "", pos: number = 0, length: number = 0, quote: QuoteState = null, TokenCache: Token | null = null, ParserState: number = 0, DolbraceState: number = 0, PendingHeredocs: Node[] = [], Extglob: boolean = false, Parser: Parser | null = null, EofToken: string = "", LastReadToken: Token | null = null, WordContext: number = 0, AtCommandStart: boolean = false, InArrayLiteral: boolean = false, InAssignBuiltin: boolean = false, PostReadPos: number = 0, CachedWordContext: number = 0, CachedAtCommandStart: boolean = false, CachedInArrayLiteral: boolean = false, CachedInAssignBuiltin: boolean = false) {
    this.RESERVED_WORDS = RESERVED_WORDS;
    this.source = source;
    this.pos = pos;
    this.length = length;
    this.quote = quote;
    this.TokenCache = TokenCache;
    this.ParserState = ParserState;
    this.DolbraceState = DolbraceState;
    this.PendingHeredocs = PendingHeredocs;
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

  peek(): string {
    if (this.pos >= this.length) {
      return "";
    }
    return (this.source[this.pos] as unknown as string);
  }

  advance(): string {
    if (this.pos >= this.length) {
      return "";
    }
    var c: any = (this.source[this.pos] as unknown as string);
    this.pos += 1;
    return c;
  }

  atEnd(): boolean {
    return this.pos >= this.length;
  }

  lookahead(n: number): string {
    return Substring(this.source, this.pos, this.pos + n);
  }

  isMetachar(c: string): boolean {
    return "|&;()<> \t\n".includes(c);
  }

  ReadOperator(): Token {
    var start: any = this.pos;
    var c: any = this.peek();
    if (c === "") {
      return null;
    }
    var two: any = this.lookahead(2);
    var three: any = this.lookahead(3);
    if (three === ";;&") {
      this.pos += 3;
      return new Token(TokenType_SEMI_SEMI_AMP as any, three as any, start as any);
    }
    if (three === "<<-") {
      this.pos += 3;
      return new Token(TokenType_LESS_LESS_MINUS as any, three as any, start as any);
    }
    if (three === "<<<") {
      this.pos += 3;
      return new Token(TokenType_LESS_LESS_LESS as any, three as any, start as any);
    }
    if (three === "&>>") {
      this.pos += 3;
      return new Token(TokenType_AMP_GREATER_GREATER as any, three as any, start as any);
    }
    if (two === "&&") {
      this.pos += 2;
      return new Token(TokenType_AND_AND as any, two as any, start as any);
    }
    if (two === "||") {
      this.pos += 2;
      return new Token(TokenType_OR_OR as any, two as any, start as any);
    }
    if (two === ";;") {
      this.pos += 2;
      return new Token(TokenType_SEMI_SEMI as any, two as any, start as any);
    }
    if (two === ";&") {
      this.pos += 2;
      return new Token(TokenType_SEMI_AMP as any, two as any, start as any);
    }
    if (two === "<<") {
      this.pos += 2;
      return new Token(TokenType_LESS_LESS as any, two as any, start as any);
    }
    if (two === ">>") {
      this.pos += 2;
      return new Token(TokenType_GREATER_GREATER as any, two as any, start as any);
    }
    if (two === "<&") {
      this.pos += 2;
      return new Token(TokenType_LESS_AMP as any, two as any, start as any);
    }
    if (two === ">&") {
      this.pos += 2;
      return new Token(TokenType_GREATER_AMP as any, two as any, start as any);
    }
    if (two === "<>") {
      this.pos += 2;
      return new Token(TokenType_LESS_GREATER as any, two as any, start as any);
    }
    if (two === ">|") {
      this.pos += 2;
      return new Token(TokenType_GREATER_PIPE as any, two as any, start as any);
    }
    if (two === "&>") {
      this.pos += 2;
      return new Token(TokenType_AMP_GREATER as any, two as any, start as any);
    }
    if (two === "|&") {
      this.pos += 2;
      return new Token(TokenType_PIPE_AMP as any, two as any, start as any);
    }
    if (c === ";") {
      this.pos += 1;
      return new Token(TokenType_SEMI as any, c as any, start as any);
    }
    if (c === "|") {
      this.pos += 1;
      return new Token(TokenType_PIPE as any, c as any, start as any);
    }
    if (c === "&") {
      this.pos += 1;
      return new Token(TokenType_AMP as any, c as any, start as any);
    }
    if (c === "(") {
      if (this.WordContext === WORD_CTX_REGEX) {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_LPAREN as any, c as any, start as any);
    }
    if (c === ")") {
      if (this.WordContext === WORD_CTX_REGEX) {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_RPAREN as any, c as any, start as any);
    }
    if (c === "<") {
      if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_LESS as any, c as any, start as any);
    }
    if (c === ">") {
      if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_GREATER as any, c as any, start as any);
    }
    if (c === "\n") {
      this.pos += 1;
      return new Token(TokenType_NEWLINE as any, c as any, start as any);
    }
    return null;
  }

  skipBlanks(): void {
    while (this.pos < this.length) {
      var c: any = (this.source[this.pos] as unknown as string);
      if (c !== " " && c !== "\t") {
        break;
      }
      this.pos += 1;
    }
  }

  SkipComment(): boolean {
    if (this.pos >= this.length) {
      return false;
    }
    if ((this.source[this.pos] as unknown as string) !== "#") {
      return false;
    }
    if (this.quote.inQuotes()) {
      return false;
    }
    if (this.pos > 0) {
      var prev: any = (this.source[this.pos - 1] as unknown as string);
      if (!" \t\n;|&(){}".includes(prev)) {
        return false;
      }
    }
    while (this.pos < this.length && (this.source[this.pos] as unknown as string) !== "\n") {
      this.pos += 1;
    }
    return true;
  }

  ReadSingleQuote(start: number): [string, boolean] {
    var chars: any = ["'"];
    var sawNewline: any = false;
    while (this.pos < this.length) {
      var c: any = (this.source[this.pos] as unknown as string);
      if (c === "\n") {
        sawNewline = true;
      }
      chars.push(c);
      this.pos += 1;
      if (c === "'") {
        return [chars.join(""), sawNewline];
      }
    }
    throw new Error(`${"Unterminated single quote"} at position ${start}`)
  }

  IsWordTerminator(ctx: number, ch: string, bracketDepth: number, parenDepth: number): boolean {
    if (ctx === WORD_CTX_REGEX) {
      if (ch === "]" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "]") {
        return true;
      }
      if (ch === "&" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "&") {
        return true;
      }
      if (ch === ")" && parenDepth === 0) {
        return true;
      }
      return IsWhitespace(ch) && parenDepth === 0;
    }
    if (ctx === WORD_CTX_COND) {
      if (ch === "]" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "]") {
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
      if (IsRedirectChar(ch) && !(this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(")) {
        return true;
      }
      return IsWhitespace(ch);
    }
    if ((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0 && this.EofToken !== "" && ch === this.EofToken && bracketDepth === 0) {
      return true;
    }
    if (IsRedirectChar(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
      return false;
    }
    return IsMetachar(ch) && bracketDepth === 0;
  }

  ReadBracketExpression(chars: string[], parts: Node[], forRegex: boolean, parenDepth: number): boolean {
    if (forRegex) {
      var scan: any = this.pos + 1;
      if (scan < this.length && (this.source[scan] as unknown as string) === "^") {
        scan += 1;
      }
      if (scan < this.length && (this.source[scan] as unknown as string) === "]") {
        scan += 1;
      }
      var bracketWillClose: any = false;
      while (scan < this.length) {
        var sc: any = (this.source[scan] as unknown as string);
        if (sc === "]" && scan + 1 < this.length && (this.source[scan + 1] as unknown as string) === "]") {
          break;
        }
        if (sc === ")" && parenDepth > 0) {
          break;
        }
        if (sc === "&" && scan + 1 < this.length && (this.source[scan + 1] as unknown as string) === "&") {
          break;
        }
        if (sc === "]") {
          bracketWillClose = true;
          break;
        }
        if (sc === "[" && scan + 1 < this.length && (this.source[scan + 1] as unknown as string) === ":") {
          scan += 2;
          while (scan < this.length && !((this.source[scan] as unknown as string) === ":" && scan + 1 < this.length && (this.source[scan + 1] as unknown as string) === "]")) {
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
      var nextCh: any = (this.source[this.pos + 1] as unknown as string);
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
      var c: any = this.peek();
      if (c === "]") {
        chars.push(this.advance());
        break;
      }
      if (c === "[" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === ":") {
        chars.push(this.advance());
        chars.push(this.advance());
        while (!this.atEnd() && !(this.peek() === ":" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "]")) {
          chars.push(this.advance());
        }
        if (!this.atEnd()) {
          chars.push(this.advance());
          chars.push(this.advance());
        }
      } else {
        if (!forRegex && c === "[" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "=") {
          chars.push(this.advance());
          chars.push(this.advance());
          while (!this.atEnd() && !(this.peek() === "=" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "]")) {
            chars.push(this.advance());
          }
          if (!this.atEnd()) {
            chars.push(this.advance());
            chars.push(this.advance());
          }
        } else {
          if (!forRegex && c === "[" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === ".") {
            chars.push(this.advance());
            chars.push(this.advance());
            while (!this.atEnd() && !(this.peek() === "." && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "]")) {
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

  ParseMatchedPair(openChar: string, closeChar: string, flags: number, initialWasDollar: boolean): string {
    var start: any = this.pos;
    var count: any = 1;
    var chars: any = [];
    var passNext: any = false;
    var wasDollar: any = initialWasDollar;
    var wasGtlt: any = false;
    while (count > 0) {
      if (this.atEnd()) {
        throw new Error(`${`unexpected EOF while looking for matching \`%v'`} at position ${start}`)
      }
      var ch: any = this.advance();
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
          var quoteFlags: any = wasDollar ? flags | MatchedPairFlags_ALLOWESC : flags;
          var nested: any = this.ParseMatchedPair("'", "'", quoteFlags, false);
          chars.push(nested);
          chars.push("'");
          wasDollar = false;
          wasGtlt = false;
          continue;
        } else {
          if (ch === "\"") {
            chars.push(ch);
            var nested: any = this.ParseMatchedPair("\"", "\"", flags | MatchedPairFlags_DQUOTE, false);
            chars.push(nested);
            chars.push("\"");
            wasDollar = false;
            wasGtlt = false;
            continue;
          } else {
            if (ch === "`") {
              chars.push(ch);
              var nested: any = this.ParseMatchedPair("`", "`", flags, false);
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
        var nextCh: any = this.peek();
        if (wasDollar) {
          chars.push(ch);
          wasDollar = false;
          wasGtlt = false;
          continue;
        }
        if (nextCh === "{") {
          if ((flags & MatchedPairFlags_ARITH) !== 0) {
            var afterBracePos: any = this.pos + 1;
            if (afterBracePos >= this.length || !IsFunsubChar((this.source[afterBracePos] as unknown as string))) {
              chars.push(ch);
              wasDollar = true;
              wasGtlt = false;
              continue;
            }
          }
          this.pos -= 1;
          this.SyncToParser();
          var inDquote: any = (flags & MatchedPairFlags_DQUOTE) !== 0;
          var [paramNode, paramText]: any = this.Parser.ParseParamExpansion(inDquote);
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
          if (nextCh === "(") {
            this.pos -= 1;
            this.SyncToParser();
            if (this.pos + 2 < this.length && (this.source[this.pos + 2] as unknown as string) === "(") {
              var [arithNode, arithText]: any = this.Parser.ParseArithmeticExpansion();
              this.SyncFromParser();
              if (arithNode !== null) {
                chars.push(arithText);
                wasDollar = false;
                wasGtlt = false;
              } else {
                this.SyncToParser();
                var [cmdNode, cmdText]: any = this.Parser.ParseCommandSubstitution();
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
              var [cmdNode, cmdText]: any = this.Parser.ParseCommandSubstitution();
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
              var [arithNode, arithText]: any = this.Parser.ParseDeprecatedArithmetic();
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
      if (ch === "(" && wasGtlt && (flags & (MatchedPairFlags_DOLBRACE | MatchedPairFlags_ARRAYSUB)) !== 0) {
        {
          var direction: any = chars[chars.length - 1];
          chars = chars.slice(0, chars.length - 1);
        }
        this.pos -= 1;
        this.SyncToParser();
        var [procsubNode, procsubText]: any = this.Parser.ParseProcessSubstitution();
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

  CollectParamArgument(flags: number, wasDollar: boolean): string {
    return this.ParseMatchedPair("{", "}", flags | MatchedPairFlags_DOLBRACE, wasDollar);
  }

  ReadWordInternal(ctx: number, atCommandStart: boolean, inArrayLiteral: boolean, inAssignBuiltin: boolean): Word {
    var start: any = this.pos;
    var chars: any = [];
    var parts: any = [];
    var bracketDepth: any = 0;
    var bracketStartPos: any = -1;
    var seenEquals: any = false;
    var parenDepth: any = 0;
    while (!this.atEnd()) {
      var ch: any = this.peek();
      if (ctx === WORD_CTX_REGEX) {
        if (ch === "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "\n") {
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
          var prevChar: any = chars[chars.length - 1];
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
        var forRegex: any = ctx === WORD_CTX_REGEX;
        if (this.ReadBracketExpression(chars, parts, forRegex, parenDepth)) {
          continue;
        }
        chars.push(this.advance());
        continue;
      }
      if (ctx === WORD_CTX_COND && ch === "(") {
        if (this.Extglob && chars.length > 0 && IsExtglobPrefix(chars[chars.length - 1])) {
          chars.push(this.advance());
          var content: any = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
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
        var trackNewline: any = ctx === WORD_CTX_NORMAL;
        var sawNewline: any;
        [content, sawNewline] = this.ReadSingleQuote(start);
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
          var inSingleInDquote: any = false;
          while (!this.atEnd() && (inSingleInDquote || this.peek() !== "\"")) {
            var c: any = this.peek();
            if (inSingleInDquote) {
              chars.push(this.advance());
              if (c === "'") {
                inSingleInDquote = false;
              }
              continue;
            }
            if (c === "\\" && this.pos + 1 < this.length) {
              var nextC: any = (this.source[this.pos + 1] as unknown as string);
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
                  var [cmdsubResult0, cmdsubResult1]: any = this.Parser.ParseBacktickSubstitution();
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
            throw new Error(`${"Unterminated double quote"} at position ${start}`)
          }
          chars.push(this.advance());
        } else {
          var handleLineContinuation: any = ctx === WORD_CTX_COND;
          this.SyncToParser();
          this.Parser.ScanDoubleQuote(chars, parts, start, handleLineContinuation);
          this.SyncFromParser();
        }
        continue;
      }
      if (ch === "\\" && this.pos + 1 < this.length) {
        var nextCh: any = (this.source[this.pos + 1] as unknown as string);
        if (ctx !== WORD_CTX_REGEX && nextCh === "\n") {
          this.advance();
          this.advance();
        } else {
          chars.push(this.advance());
          chars.push(this.advance());
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && ch === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "'") {
        var [ansiResult0, ansiResult1]: any = this.ReadAnsiCQuote();
        if (ansiResult0 !== null) {
          parts.push(ansiResult0);
          chars.push(ansiResult1);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && ch === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "\"") {
        var [localeResult0, localeResult1, localeResult2]: any = this.ReadLocaleString();
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
          if (this.Extglob && ctx === WORD_CTX_NORMAL && chars.length > 0 && chars[chars.length - 1].length === 2 && (chars[chars.length - 1][0] as unknown as string) === "$" && "?*@".includes((chars[chars.length - 1][1] as unknown as string)) && !this.atEnd() && this.peek() === "(") {
            chars.push(this.advance());
            var content: any = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
            chars.push(content);
            chars.push(")");
          }
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && ch === "`") {
        this.SyncToParser();
        var [cmdsubResult0, cmdsubResult1]: any = this.Parser.ParseBacktickSubstitution();
        this.SyncFromParser();
        if (cmdsubResult0 !== null) {
          parts.push(cmdsubResult0);
          chars.push(cmdsubResult1);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && IsRedirectChar(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
        this.SyncToParser();
        var [procsubResult0, procsubResult1]: any = this.Parser.ParseProcessSubstitution();
        this.SyncFromParser();
        if (procsubResult0 !== null) {
          parts.push(procsubResult0);
          chars.push(procsubResult1);
        } else {
          if (procsubResult1 !== "") {
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
      if (ctx === WORD_CTX_NORMAL && ch === "(" && chars.length > 0 && bracketDepth === 0) {
        var isArrayAssign: any = false;
        if (chars.length >= 3 && chars[chars.length - 2] === "+" && chars[chars.length - 1] === "=") {
          isArrayAssign = IsArrayAssignmentPrefix(chars.slice(0, chars.length - 2));
        } else {
          if (chars[chars.length - 1] === "=" && chars.length >= 2) {
            isArrayAssign = IsArrayAssignmentPrefix(chars.slice(0, chars.length - 1));
          }
        }
        if (isArrayAssign && (atCommandStart || inAssignBuiltin)) {
          this.SyncToParser();
          var [arrayResult0, arrayResult1]: any = this.Parser.ParseArrayLiteral();
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
      if (this.Extglob && ctx === WORD_CTX_NORMAL && IsExtglobPrefix(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
        chars.push(this.advance());
        chars.push(this.advance());
        var content: any = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
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
      throw new Error(`${"unexpected EOF looking for `]'"} at position ${bracketStartPos}`)
    }
    if (!(chars.length > 0)) {
      return null;
    }
    if (parts.length > 0) {
      return new Word(chars.join("") as any, parts as any, "word" as any);
    }
    return new Word(chars.join("") as any, null as any, "word" as any);
  }

  ReadWord(): Token {
    var start: any = this.pos;
    if (this.pos >= this.length) {
      return null;
    }
    var c: any = this.peek();
    if (c === "") {
      return null;
    }
    var isProcsub: any = (c === "<" || c === ">") && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(";
    var isRegexParen: any = this.WordContext === WORD_CTX_REGEX && (c === "(" || c === ")");
    if (this.isMetachar(c) && !isProcsub && !isRegexParen) {
      return null;
    }
    var word: any = this.ReadWordInternal(this.WordContext, this.AtCommandStart, this.InArrayLiteral, this.InAssignBuiltin);
    if (word === null) {
      return null;
    }
    return new Token(TokenType_WORD as any, word.value as any, start as any, null as any, word as any);
  }

  nextToken(): Token {
    if (this.TokenCache !== null) {
      var tok: any = this.TokenCache;
      this.TokenCache = null;
      this.LastReadToken = tok;
      return tok;
    }
    this.skipBlanks();
    if (this.atEnd()) {
      var tok: any = new Token(TokenType_EOF as any, "" as any, this.pos as any);
      this.LastReadToken = tok;
      return tok;
    }
    if (this.EofToken !== "" && this.peek() === this.EofToken && !((this.ParserState & ParserStateFlags_PST_CASEPAT) !== 0) && !((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0)) {
      var tok: any = new Token(TokenType_EOF as any, "" as any, this.pos as any);
      this.LastReadToken = tok;
      return tok;
    }
    while (this.SkipComment()) {
      this.skipBlanks();
      if (this.atEnd()) {
        var tok: any = new Token(TokenType_EOF as any, "" as any, this.pos as any);
        this.LastReadToken = tok;
        return tok;
      }
      if (this.EofToken !== "" && this.peek() === this.EofToken && !((this.ParserState & ParserStateFlags_PST_CASEPAT) !== 0) && !((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0)) {
        var tok: any = new Token(TokenType_EOF as any, "" as any, this.pos as any);
        this.LastReadToken = tok;
        return tok;
      }
    }
    var tok: any = this.ReadOperator();
    if (tok !== null) {
      this.LastReadToken = tok;
      return tok;
    }
    tok = this.ReadWord();
    if (tok !== null) {
      this.LastReadToken = tok;
      return tok;
    }
    tok = new Token(TokenType_EOF as any, "" as any, this.pos as any);
    this.LastReadToken = tok;
    return tok;
  }

  peekToken(): Token {
    if (this.TokenCache === null) {
      var savedLast: any = this.LastReadToken;
      this.TokenCache = this.nextToken();
      this.LastReadToken = savedLast;
    }
    return this.TokenCache;
  }

  ReadAnsiCQuote(): [Node, string] {
    if (this.atEnd() || this.peek() !== "$") {
      return [null, ""];
    }
    if (this.pos + 1 >= this.length || (this.source[this.pos + 1] as unknown as string) !== "'") {
      return [null, ""];
    }
    var start: any = this.pos;
    this.advance();
    this.advance();
    var contentChars: any = [];
    var foundClose: any = false;
    while (!this.atEnd()) {
      var ch: any = this.peek();
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
      throw new Error(`${"unexpected EOF while looking for matching `''"} at position ${start}`)
    }
    var text: any = Substring(this.source, start, this.pos);
    var content: any = contentChars.join("");
    var node: any = new AnsiCQuote(content as any, "ansi-c" as any);
    return [node, text];
  }

  SyncToParser(): void {
    if (this.Parser !== null) {
      this.Parser.pos = this.pos;
    }
  }

  SyncFromParser(): void {
    if (this.Parser !== null) {
      this.pos = this.Parser.pos;
    }
  }

  ReadLocaleString(): [Node, string, Node[]] {
    if (this.atEnd() || this.peek() !== "$") {
      return [null, "", []];
    }
    if (this.pos + 1 >= this.length || (this.source[this.pos + 1] as unknown as string) !== "\"") {
      return [null, "", []];
    }
    var start: any = this.pos;
    this.advance();
    this.advance();
    var contentChars: any = [];
    var innerParts: any = [];
    var foundClose: any = false;
    while (!this.atEnd()) {
      var ch: any = this.peek();
      if (ch === "\"") {
        this.advance();
        foundClose = true;
        break;
      } else {
        if (ch === "\\" && this.pos + 1 < this.length) {
          var nextCh: any = (this.source[this.pos + 1] as unknown as string);
          if (nextCh === "\n") {
            this.advance();
            this.advance();
          } else {
            contentChars.push(this.advance());
            contentChars.push(this.advance());
          }
        } else {
          if (ch === "$" && this.pos + 2 < this.length && (this.source[this.pos + 1] as unknown as string) === "(" && (this.source[this.pos + 2] as unknown as string) === "(") {
            this.SyncToParser();
            var [arithNode, arithText]: any = this.Parser.ParseArithmeticExpansion();
            this.SyncFromParser();
            if (arithNode !== null) {
              innerParts.push(arithNode);
              contentChars.push(arithText);
            } else {
              this.SyncToParser();
              var [cmdsubNode, cmdsubText]: any = this.Parser.ParseCommandSubstitution();
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
              var [cmdsubNode, cmdsubText]: any = this.Parser.ParseCommandSubstitution();
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
                var [paramNode, paramText]: any = this.Parser.ParseParamExpansion(false);
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
                  var [cmdsubNode, cmdsubText]: any = this.Parser.ParseBacktickSubstitution();
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
    var content: any = contentChars.join("");
    var text: any = "$\"" + content + "\"";
    return [new LocaleString(content as any, "locale" as any), text, innerParts];
  }

  UpdateDolbraceForOp(op: string, hasParam: boolean): void {
    if (this.DolbraceState === DolbraceState_NONE) {
      return;
    }
    if (op === "" || op.length === 0) {
      return;
    }
    var firstChar: any = (op[0] as unknown as string);
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

  ConsumeParamOperator(): string {
    if (this.atEnd()) {
      return "";
    }
    var ch: any = this.peek();
    if (ch === ":") {
      this.advance();
      if (this.atEnd()) {
        return ":";
      }
      var nextCh: any = this.peek();
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
        var nextCh: any = this.peek();
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

  ParamSubscriptHasClose(startPos: number): boolean {
    var depth: any = 1;
    var i: any = startPos + 1;
    var quote: any = newQuoteState();
    while (i < this.length) {
      var c: any = (this.source[i] as unknown as string);
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

  ConsumeParamName(): string {
    if (this.atEnd()) {
      return "";
    }
    var ch: any = this.peek();
    if (IsSpecialParam(ch)) {
      if (ch === "$" && this.pos + 1 < this.length && "{'\"".includes((this.source[this.pos + 1] as unknown as string))) {
        return "";
      }
      this.advance();
      return ch;
    }
    if (/^[0-9]$/.test(ch)) {
      var nameChars: any = [];
      while (!this.atEnd() && /^[0-9]$/.test(this.peek())) {
        nameChars.push(this.advance());
      }
      return nameChars.join("");
    }
    if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
      var nameChars: any = [];
      while (!this.atEnd()) {
        var c: any = this.peek();
        if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
          nameChars.push(this.advance());
        } else {
          if (c === "[") {
            if (!this.ParamSubscriptHasClose(this.pos)) {
              break;
            }
            nameChars.push(this.advance());
            var content: any = this.ParseMatchedPair("[", "]", MatchedPairFlags_ARRAYSUB, false);
            nameChars.push(content);
            nameChars.push("]");
            break;
          } else {
            break;
          }
        }
      }
      if (nameChars.length > 0) {
        return nameChars.join("");
      } else {
        return "";
      }
    }
    return "";
  }

  ReadParamExpansion(inDquote: boolean): [Node, string] {
    if (this.atEnd() || this.peek() !== "$") {
      return [null, ""];
    }
    var start: any = this.pos;
    this.advance();
    if (this.atEnd()) {
      this.pos = start;
      return [null, ""];
    }
    var ch: any = this.peek();
    if (ch === "{") {
      this.advance();
      return this.ReadBracedParam(start, inDquote);
    }
    if (IsSpecialParamUnbraced(ch) || IsDigit(ch) || ch === "#") {
      this.advance();
      var text: any = Substring(this.source, start, this.pos);
      return [new ParamExpansion(ch as any, "param" as any), text];
    }
    if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
      var nameStart: any = this.pos;
      while (!this.atEnd()) {
        var c: any = this.peek();
        if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
          this.advance();
        } else {
          break;
        }
      }
      var name: any = Substring(this.source, nameStart, this.pos);
      var text: any = Substring(this.source, start, this.pos);
      return [new ParamExpansion(name as any, "param" as any), text];
    }
    this.pos = start;
    return [null, ""];
  }

  ReadBracedParam(start: number, inDquote: boolean): [Node, string] {
    if (this.atEnd()) {
      throw new Error(`${"unexpected EOF looking for `}'"} at position ${start}`)
    }
    var savedDolbrace: any = this.DolbraceState;
    this.DolbraceState = DolbraceState_PARAM;
    var ch: any = this.peek();
    if (IsFunsubChar(ch)) {
      this.DolbraceState = savedDolbrace;
      return this.ReadFunsub(start);
    }
    if (ch === "#") {
      this.advance();
      var param: any = this.ConsumeParamName();
      if (param !== "" && !this.atEnd() && this.peek() === "}") {
        this.advance();
        var text: any = Substring(this.source, start, this.pos);
        this.DolbraceState = savedDolbrace;
        return [new ParamLength(param as any, "param-len" as any), text];
      }
      this.pos = start + 2;
    }
    if (ch === "!") {
      this.advance();
      while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
        this.advance();
      }
      var param: any = this.ConsumeParamName();
      if (param !== "") {
        while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
          this.advance();
        }
        if (!this.atEnd() && this.peek() === "}") {
          this.advance();
          var text: any = Substring(this.source, start, this.pos);
          this.DolbraceState = savedDolbrace;
          return [new ParamIndirect(param as any, "param-indirect" as any), text];
        }
        if (!this.atEnd() && IsAtOrStar(this.peek())) {
          var suffix: any = this.advance();
          var trailing: any = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
          var text: any = Substring(this.source, start, this.pos);
          this.DolbraceState = savedDolbrace;
          return [new ParamIndirect(param + suffix + trailing as any, "param-indirect" as any), text];
        }
        var op: any = this.ConsumeParamOperator();
        if (op === "" && !this.atEnd() && !"}\"'`".includes(this.peek())) {
          op = this.advance();
        }
        if (op !== "" && !"\"'`".includes(op)) {
          var arg: any = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
          var text: any = Substring(this.source, start, this.pos);
          this.DolbraceState = savedDolbrace;
          return [new ParamIndirect(param as any, op as any, arg as any, "param-indirect" as any), text];
        }
        if (this.atEnd()) {
          this.DolbraceState = savedDolbrace;
          throw new Error(`${"unexpected EOF looking for `}'"} at position ${start}`)
        }
        this.pos = start + 2;
      } else {
        this.pos = start + 2;
      }
    }
    var param: any = this.ConsumeParamName();
    if (!(param !== "")) {
      if (!this.atEnd() && ("-=+?".includes(this.peek()) || this.peek() === ":" && this.pos + 1 < this.length && IsSimpleParamOp((this.source[this.pos + 1] as unknown as string)))) {
        param = "";
      } else {
        var content: any = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
        var text: any = "${" + content + "}";
        this.DolbraceState = savedDolbrace;
        return [new ParamExpansion(content as any, "param" as any), text];
      }
    }
    if (this.atEnd()) {
      this.DolbraceState = savedDolbrace;
      throw new Error(`${"unexpected EOF looking for `}'"} at position ${start}`)
    }
    if (this.peek() === "}") {
      this.advance();
      var text: any = Substring(this.source, start, this.pos);
      this.DolbraceState = savedDolbrace;
      return [new ParamExpansion(param as any, "param" as any), text];
    }
    var op: any = this.ConsumeParamOperator();
    if (op === "") {
      if (!this.atEnd() && this.peek() === "$" && this.pos + 1 < this.length && ((this.source[this.pos + 1] as unknown as string) === "\"" || (this.source[this.pos + 1] as unknown as string) === "'")) {
        var dollarCount: any = 1 + CountConsecutiveDollarsBefore(this.source, this.pos);
        if (dollarCount % 2 === 1) {
          op = "";
        } else {
          op = this.advance();
        }
      } else {
        if (!this.atEnd() && this.peek() === "`") {
          var backtickPos: any = this.pos;
          this.advance();
          while (!this.atEnd() && this.peek() !== "`") {
            var bc: any = this.peek();
            if (bc === "\\" && this.pos + 1 < this.length) {
              var nextC: any = (this.source[this.pos + 1] as unknown as string);
              if (IsEscapeCharInBacktick(nextC)) {
                this.advance();
              }
            }
            this.advance();
          }
          if (this.atEnd()) {
            this.DolbraceState = savedDolbrace;
            throw new Error(`${"Unterminated backtick"} at position ${backtickPos}`)
          }
          this.advance();
          op = "`";
        } else {
          if (!this.atEnd() && this.peek() === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "{") {
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
      var flags: any = inDquote ? MatchedPairFlags_DQUOTE : MatchedPairFlags_NONE;
      var paramEndsWithDollar: any = param !== "" && param.endsWith("$");
      var arg: any = this.CollectParamArgument(flags, paramEndsWithDollar);
    } catch (e) {
      this.DolbraceState = savedDolbrace;
      throw new Error(`${""} at position ${0}`)
    }
    if ((op === "<" || op === ">") && arg.startsWith("(") && arg.endsWith(")")) {
      var inner: any = arg.slice(1, arg.length - 1);
      try {
        var subParser: any = newParser(inner, true, this.Parser.Extglob);
        var parsed: any = subParser.parseList(true);
        if (parsed !== null && subParser.atEnd()) {
          var formatted: any = FormatCmdsubNode(parsed, 0, true, false, true);
          var arg: any = "(" + formatted + ")";
        }
      } catch (_e) {
      }
    }
    var text: any = "${" + param + op + arg + "}";
    this.DolbraceState = savedDolbrace;
    return [new ParamExpansion(param as any, op as any, arg as any, "param" as any), text];
  }

  ReadFunsub(start: number): [Node, string] {
    return this.Parser.ParseFunsub(start);
  }
}

class Word implements Node {
  value: string;
  parts: Node[];
  kind: string;

  constructor(value: string = "", parts: Node[] = [], kind: string = "") {
    this.value = value;
    this.parts = parts;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var value: any = this.value;
    value = this.ExpandAllAnsiCQuotes(value);
    value = this.StripLocaleStringDollars(value);
    value = this.NormalizeArrayWhitespace(value);
    value = this.FormatCommandSubstitutions(value, false);
    value = this.NormalizeParamExpansionNewlines(value);
    value = this.StripArithLineContinuations(value);
    value = this.DoubleCtlescSmart(value);
    value = value.replace("", "");
    value = value.replace("\\", "\\\\");
    if (value.endsWith("\\\\") && !value.endsWith("\\\\\\\\")) {
      value = value + "\\\\";
    }
    var escaped: any = value.replace("\"", "\\\"").replace("\n", "\\n").replace("\t", "\\t");
    return "(word \"" + escaped + "\")";
  }

  AppendWithCtlesc(result: number[], byteVal: number): void {
    result.push(byteVal);
  }

  DoubleCtlescSmart(value: string): string {
    var result: any = [];
    var quote: any = newQuoteState();
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
          var bsCount: any = 0;
          for (const j of range(result.length - 2, -1, -1)) {
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

  NormalizeParamExpansionNewlines(value: string): string {
    var result: any = [];
    var i: any = 0;
    var quote: any = newQuoteState();
    while (i < value.length) {
      var c: any = (value[i] as unknown as string);
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
            var hadLeadingNewline: any = i < value.length && (value[i] as unknown as string) === "\n";
            if (hadLeadingNewline) {
              result.push(" ");
              i += 1;
            }
            var depth: any = 1;
            while (i < value.length && depth > 0) {
              var ch: any = (value[i] as unknown as string);
              if (ch === "\\" && i + 1 < value.length && !quote.single) {
                if ((value[i + 1] as unknown as string) === "\n") {
                  i += 2;
                  continue;
                }
                result.push(ch);
                result.push((value[i + 1] as unknown as string));
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

  ShSingleQuote(s: string): string {
    if (!(s !== "")) {
      return "''";
    }
    if (s === "'") {
      return "\\'";
    }
    var result: any = ["'"];
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

  AnsiCToBytes(inner: string): number[] {
    var result: any = [];
    var i: any = 0;
    while (i < inner.length) {
      if ((inner[i] as unknown as string) === "\\" && i + 1 < inner.length) {
        var c: any = (inner[i + 1] as unknown as string);
        var simple: any = GetAnsiEscape(c);
        if (simple >= 0) {
          result.push(simple);
          i += 2;
        } else {
          if (c === "'") {
            result.push(39);
            i += 2;
          } else {
            if (c === "x") {
              if (i + 2 < inner.length && (inner[i + 2] as unknown as string) === "{") {
                var j: any = i + 3;
                while (j < inner.length && IsHexDigit((inner[j] as unknown as string))) {
                  j += 1;
                }
                var hexStr: any = Substring(inner, i + 3, j);
                if (j < inner.length && (inner[j] as unknown as string) === "}") {
                  j += 1;
                }
                if (!(hexStr !== "")) {
                  return result;
                }
                var byteVal: any = parseInt(hexStr, 16) & 255;
                if (byteVal === 0) {
                  return result;
                }
                this.AppendWithCtlesc(result, byteVal);
                i = j;
              } else {
                var j: any = i + 2;
                while (j < inner.length && j < i + 4 && IsHexDigit((inner[j] as unknown as string))) {
                  j += 1;
                }
                if (j > i + 2) {
                  var byteVal: any = parseInt(Substring(inner, i + 2, j), 16);
                  if (byteVal === 0) {
                    return result;
                  }
                  this.AppendWithCtlesc(result, byteVal);
                  i = j;
                } else {
                  result.push((inner[i] as unknown as string)[0]);
                  i += 1;
                }
              }
            } else {
              if (c === "u") {
                var j: any = i + 2;
                while (j < inner.length && j < i + 6 && IsHexDigit((inner[j] as unknown as string))) {
                  j += 1;
                }
                if (j > i + 2) {
                  var codepoint: any = parseInt(Substring(inner, i + 2, j), 16);
                  if (codepoint === 0) {
                    return result;
                  }
                  result.push(...((codepoint as unknown as string) as unknown as number[]));
                  i = j;
                } else {
                  result.push((inner[i] as unknown as string)[0]);
                  i += 1;
                }
              } else {
                if (c === "U") {
                  var j: any = i + 2;
                  while (j < inner.length && j < i + 10 && IsHexDigit((inner[j] as unknown as string))) {
                    j += 1;
                  }
                  if (j > i + 2) {
                    var codepoint: any = parseInt(Substring(inner, i + 2, j), 16);
                    if (codepoint === 0) {
                      return result;
                    }
                    result.push(...((codepoint as unknown as string) as unknown as number[]));
                    i = j;
                  } else {
                    result.push((inner[i] as unknown as string)[0]);
                    i += 1;
                  }
                } else {
                  if (c === "c") {
                    if (i + 3 <= inner.length) {
                      var ctrlChar: any = (inner[i + 2] as unknown as string);
                      var skipExtra: any = 0;
                      if (ctrlChar === "\\" && i + 4 <= inner.length && (inner[i + 3] as unknown as string) === "\\") {
                        skipExtra = 1;
                      }
                      var ctrlVal: any = ctrlChar[0] & 31;
                      if (ctrlVal === 0) {
                        return result;
                      }
                      this.AppendWithCtlesc(result, ctrlVal);
                      i += 3 + skipExtra;
                    } else {
                      result.push((inner[i] as unknown as string)[0]);
                      i += 1;
                    }
                  } else {
                    if (c === "0") {
                      var j: any = i + 2;
                      while (j < inner.length && j < i + 4 && IsOctalDigit((inner[j] as unknown as string))) {
                        j += 1;
                      }
                      if (j > i + 2) {
                        var byteVal: any = parseInt(Substring(inner, i + 1, j), 8) & 255;
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
                        var j: any = i + 1;
                        while (j < inner.length && j < i + 4 && IsOctalDigit((inner[j] as unknown as string))) {
                          j += 1;
                        }
                        var byteVal: any = parseInt(Substring(inner, i + 1, j), 8) & 255;
                        if (byteVal === 0) {
                          return result;
                        }
                        this.AppendWithCtlesc(result, byteVal);
                        i = j;
                      } else {
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
      } else {
        result.push(...((inner[i] as unknown as string) as unknown as number[]));
        i += 1;
      }
    }
    return result;
  }

  ExpandAnsiCEscapes(value: string): string {
    if (!(value.startsWith("'") && value.endsWith("'"))) {
      return value;
    }
    var inner: any = Substring(value, 1, value.length - 1);
    var literalBytes: any = this.AnsiCToBytes(inner);
    var literalStr: any = (literalBytes as unknown as string);
    return this.ShSingleQuote(literalStr);
  }

  ExpandAllAnsiCQuotes(value: string): string {
    var result: any = [];
    var i: any = 0;
    var quote: any = newQuoteState();
    var inBacktick: any = false;
    var braceDepth: any = 0;
    while (i < value.length) {
      var ch: any = (value[i] as unknown as string);
      if (ch === "`" && !quote.single) {
        inBacktick = !inBacktick;
        result.push(ch);
        i += 1;
        continue;
      }
      if (inBacktick) {
        if (ch === "\\" && i + 1 < value.length) {
          result.push(ch);
          result.push((value[i + 1] as unknown as string));
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
      var effectiveInDquote: any = quote.double;
      if (ch === "'" && !effectiveInDquote) {
        var isAnsiC: any = !quote.single && i > 0 && (value[i - 1] as unknown as string) === "$" && CountConsecutiveDollarsBefore(value, i - 1) % 2 === 0;
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
            result.push((value[i + 1] as unknown as string));
            i += 2;
          } else {
            if (StartsWithAt(value, i, "$'") && !quote.single && !effectiveInDquote && CountConsecutiveDollarsBefore(value, i) % 2 === 0) {
              var j: any = i + 2;
              while (j < value.length) {
                if ((value[j] as unknown as string) === "\\" && j + 1 < value.length) {
                  j += 2;
                } else {
                  if ((value[j] as unknown as string) === "'") {
                    j += 1;
                    break;
                  } else {
                    j += 1;
                  }
                }
              }
              var ansiStr: any = Substring(value, i, j);
              var expanded: any = this.ExpandAnsiCEscapes(Substring(ansiStr, 1, ansiStr.length));
              var outerInDquote: any = quote.outerDouble();
              if (braceDepth > 0 && outerInDquote && expanded.startsWith("'") && expanded.endsWith("'")) {
                var inner: any = Substring(expanded, 1, expanded.length - 1);
                if (inner.indexOf("") === -1) {
                  var resultStr: any = result.join("");
                  var inPattern: any = false;
                  var lastBraceIdx: any = resultStr.lastIndexOf("${");
                  if (lastBraceIdx >= 0) {
                    var afterBrace: any = resultStr.slice(lastBraceIdx + 2);
                    var varNameLen: any = 0;
                    if (afterBrace !== "") {
                      if ("@*#?-$!0123456789_".includes((afterBrace[0] as unknown as string))) {
                        varNameLen = 1;
                      } else {
                        if (/^[a-zA-Z]$/.test((afterBrace[0] as unknown as string)) || (afterBrace[0] as unknown as string) === "_") {
                          while (varNameLen < afterBrace.length) {
                            var c: any = (afterBrace[varNameLen] as unknown as string);
                            if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
                              break;
                            }
                            varNameLen += 1;
                          }
                        }
                      }
                    }
                    if (varNameLen > 0 && varNameLen < afterBrace.length && !"#?-".includes((afterBrace[0] as unknown as string))) {
                      var opStart: any = afterBrace.slice(varNameLen);
                      if (opStart.startsWith("@") && opStart.length > 1) {
                        opStart = opStart.slice(1);
                      }
                      for (const op of ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
                        if (opStart.startsWith(op)) {
                          inPattern = true;
                          break;
                        }
                      }
                      if (!inPattern && opStart !== "" && !"%#/^,~:+-=?".includes((opStart[0] as unknown as string))) {
                        for (const op of ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
                          if (opStart.includes(op)) {
                            inPattern = true;
                            break;
                          }
                        }
                      }
                    } else {
                      if (varNameLen === 0 && afterBrace.length > 1) {
                        var firstChar: any = (afterBrace[0] as unknown as string);
                        if (!"%#/^,".includes(firstChar)) {
                          var rest: any = afterBrace.slice(1);
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

  StripLocaleStringDollars(value: string): string {
    var result: any = [];
    var i: any = 0;
    var braceDepth: any = 0;
    var bracketDepth: any = 0;
    var quote: any = newQuoteState();
    var braceQuote: any = newQuoteState();
    var bracketInDoubleQuote: any = false;
    while (i < value.length) {
      var ch: any = (value[i] as unknown as string);
      if (ch === "\\" && i + 1 < value.length && !quote.single && !braceQuote.single) {
        result.push(ch);
        result.push((value[i + 1] as unknown as string));
        i += 2;
      } else {
        if (StartsWithAt(value, i, "${") && !quote.single && !braceQuote.single && (i === 0 || (value[i - 1] as unknown as string) !== "$")) {
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
                            var dollarCount: any = 1 + CountConsecutiveDollarsBefore(value, i);
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

  NormalizeArrayWhitespace(value: string): string {
    var i: any = 0;
    if (!(i < value.length && (/^[a-zA-Z]$/.test((value[i] as unknown as string)) || (value[i] as unknown as string) === "_"))) {
      return value;
    }
    i += 1;
    while (i < value.length && (/^[a-zA-Z0-9]$/.test((value[i] as unknown as string)) || (value[i] as unknown as string) === "_")) {
      i += 1;
    }
    while (i < value.length && (value[i] as unknown as string) === "[") {
      var depth: any = 1;
      i += 1;
      while (i < value.length && depth > 0) {
        if ((value[i] as unknown as string) === "[") {
          depth += 1;
        } else {
          if ((value[i] as unknown as string) === "]") {
            depth -= 1;
          }
        }
        i += 1;
      }
      if (depth !== 0) {
        return value;
      }
    }
    if (i < value.length && (value[i] as unknown as string) === "+") {
      i += 1;
    }
    if (!(i + 1 < value.length && (value[i] as unknown as string) === "=" && (value[i + 1] as unknown as string) === "(")) {
      return value;
    }
    var prefix: any = Substring(value, 0, i + 1);
    var openParenPos: any = i + 1;
    if (value.endsWith(")")) {
      var closeParenPos: any = value.length - 1;
    } else {
      var closeParenPos: any = this.FindMatchingParen(value, openParenPos);
      if (closeParenPos < 0) {
        return value;
      }
    }
    var inner: any = Substring(value, openParenPos + 1, closeParenPos);
    var suffix: any = Substring(value, closeParenPos + 1, value.length);
    var result: any = this.NormalizeArrayInner(inner);
    return prefix + "(" + result + ")" + suffix;
  }

  FindMatchingParen(value: string, openPos: number): number {
    if (openPos >= value.length || (value[openPos] as unknown as string) !== "(") {
      return -1;
    }
    var i: any = openPos + 1;
    var depth: any = 1;
    var quote: any = newQuoteState();
    while (i < value.length && depth > 0) {
      var ch: any = (value[i] as unknown as string);
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
        while (i < value.length && (value[i] as unknown as string) !== "\n") {
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

  NormalizeArrayInner(inner: string): string {
    var normalized: any = [];
    var i: any = 0;
    var inWhitespace: any = true;
    var braceDepth: any = 0;
    var bracketDepth: any = 0;
    while (i < inner.length) {
      var ch: any = (inner[i] as unknown as string);
      if (IsWhitespace(ch)) {
        if (!inWhitespace && normalized.length > 0 && braceDepth === 0 && bracketDepth === 0) {
          normalized.push(" ");
          inWhitespace = true;
        }
        if (braceDepth > 0 || bracketDepth > 0) {
          normalized.push(ch);
        }
        i += 1;
      } else {
        if (ch === "'") {
          inWhitespace = false;
          var j: any = i + 1;
          while (j < inner.length && (inner[j] as unknown as string) !== "'") {
            j += 1;
          }
          normalized.push(Substring(inner, i, j + 1));
          i = j + 1;
        } else {
          if (ch === "\"") {
            inWhitespace = false;
            var j: any = i + 1;
            var dqContent: any = ["\""];
            var dqBraceDepth: any = 0;
            while (j < inner.length) {
              if ((inner[j] as unknown as string) === "\\" && j + 1 < inner.length) {
                if ((inner[j + 1] as unknown as string) === "\n") {
                  j += 2;
                } else {
                  dqContent.push((inner[j] as unknown as string));
                  dqContent.push((inner[j + 1] as unknown as string));
                  j += 2;
                }
              } else {
                if (IsExpansionStart(inner, j, "${")) {
                  dqContent.push("${");
                  dqBraceDepth += 1;
                  j += 2;
                } else {
                  if ((inner[j] as unknown as string) === "}" && dqBraceDepth > 0) {
                    dqContent.push("}");
                    dqBraceDepth -= 1;
                    j += 1;
                  } else {
                    if ((inner[j] as unknown as string) === "\"" && dqBraceDepth === 0) {
                      dqContent.push("\"");
                      j += 1;
                      break;
                    } else {
                      dqContent.push((inner[j] as unknown as string));
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
              if ((inner[i + 1] as unknown as string) === "\n") {
                i += 2;
              } else {
                inWhitespace = false;
                normalized.push(Substring(inner, i, i + 2));
                i += 2;
              }
            } else {
              if (IsExpansionStart(inner, i, "$((")) {
                inWhitespace = false;
                var j: any = i + 3;
                var depth: any = 1;
                while (j < inner.length && depth > 0) {
                  if (j + 1 < inner.length && (inner[j] as unknown as string) === "(" && (inner[j + 1] as unknown as string) === "(") {
                    depth += 1;
                    j += 2;
                  } else {
                    if (j + 1 < inner.length && (inner[j] as unknown as string) === ")" && (inner[j + 1] as unknown as string) === ")") {
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
                  var j: any = i + 2;
                  var depth: any = 1;
                  while (j < inner.length && depth > 0) {
                    if ((inner[j] as unknown as string) === "(" && j > 0 && (inner[j - 1] as unknown as string) === "$") {
                      depth += 1;
                    } else {
                      if ((inner[j] as unknown as string) === ")") {
                        depth -= 1;
                      } else {
                        if ((inner[j] as unknown as string) === "'") {
                          j += 1;
                          while (j < inner.length && (inner[j] as unknown as string) !== "'") {
                            j += 1;
                          }
                        } else {
                          if ((inner[j] as unknown as string) === "\"") {
                            j += 1;
                            while (j < inner.length) {
                              if ((inner[j] as unknown as string) === "\\" && j + 1 < inner.length) {
                                j += 2;
                                continue;
                              }
                              if ((inner[j] as unknown as string) === "\"") {
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
                  if ((ch === "<" || ch === ">") && i + 1 < inner.length && (inner[i + 1] as unknown as string) === "(") {
                    inWhitespace = false;
                    var j: any = i + 2;
                    var depth: any = 1;
                    while (j < inner.length && depth > 0) {
                      if ((inner[j] as unknown as string) === "(") {
                        depth += 1;
                      } else {
                        if ((inner[j] as unknown as string) === ")") {
                          depth -= 1;
                        } else {
                          if ((inner[j] as unknown as string) === "'") {
                            j += 1;
                            while (j < inner.length && (inner[j] as unknown as string) !== "'") {
                              j += 1;
                            }
                          } else {
                            if ((inner[j] as unknown as string) === "\"") {
                              j += 1;
                              while (j < inner.length) {
                                if ((inner[j] as unknown as string) === "\\" && j + 1 < inner.length) {
                                  j += 2;
                                  continue;
                                }
                                if ((inner[j] as unknown as string) === "\"") {
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
                            while (i < inner.length && (inner[i] as unknown as string) !== "\n") {
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

  StripArithLineContinuations(value: string): string {
    var result: any = [];
    var i: any = 0;
    while (i < value.length) {
      if (IsExpansionStart(value, i, "$((")) {
        var start: any = i;
        i += 3;
        var depth: any = 2;
        var arithContent: any = [];
        var firstCloseIdx: any = -1;
        while (i < value.length && depth > 0) {
          if ((value[i] as unknown as string) === "(") {
            arithContent.push("(");
            depth += 1;
            i += 1;
            if (depth > 1) {
              firstCloseIdx = -1;
            }
          } else {
            if ((value[i] as unknown as string) === ")") {
              if (depth === 2) {
                firstCloseIdx = arithContent.length;
              }
              depth -= 1;
              if (depth > 0) {
                arithContent.push(")");
              }
              i += 1;
            } else {
              if ((value[i] as unknown as string) === "\\" && i + 1 < value.length && (value[i + 1] as unknown as string) === "\n") {
                var numBackslashes: any = 0;
                var j: any = arithContent.length - 1;
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
                arithContent.push((value[i] as unknown as string));
                i += 1;
                if (depth === 1) {
                  firstCloseIdx = -1;
                }
              }
            }
          }
        }
        if (depth === 0 || depth === 1 && firstCloseIdx !== -1) {
          var content: any = arithContent.join("");
          if (firstCloseIdx !== -1) {
            content = content.slice(0, firstCloseIdx);
            var closing: any = depth === 0 ? "))" : ")";
            result.push("$((" + content + closing);
          } else {
            result.push("$((" + content + ")");
          }
        } else {
          result.push(Substring(value, start, i));
        }
      } else {
        result.push((value[i] as unknown as string));
        i += 1;
      }
    }
    return result.join("");
  }

  CollectCmdsubs(node: Node): Node[] {
    var result: any = [];
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

  CollectProcsubs(node: Node): Node[] {
    var result: any = [];
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

  FormatCommandSubstitutions(value: string, inArith: boolean): string {
    var cmdsubParts: any = [];
    var procsubParts: any = [];
    var hasArith: any = false;
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
    var hasBraceCmdsub: any = value.indexOf("${ ") !== -1 || value.indexOf("${\t") !== -1 || value.indexOf("${\n") !== -1 || value.indexOf("${|") !== -1;
    var hasUntrackedCmdsub: any = false;
    var hasUntrackedProcsub: any = false;
    var idx: any = 0;
    var scanQuote: any = newQuoteState();
    while (idx < value.length) {
      if ((value[idx] as unknown as string) === "\"") {
        scanQuote.double = !scanQuote.double;
        idx += 1;
      } else {
        if ((value[idx] as unknown as string) === "'" && !scanQuote.double) {
          idx += 1;
          while (idx < value.length && (value[idx] as unknown as string) !== "'") {
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
              if (idx === 0 || !/^[a-zA-Z0-9]$/.test((value[idx - 1] as unknown as string)) && !"\"'".includes((value[idx - 1] as unknown as string))) {
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
    var hasParamWithProcsubPattern: any = value.includes("${") && (value.includes("<(") || value.includes(">("));
    if (!(cmdsubParts.length > 0) && !(procsubParts.length > 0) && !hasBraceCmdsub && !hasUntrackedCmdsub && !hasUntrackedProcsub && !hasParamWithProcsubPattern) {
      return value;
    }
    var result: any = [];
    var i: any = 0;
    var cmdsubIdx: any = 0;
    var procsubIdx: any = 0;
    var mainQuote: any = newQuoteState();
    var extglobDepth: any = 0;
    var deprecatedArithDepth: any = 0;
    var arithDepth: any = 0;
    var arithParenDepth: any = 0;
    while (i < value.length) {
      if (i > 0 && IsExtglobPrefix((value[i - 1] as unknown as string)) && (value[i] as unknown as string) === "(" && !IsBackslashEscaped(value, i - 1)) {
        extglobDepth += 1;
        result.push((value[i] as unknown as string));
        i += 1;
        continue;
      }
      if ((value[i] as unknown as string) === ")" && extglobDepth > 0) {
        extglobDepth -= 1;
        result.push((value[i] as unknown as string));
        i += 1;
        continue;
      }
      if (StartsWithAt(value, i, "$[") && !IsBackslashEscaped(value, i)) {
        deprecatedArithDepth += 1;
        result.push((value[i] as unknown as string));
        i += 1;
        continue;
      }
      if ((value[i] as unknown as string) === "]" && deprecatedArithDepth > 0) {
        deprecatedArithDepth -= 1;
        result.push((value[i] as unknown as string));
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
        if ((value[i] as unknown as string) === "(") {
          arithParenDepth += 1;
          result.push((value[i] as unknown as string));
          i += 1;
          continue;
        } else {
          if ((value[i] as unknown as string) === ")") {
            arithParenDepth -= 1;
            result.push((value[i] as unknown as string));
            i += 1;
            continue;
          }
        }
      }
      if (IsExpansionStart(value, i, "$((") && !hasArith) {
        var j: any = FindCmdsubEnd(value, i + 2);
        result.push(Substring(value, i, j));
        if (cmdsubIdx < cmdsubParts.length) {
          cmdsubIdx += 1;
        }
        i = j;
        continue;
      }
      if (StartsWithAt(value, i, "$(") && !StartsWithAt(value, i, "$((") && !IsBackslashEscaped(value, i) && !IsDollarDollarParen(value, i)) {
        var j: any = FindCmdsubEnd(value, i + 2);
        if (extglobDepth > 0) {
          result.push(Substring(value, i, j));
          if (cmdsubIdx < cmdsubParts.length) {
            cmdsubIdx += 1;
          }
          i = j;
          continue;
        }
        var inner: any = Substring(value, i + 2, j - 1);
        if (cmdsubIdx < cmdsubParts.length) {
          var node: any = cmdsubParts[cmdsubIdx];
          var formatted: any = FormatCmdsubNode((node as unknown as CommandSubstitution).command, 0, false, false, false);
          cmdsubIdx += 1;
        } else {
          try {
            var parser: any = newParser(inner, false, false);
            var parsed: any = parser.parseList(true);
            var formatted: any = parsed !== null ? FormatCmdsubNode(parsed, 0, false, false, false) : "";
          } catch (_e) {
            var formatted: any = inner;
          }
        }
        if (formatted.startsWith("(")) {
          result.push("$( " + formatted + ")");
        } else {
          result.push("$(" + formatted + ")");
        }
        i = j;
      } else {
        if ((value[i] as unknown as string) === "`" && cmdsubIdx < cmdsubParts.length) {
          var j: any = i + 1;
          while (j < value.length) {
            if ((value[j] as unknown as string) === "\\" && j + 1 < value.length) {
              j += 2;
              continue;
            }
            if ((value[j] as unknown as string) === "`") {
              j += 1;
              break;
            }
            j += 1;
          }
          result.push(Substring(value, i, j));
          cmdsubIdx += 1;
          i = j;
        } else {
          if (IsExpansionStart(value, i, "${") && i + 2 < value.length && IsFunsubChar((value[i + 2] as unknown as string)) && !IsBackslashEscaped(value, i)) {
            var j: any = FindFunsubEnd(value, i + 2);
            var cmdsubNode: any = cmdsubIdx < cmdsubParts.length ? cmdsubParts[cmdsubIdx] : null;
            if (cmdsubNode instanceof CommandSubstitution && (cmdsubNode as unknown as CommandSubstitution).brace) {
              var node: any = cmdsubNode;
              var formatted: any = FormatCmdsubNode((node as unknown as CommandSubstitution).command, 0, false, false, false);
              var hasPipe: any = (value[i + 2] as unknown as string) === "|";
              var prefix: any = hasPipe ? "${|" : "${ ";
              var origInner: any = Substring(value, i + 2, j - 1);
              var endsWithNewline: any = origInner.endsWith("\n");
              if (!(formatted !== "") || /^\s$/.test(formatted)) {
                var suffix: any = "}";
              } else {
                if (formatted.endsWith("&") || formatted.endsWith("& ")) {
                  var suffix: any = formatted.endsWith("&") ? " }" : "}";
                } else {
                  if (endsWithNewline) {
                    var suffix: any = "\n }";
                  } else {
                    var suffix: any = "; }";
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
              var isProcsub: any = i === 0 || !/^[a-zA-Z0-9]$/.test((value[i - 1] as unknown as string)) && !"\"'".includes((value[i - 1] as unknown as string));
              if (extglobDepth > 0) {
                var j: any = FindCmdsubEnd(value, i + 2);
                result.push(Substring(value, i, j));
                if (procsubIdx < procsubParts.length) {
                  procsubIdx += 1;
                }
                i = j;
                continue;
              }
              if (procsubIdx < procsubParts.length) {
                var direction: any = (value[i] as unknown as string);
                var j: any = FindCmdsubEnd(value, i + 2);
                var node: any = procsubParts[procsubIdx];
                var compact: any = StartsWithSubshell((node as unknown as ProcessSubstitution).command);
                var formatted: any = FormatCmdsubNode((node as unknown as ProcessSubstitution).command, 0, true, compact, true);
                var rawContent: any = Substring(value, i + 2, j - 1);
                if ((node as unknown as ProcessSubstitution).command.kind === "subshell") {
                  var leadingWsEnd: any = 0;
                  while (leadingWsEnd < rawContent.length && " \t\n".includes((rawContent[leadingWsEnd] as unknown as string))) {
                    leadingWsEnd += 1;
                  }
                  var leadingWs: any = rawContent.slice(0, leadingWsEnd);
                  var stripped: any = rawContent.slice(leadingWsEnd);
                  if (stripped.startsWith("(")) {
                    if (leadingWs !== "") {
                      var normalizedWs: any = leadingWs.replace("\n", " ").replace("\t", " ");
                      var spaced: any = FormatCmdsubNode((node as unknown as ProcessSubstitution).command, 0, false, false, false);
                      result.push(direction + "(" + normalizedWs + spaced + ")");
                    } else {
                      rawContent = rawContent.replace("\\\n", "");
                      result.push(direction + "(" + rawContent + ")");
                    }
                    procsubIdx += 1;
                    i = j;
                    continue;
                  }
                }
                rawContent = Substring(value, i + 2, j - 1);
                var rawStripped: any = rawContent.replace("\\\n", "");
                if (StartsWithSubshell((node as unknown as ProcessSubstitution).command) && formatted !== rawStripped) {
                  result.push(direction + "(" + rawStripped + ")");
                } else {
                  var finalOutput: any = direction + "(" + formatted + ")";
                  result.push(finalOutput);
                }
                procsubIdx += 1;
                i = j;
              } else {
                if (isProcsub && this.parts.length !== 0) {
                  var direction: any = (value[i] as unknown as string);
                  var j: any = FindCmdsubEnd(value, i + 2);
                  if (j > value.length || j > 0 && j <= value.length && (value[j - 1] as unknown as string) !== ")") {
                    result.push((value[i] as unknown as string));
                    i += 1;
                    continue;
                  }
                  var inner: any = Substring(value, i + 2, j - 1);
                  try {
                    var parser: any = newParser(inner, false, false);
                    var parsed: any = parser.parseList(true);
                    if (parsed !== null && parser.pos === inner.length && !inner.includes("\n")) {
                      var compact: any = StartsWithSubshell(parsed);
                      var formatted: any = FormatCmdsubNode(parsed, 0, true, compact, true);
                    } else {
                      var formatted: any = inner;
                    }
                  } catch (_e) {
                    var formatted: any = inner;
                  }
                  result.push(direction + "(" + formatted + ")");
                  i = j;
                } else {
                  if (isProcsub) {
                    var direction: any = (value[i] as unknown as string);
                    var j: any = FindCmdsubEnd(value, i + 2);
                    if (j > value.length || j > 0 && j <= value.length && (value[j - 1] as unknown as string) !== ")") {
                      result.push((value[i] as unknown as string));
                      i += 1;
                      continue;
                    }
                    var inner: any = Substring(value, i + 2, j - 1);
                    if (inArith) {
                      result.push(direction + "(" + inner + ")");
                    } else {
                      if (inner.trim() !== "") {
                        var stripped: any = inner.replace(/^[ \t]+/, '');
                        result.push(direction + "(" + stripped + ")");
                      } else {
                        result.push(direction + "(" + inner + ")");
                      }
                    }
                    i = j;
                  } else {
                    result.push((value[i] as unknown as string));
                    i += 1;
                  }
                }
              }
            } else {
              if ((IsExpansionStart(value, i, "${ ") || IsExpansionStart(value, i, "${\t") || IsExpansionStart(value, i, "${\n") || IsExpansionStart(value, i, "${|")) && !IsBackslashEscaped(value, i)) {
                var prefix: any = Substring(value, i, i + 3).replace("\t", " ").replace("\n", " ");
                var j: any = i + 3;
                var depth: any = 1;
                while (j < value.length && depth > 0) {
                  if ((value[j] as unknown as string) === "{") {
                    depth += 1;
                  } else {
                    if ((value[j] as unknown as string) === "}") {
                      depth -= 1;
                    }
                  }
                  j += 1;
                }
                var inner: any = Substring(value, i + 2, j - 1);
                if (inner.trim() === "") {
                  result.push("${ }");
                } else {
                  try {
                    var parser: any = newParser(inner.replace(/^[ \t\n|]+/, ''), false, false);
                    var parsed: any = parser.parseList(true);
                    if (parsed !== null) {
                      var formatted: any = FormatCmdsubNode(parsed, 0, false, false, false);
                      formatted = formatted.replace(/[;]+$/, '');
                      if (inner.replace(/[ \t]+$/, '').endsWith("\n")) {
                        var terminator: any = "\n }";
                      } else {
                        if (formatted.endsWith(" &")) {
                          var terminator: any = " }";
                        } else {
                          var terminator: any = "; }";
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
                  var j: any = i + 2;
                  var depth: any = 1;
                  var braceQuote: any = newQuoteState();
                  while (j < value.length && depth > 0) {
                    var c: any = (value[j] as unknown as string);
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
                    var inner: any = Substring(value, i + 2, j);
                  } else {
                    var inner: any = Substring(value, i + 2, j - 1);
                  }
                  var formattedInner: any = this.FormatCommandSubstitutions(inner, false);
                  formattedInner = this.NormalizeExtglobWhitespace(formattedInner);
                  if (depth === 0) {
                    result.push("${" + formattedInner + "}");
                  } else {
                    result.push("${" + formattedInner);
                  }
                  i = j;
                } else {
                  if ((value[i] as unknown as string) === "\"") {
                    mainQuote.double = !mainQuote.double;
                    result.push((value[i] as unknown as string));
                    i += 1;
                  } else {
                    if ((value[i] as unknown as string) === "'" && !mainQuote.double) {
                      var j: any = i + 1;
                      while (j < value.length && (value[j] as unknown as string) !== "'") {
                        j += 1;
                      }
                      if (j < value.length) {
                        j += 1;
                      }
                      result.push(Substring(value, i, j));
                      i = j;
                    } else {
                      result.push((value[i] as unknown as string));
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

  NormalizeExtglobWhitespace(value: string): string {
    var result: any = [];
    var i: any = 0;
    var extglobQuote: any = newQuoteState();
    var deprecatedArithDepth: any = 0;
    while (i < value.length) {
      if ((value[i] as unknown as string) === "\"") {
        extglobQuote.double = !extglobQuote.double;
        result.push((value[i] as unknown as string));
        i += 1;
        continue;
      }
      if (StartsWithAt(value, i, "$[") && !IsBackslashEscaped(value, i)) {
        deprecatedArithDepth += 1;
        result.push((value[i] as unknown as string));
        i += 1;
        continue;
      }
      if ((value[i] as unknown as string) === "]" && deprecatedArithDepth > 0) {
        deprecatedArithDepth -= 1;
        result.push((value[i] as unknown as string));
        i += 1;
        continue;
      }
      if (i + 1 < value.length && (value[i + 1] as unknown as string) === "(") {
        var prefixChar: any = (value[i] as unknown as string);
        if ("><".includes(prefixChar) && !extglobQuote.double && deprecatedArithDepth === 0) {
          result.push(prefixChar);
          result.push("(");
          i += 2;
          var depth: any = 1;
          var patternParts: any = [];
          var currentPart: any = [];
          var hasPipe: any = false;
          while (i < value.length && depth > 0) {
            if ((value[i] as unknown as string) === "\\" && i + 1 < value.length) {
              currentPart.push(value.slice(i, i + 2));
              i += 2;
              continue;
            } else {
              if ((value[i] as unknown as string) === "(") {
                depth += 1;
                currentPart.push((value[i] as unknown as string));
                i += 1;
              } else {
                if ((value[i] as unknown as string) === ")") {
                  depth -= 1;
                  if (depth === 0) {
                    var partContent: any = currentPart.join("");
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
                  currentPart.push((value[i] as unknown as string));
                  i += 1;
                } else {
                  if ((value[i] as unknown as string) === "|" && depth === 1) {
                    if (i + 1 < value.length && (value[i + 1] as unknown as string) === "|") {
                      currentPart.push("||");
                      i += 2;
                    } else {
                      hasPipe = true;
                      var partContent: any = currentPart.join("");
                      if (partContent.includes("<<")) {
                        patternParts.push(partContent);
                      } else {
                        patternParts.push(partContent.trim());
                      }
                      currentPart = [];
                      i += 1;
                    }
                  } else {
                    currentPart.push((value[i] as unknown as string));
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
      result.push((value[i] as unknown as string));
      i += 1;
    }
    return result.join("");
  }

  getCondFormattedValue(): string {
    var value: any = this.ExpandAllAnsiCQuotes(this.value);
    value = this.StripLocaleStringDollars(value);
    value = this.FormatCommandSubstitutions(value, false);
    value = this.NormalizeExtglobWhitespace(value);
    value = value.replace("", "");
    return value.replace(/[\n]+$/, '');
  }
}

class Command implements Node {
  words: Word[];
  redirects: Node[];
  kind: string;

  constructor(words: Word[] = [], redirects: Node[] = [], kind: string = "") {
    this.words = words;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var parts: any = [];
    for (const w of this.words) {
      parts.push(w.toSexp());
    }
    for (const r of this.redirects) {
      parts.push(r.toSexp());
    }
    var inner: any = parts.join(" ");
    if (!(inner !== "")) {
      return "(command)";
    }
    return "(command " + inner + ")";
  }
}

class Pipeline implements Node {
  commands: Node[];
  kind: string;

  constructor(commands: Node[] = [], kind: string = "") {
    this.commands = commands;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    if (this.commands.length === 1) {
      return this.commands[0].toSexp();
    }
    var cmds: any = [];
    var i: any = 0;
    while (i < this.commands.length) {
      var cmd: any = this.commands[i];
      if (cmd instanceof PipeBoth) {
        i += 1;
        continue;
      }
      var needsRedirect: any = i + 1 < this.commands.length && this.commands[i + 1].kind === "pipe-both";
      cmds.push([cmd, needsRedirect]);
      i += 1;
    }
    if (cmds.length === 1) {
      var pair: any = cmds[0];
      cmd = pair[0];
      var needs: any = pair[1];
      return this.CmdSexp(cmd, needs);
    }
    var lastPair: any = cmds[cmds.length - 1];
    var lastCmd: any = lastPair[0];
    var lastNeeds: any = lastPair[1];
    var result: any = this.CmdSexp(lastCmd, lastNeeds);
    var j: any = cmds.length - 2;
    while (j >= 0) {
      var pair: any = cmds[j];
      cmd = pair[0];
      var needs: any = pair[1];
      if (needs && cmd.kind !== "command") {
        result = "(pipe " + cmd.toSexp() + " (redirect \">&\" 1) " + result + ")";
      } else {
        result = "(pipe " + this.CmdSexp(cmd, needs) + " " + result + ")";
      }
      j -= 1;
    }
    return result;
  }

  CmdSexp(cmd: Node, needsRedirect: boolean): string {
    if (!needsRedirect) {
      return cmd.toSexp();
    }
    if (cmd instanceof Command) {
      var parts: any = [];
      for (const w of cmd.words) {
        parts.push(w.toSexp());
      }
      for (const r of cmd.redirects) {
        parts.push(r.toSexp());
      }
      parts.push("(redirect \">&\" 1)");
      return "(command " + parts.join(" ") + ")";
    }
    return cmd.toSexp();
  }
}

class List implements Node {
  parts: Node[];
  kind: string;

  constructor(parts: Node[] = [], kind: string = "") {
    this.parts = parts;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var parts: any = this.parts.slice();
    var opNames: any = new Map([["&&", "and"], ["||", "or"], [";", "semi"], ["\n", "semi"], ["&", "background"]]);
    while (parts.length > 1 && parts[parts.length - 1].kind === "operator" && ((parts[parts.length - 1] as unknown as Operator).op === ";" || (parts[parts.length - 1] as unknown as Operator).op === "\n")) {
      parts = Sublist(parts, 0, parts.length - 1);
    }
    if (parts.length === 1) {
      return parts[0].toSexp();
    }
    if (parts[parts.length - 1].kind === "operator" && (parts[parts.length - 1] as unknown as Operator).op === "&") {
      for (const i of range(parts.length - 3, 0, -2)) {
        if (parts[i].kind === "operator" && ((parts[i] as unknown as Operator).op === ";" || (parts[i] as unknown as Operator).op === "\n")) {
          var left: any = Sublist(parts, 0, i);
          var right: any = Sublist(parts, i + 1, parts.length - 1);
          if (left.length > 1) {
            var leftSexp: any = new List(left as any, "list" as any).toSexp();
          } else {
            var leftSexp: any = left[0].toSexp();
          }
          if (right.length > 1) {
            var rightSexp: any = new List(right as any, "list" as any).toSexp();
          } else {
            var rightSexp: any = right[0].toSexp();
          }
          return "(semi " + leftSexp + " (background " + rightSexp + "))";
        }
      }
      var innerParts: any = Sublist(parts, 0, parts.length - 1);
      if (innerParts.length === 1) {
        return "(background " + innerParts[0].toSexp() + ")";
      }
      var innerList: any = new List(innerParts as any, "list" as any);
      return "(background " + innerList.toSexp() + ")";
    }
    return this.ToSexpWithPrecedence(parts, opNames);
  }

  ToSexpWithPrecedence(parts: Node[], opNames: Map<string, string>): string {
    var semiPositions: any = [];
    for (const i of range(parts.length)) {
      if (parts[i].kind === "operator" && ((parts[i] as unknown as Operator).op === ";" || (parts[i] as unknown as Operator).op === "\n")) {
        semiPositions.push(i);
      }
    }
    if (semiPositions.length > 0) {
      var segments: any = [];
      var start: any = 0;
      for (const pos of semiPositions) {
        var seg: any = Sublist(parts, start, pos);
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
      var result: any = this.ToSexpAmpAndHigher(segments[0], opNames);
      for (const i of range(1, segments.length)) {
        result = "(semi " + result + " " + this.ToSexpAmpAndHigher(segments[i], opNames) + ")";
      }
      return result;
    }
    return this.ToSexpAmpAndHigher(parts, opNames);
  }

  ToSexpAmpAndHigher(parts: Node[], opNames: Map<string, string>): string {
    if (parts.length === 1) {
      return parts[0].toSexp();
    }
    var ampPositions: any = [];
    for (const i of range(1, parts.length - 1, 2)) {
      if (parts[i].kind === "operator" && (parts[i] as unknown as Operator).op === "&") {
        ampPositions.push(i);
      }
    }
    if (ampPositions.length > 0) {
      var segments: any = [];
      var start: any = 0;
      for (const pos of ampPositions) {
        segments.push(Sublist(parts, start, pos));
        start = pos + 1;
      }
      segments.push(Sublist(parts, start, parts.length));
      var result: any = this.ToSexpAndOr(segments[0], opNames);
      for (const i of range(1, segments.length)) {
        result = "(background " + result + " " + this.ToSexpAndOr(segments[i], opNames) + ")";
      }
      return result;
    }
    return this.ToSexpAndOr(parts, opNames);
  }

  ToSexpAndOr(parts: Node[], opNames: Map<string, string>): string {
    if (parts.length === 1) {
      return parts[0].toSexp();
    }
    var result: any = parts[0].toSexp();
    for (const i of range(1, parts.length - 1, 2)) {
      var op: any = parts[i];
      var cmd: any = parts[i + 1];
      var opName: any = opNames.get((op as unknown as Operator).op) ?? (op as unknown as Operator).op;
      result = "(" + opName + " " + result + " " + cmd.toSexp() + ")";
    }
    return result;
  }
}

class Operator implements Node {
  op: string;
  kind: string;

  constructor(op: string = "", kind: string = "") {
    this.op = op;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var names: any = new Map([["&&", "and"], ["||", "or"], [";", "semi"], ["&", "bg"], ["|", "pipe"]]);
    return ("(" + (names.get(this.op) ?? this.op)) + ")";
  }
}

class PipeBoth implements Node {
  kind: string;

  constructor(kind: string = "") {
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(pipe-both)";
  }
}

class Empty implements Node {
  kind: string;

  constructor(kind: string = "") {
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "";
  }
}

class Comment implements Node {
  text: string;
  kind: string;

  constructor(text: string = "", kind: string = "") {
    this.text = text;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "";
  }
}

class Redirect implements Node {
  op: string;
  target: Word;
  fd: number | null;
  kind: string;

  constructor(op: string = "", target: Word = null, fd: number | null = null, kind: string = "") {
    this.op = op;
    this.target = target;
    this.fd = fd;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var op: any = this.op.replace(/^[0123456789]+/, '');
    if (op.startsWith("{")) {
      var j: any = 1;
      if (j < op.length && (/^[a-zA-Z]$/.test((op[j] as unknown as string)) || (op[j] as unknown as string) === "_")) {
        j += 1;
        while (j < op.length && (/^[a-zA-Z0-9]$/.test((op[j] as unknown as string)) || (op[j] as unknown as string) === "_")) {
          j += 1;
        }
        if (j < op.length && (op[j] as unknown as string) === "[") {
          j += 1;
          while (j < op.length && (op[j] as unknown as string) !== "]") {
            j += 1;
          }
          if (j < op.length && (op[j] as unknown as string) === "]") {
            j += 1;
          }
        }
        if (j < op.length && (op[j] as unknown as string) === "}") {
          op = Substring(op, j + 1, op.length);
        }
      }
    }
    var targetVal: any = this.target.value;
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
      var raw: any = Substring(targetVal, 1, targetVal.length);
      if (/^[0-9]$/.test(raw) && parseInt(raw, 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(raw, 10)) + ")";
      }
      if (raw.endsWith("-") && /^[0-9]$/.test(raw.slice(0, raw.length - 1)) && parseInt(raw.slice(0, raw.length - 1), 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(raw.slice(0, raw.length - 1), 10)) + ")";
      }
      if (targetVal === "&-") {
        return "(redirect \">&-\" 0)";
      }
      var fdTarget: any = raw.endsWith("-") ? raw.slice(0, raw.length - 1) : raw;
      return "(redirect \"" + op + "\" \"" + fdTarget + "\")";
    }
    if (op === ">&" || op === "<&") {
      if (/^[0-9]$/.test(targetVal) && parseInt(targetVal, 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(targetVal, 10)) + ")";
      }
      if (targetVal === "-") {
        return "(redirect \">&-\" 0)";
      }
      if (targetVal.endsWith("-") && /^[0-9]$/.test(targetVal.slice(0, targetVal.length - 1)) && parseInt(targetVal.slice(0, targetVal.length - 1), 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(targetVal.slice(0, targetVal.length - 1), 10)) + ")";
      }
      var outVal: any = targetVal.endsWith("-") ? targetVal.slice(0, targetVal.length - 1) : targetVal;
      return "(redirect \"" + op + "\" \"" + outVal + "\")";
    }
    return "(redirect \"" + op + "\" \"" + targetVal + "\")";
  }
}

class HereDoc implements Node {
  delimiter: string;
  content: string;
  stripTabs: boolean;
  quoted: boolean;
  fd: number | null;
  complete: boolean;
  StartPos: number;
  kind: string;

  constructor(delimiter: string = "", content: string = "", stripTabs: boolean = false, quoted: boolean = false, fd: number | null = null, complete: boolean = false, StartPos: number = 0, kind: string = "") {
    this.delimiter = delimiter;
    this.content = content;
    this.stripTabs = stripTabs;
    this.quoted = quoted;
    this.fd = fd;
    this.complete = complete;
    this.StartPos = StartPos;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var op: any = this.stripTabs ? "<<-" : "<<";
    var content: any = this.content;
    if (content.endsWith("\\") && !content.endsWith("\\\\")) {
      content = content + "\\";
    }
    return `(redirect "%v" "%v")`;
  }
}

class Subshell implements Node {
  body: Node;
  redirects: Node[];
  kind: string;

  constructor(body: Node = null, redirects: Node[] = [], kind: string = "") {
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var base: any = "(subshell " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }
}

class BraceGroup implements Node {
  body: Node;
  redirects: Node[];
  kind: string;

  constructor(body: Node = null, redirects: Node[] = [], kind: string = "") {
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var base: any = "(brace-group " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }
}

class If implements Node {
  condition: Node;
  thenBody: Node;
  elseBody: Node;
  redirects: Node[];
  kind: string;

  constructor(condition: Node = null, thenBody: Node = null, elseBody: Node = null, redirects: Node[] = [], kind: string = "") {
    this.condition = condition;
    this.thenBody = thenBody;
    this.elseBody = elseBody;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var result: any = "(if " + this.condition.toSexp() + " " + this.thenBody.toSexp();
    if (this.elseBody !== null) {
      result = result + " " + this.elseBody.toSexp();
    }
    result = result + ")";
    for (const r of this.redirects) {
      result = result + " " + r.toSexp();
    }
    return result;
  }
}

class While implements Node {
  condition: Node;
  body: Node;
  redirects: Node[];
  kind: string;

  constructor(condition: Node = null, body: Node = null, redirects: Node[] = [], kind: string = "") {
    this.condition = condition;
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var base: any = "(while " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }
}

class Until implements Node {
  condition: Node;
  body: Node;
  redirects: Node[];
  kind: string;

  constructor(condition: Node = null, body: Node = null, redirects: Node[] = [], kind: string = "") {
    this.condition = condition;
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var base: any = "(until " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }
}

class For implements Node {
  varName: string;
  words: Word[];
  body: Node;
  redirects: Node[];
  kind: string;

  constructor(varName: string = "", words: Word[] = [], body: Node = null, redirects: Node[] = [], kind: string = "") {
    this.varName = varName;
    this.words = words;
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var suffix: any = "";
    if (this.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of this.redirects) {
        redirectParts.push(r.toSexp());
      }
      suffix = " " + redirectParts.join(" ");
    }
    var tempWord: any = new Word(this.varName as any, [] as any, "word" as any);
    var varFormatted: any = tempWord.FormatCommandSubstitutions(this.varName, false);
    var varEscaped: any = varFormatted.replace("\\", "\\\\").replace("\"", "\\\"");
    if (this.words === null) {
      return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + this.body.toSexp() + ")" + suffix;
    } else {
      if (this.words.length === 0) {
        return "(for (word \"" + varEscaped + "\") (in) " + this.body.toSexp() + ")" + suffix;
      } else {
        var wordParts: any = [];
        for (const w of this.words) {
          wordParts.push(w.toSexp());
        }
        var wordStrs: any = wordParts.join(" ");
        return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + this.body.toSexp() + ")" + suffix;
      }
    }
  }
}

class ForArith implements Node {
  init: string;
  cond: string;
  incr: string;
  body: Node;
  redirects: Node[];
  kind: string;

  constructor(init: string = "", cond: string = "", incr: string = "", body: Node = null, redirects: Node[] = [], kind: string = "") {
    this.init = init;
    this.cond = cond;
    this.incr = incr;
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var suffix: any = "";
    if (this.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of this.redirects) {
        redirectParts.push(r.toSexp());
      }
      suffix = " " + redirectParts.join(" ");
    }
    var initVal: any = this.init !== "" ? this.init : "1";
    var condVal: any = this.cond !== "" ? this.cond : "1";
    var incrVal: any = this.incr !== "" ? this.incr : "1";
    var initStr: any = FormatArithVal(initVal);
    var condStr: any = FormatArithVal(condVal);
    var incrStr: any = FormatArithVal(incrVal);
    var bodyStr: any = this.body.toSexp();
    return `(arith-for (init (word "%v")) (test (word "%v")) (step (word "%v")) %v)%v`;
  }
}

class Select implements Node {
  varName: string;
  words: Word[];
  body: Node;
  redirects: Node[];
  kind: string;

  constructor(varName: string = "", words: Word[] = [], body: Node = null, redirects: Node[] = [], kind: string = "") {
    this.varName = varName;
    this.words = words;
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var suffix: any = "";
    if (this.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of this.redirects) {
        redirectParts.push(r.toSexp());
      }
      suffix = " " + redirectParts.join(" ");
    }
    var varEscaped: any = this.varName.replace("\\", "\\\\").replace("\"", "\\\"");
    if (this.words !== null) {
      var wordParts: any = [];
      for (const w of this.words) {
        wordParts.push(w.toSexp());
      }
      var wordStrs: any = wordParts.join(" ");
      if (this.words.length > 0) {
        var inClause: any = "(in " + wordStrs + ")";
      } else {
        var inClause: any = "(in)";
      }
    } else {
      var inClause: any = "(in (word \"\\\"$@\\\"\"))";
    }
    return "(select (word \"" + varEscaped + "\") " + inClause + " " + this.body.toSexp() + ")" + suffix;
  }
}

class Case implements Node {
  word: Node;
  patterns: Node[];
  redirects: Node[];
  kind: string;

  constructor(word: Node = null, patterns: Node[] = [], redirects: Node[] = [], kind: string = "") {
    this.word = word;
    this.patterns = patterns;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var parts: any = [];
    parts.push("(case " + this.word.toSexp());
    for (const p of this.patterns) {
      parts.push(p.toSexp());
    }
    var base: any = parts.join(" ") + ")";
    return AppendRedirects(base, this.redirects);
  }
}

class CasePattern implements Node {
  pattern: string;
  body: Node;
  terminator: string;
  kind: string;

  constructor(pattern: string = "", body: Node = null, terminator: string = "", kind: string = "") {
    this.pattern = pattern;
    this.body = body;
    this.terminator = terminator;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var alternatives: any = [];
    var current: any = [];
    var i: any = 0;
    var depth: any = 0;
    while (i < this.pattern.length) {
      var ch: any = (this.pattern[i] as unknown as string);
      if (ch === "\\" && i + 1 < this.pattern.length) {
        current.push(Substring(this.pattern, i, i + 2));
        i += 2;
      } else {
        if ((ch === "@" || ch === "?" || ch === "*" || ch === "+" || ch === "!") && i + 1 < this.pattern.length && (this.pattern[i + 1] as unknown as string) === "(") {
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
                if (ch === "[") {
                  var [result0, result1, result2]: any = ConsumeBracketClass(this.pattern, i, depth);
                  i = result0;
                  current.push(...result1);
                } else {
                  if (ch === "'" && depth === 0) {
                    var [result0, result1]: any = ConsumeSingleQuote(this.pattern, i);
                    i = result0;
                    current.push(...result1);
                  } else {
                    if (ch === "\"" && depth === 0) {
                      var [result0, result1]: any = ConsumeDoubleQuote(this.pattern, i);
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
    var wordList: any = [];
    for (const alt of alternatives) {
      wordList.push(new Word(alt as any, "word" as any).toSexp());
    }
    var patternStr: any = wordList.join(" ");
    var parts: any = ["(pattern (" + patternStr + ")"];
    if (this.body !== null) {
      parts.push(" " + this.body.toSexp());
    } else {
      parts.push(" ()");
    }
    parts.push(")");
    return parts.join("");
  }
}

class FunctionName implements Node {
  name: string;
  body: Node;
  kind: string;

  constructor(name: string = "", body: Node = null, kind: string = "") {
    this.name = name;
    this.body = body;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(function \"" + this.name + "\" " + this.body.toSexp() + ")";
  }
}

class ParamExpansion implements Node {
  param: string;
  op: string;
  arg: string;
  kind: string;

  constructor(param: string = "", op: string = "", arg: string = "", kind: string = "") {
    this.param = param;
    this.op = op;
    this.arg = arg;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var escapedParam: any = this.param.replace("\\", "\\\\").replace("\"", "\\\"");
    if (this.op !== "") {
      var escapedOp: any = this.op.replace("\\", "\\\\").replace("\"", "\\\"");
      if (this.arg !== "") {
        var argVal: any = this.arg;
      } else {
        var argVal: any = "";
      }
      var escapedArg: any = argVal.replace("\\", "\\\\").replace("\"", "\\\"");
      return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
    }
    return "(param \"" + escapedParam + "\")";
  }
}

class ParamLength implements Node {
  param: string;
  kind: string;

  constructor(param: string = "", kind: string = "") {
    this.param = param;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var escaped: any = this.param.replace("\\", "\\\\").replace("\"", "\\\"");
    return "(param-len \"" + escaped + "\")";
  }
}

class ParamIndirect implements Node {
  param: string;
  op: string;
  arg: string;
  kind: string;

  constructor(param: string = "", op: string = "", arg: string = "", kind: string = "") {
    this.param = param;
    this.op = op;
    this.arg = arg;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var escaped: any = this.param.replace("\\", "\\\\").replace("\"", "\\\"");
    if (this.op !== "") {
      var escapedOp: any = this.op.replace("\\", "\\\\").replace("\"", "\\\"");
      if (this.arg !== "") {
        var argVal: any = this.arg;
      } else {
        var argVal: any = "";
      }
      var escapedArg: any = argVal.replace("\\", "\\\\").replace("\"", "\\\"");
      return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
    }
    return "(param-indirect \"" + escaped + "\")";
  }
}

class CommandSubstitution implements Node {
  command: Node;
  brace: boolean;
  kind: string;

  constructor(command: Node = null, brace: boolean = false, kind: string = "") {
    this.command = command;
    this.brace = brace;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    if (this.brace) {
      return "(funsub " + this.command.toSexp() + ")";
    }
    return "(cmdsub " + this.command.toSexp() + ")";
  }
}

class ArithmeticExpansion implements Node {
  expression: Node | null;
  kind: string;

  constructor(expression: Node | null = null, kind: string = "") {
    this.expression = expression;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    if (this.expression === null) {
      return "(arith)";
    }
    return "(arith " + this.expression.toSexp() + ")";
  }
}

class ArithmeticCommand implements Node {
  expression: Node | null;
  redirects: Node[];
  rawContent: string;
  kind: string;

  constructor(expression: Node | null = null, redirects: Node[] = [], rawContent: string = "", kind: string = "") {
    this.expression = expression;
    this.redirects = redirects;
    this.rawContent = rawContent;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var formatted: any = new Word(this.rawContent as any, "word" as any).FormatCommandSubstitutions(this.rawContent, true);
    var escaped: any = formatted.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\t", "\\t");
    var result: any = "(arith (word \"" + escaped + "\"))";
    if (this.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of this.redirects) {
        redirectParts.push(r.toSexp());
      }
      var redirectSexps: any = redirectParts.join(" ");
      return result + " " + redirectSexps;
    }
    return result;
  }
}

class ArithNumber implements Node {
  value: string;
  kind: string;

  constructor(value: string = "", kind: string = "") {
    this.value = value;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(number \"" + this.value + "\")";
  }
}

class ArithEmpty implements Node {
  kind: string;

  constructor(kind: string = "") {
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(empty)";
  }
}

class ArithVar implements Node {
  name: string;
  kind: string;

  constructor(name: string = "", kind: string = "") {
    this.name = name;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(var \"" + this.name + "\")";
  }
}

class ArithBinaryOp implements Node {
  op: string;
  left: Node;
  right: Node;
  kind: string;

  constructor(op: string = "", left: Node = null, right: Node = null, kind: string = "") {
    this.op = op;
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(binary-op \"" + this.op + "\" " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }
}

class ArithUnaryOp implements Node {
  op: string;
  operand: Node;
  kind: string;

  constructor(op: string = "", operand: Node = null, kind: string = "") {
    this.op = op;
    this.operand = operand;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(unary-op \"" + this.op + "\" " + this.operand.toSexp() + ")";
  }
}

class ArithPreIncr implements Node {
  operand: Node;
  kind: string;

  constructor(operand: Node = null, kind: string = "") {
    this.operand = operand;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(pre-incr " + this.operand.toSexp() + ")";
  }
}

class ArithPostIncr implements Node {
  operand: Node;
  kind: string;

  constructor(operand: Node = null, kind: string = "") {
    this.operand = operand;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(post-incr " + this.operand.toSexp() + ")";
  }
}

class ArithPreDecr implements Node {
  operand: Node;
  kind: string;

  constructor(operand: Node = null, kind: string = "") {
    this.operand = operand;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(pre-decr " + this.operand.toSexp() + ")";
  }
}

class ArithPostDecr implements Node {
  operand: Node;
  kind: string;

  constructor(operand: Node = null, kind: string = "") {
    this.operand = operand;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(post-decr " + this.operand.toSexp() + ")";
  }
}

class ArithAssign implements Node {
  op: string;
  target: Node;
  value: Node;
  kind: string;

  constructor(op: string = "", target: Node = null, value: Node = null, kind: string = "") {
    this.op = op;
    this.target = target;
    this.value = value;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(assign \"" + this.op + "\" " + this.target.toSexp() + " " + this.value.toSexp() + ")";
  }
}

class ArithTernary implements Node {
  condition: Node;
  ifTrue: Node;
  ifFalse: Node;
  kind: string;

  constructor(condition: Node = null, ifTrue: Node = null, ifFalse: Node = null, kind: string = "") {
    this.condition = condition;
    this.ifTrue = ifTrue;
    this.ifFalse = ifFalse;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(ternary " + this.condition.toSexp() + " " + this.ifTrue.toSexp() + " " + this.ifFalse.toSexp() + ")";
  }
}

class ArithComma implements Node {
  left: Node;
  right: Node;
  kind: string;

  constructor(left: Node = null, right: Node = null, kind: string = "") {
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(comma " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }
}

class ArithSubscript implements Node {
  array: string;
  index: Node;
  kind: string;

  constructor(array: string = "", index: Node = null, kind: string = "") {
    this.array = array;
    this.index = index;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(subscript \"" + this.array + "\" " + this.index.toSexp() + ")";
  }
}

class ArithEscape implements Node {
  char: string;
  kind: string;

  constructor(char: string = "", kind: string = "") {
    this.char = char;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(escape \"" + this.char + "\")";
  }
}

class ArithDeprecated implements Node {
  expression: string;
  kind: string;

  constructor(expression: string = "", kind: string = "") {
    this.expression = expression;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var escaped: any = this.expression.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    return "(arith-deprecated \"" + escaped + "\")";
  }
}

class ArithConcat implements Node {
  parts: Node[];
  kind: string;

  constructor(parts: Node[] = [], kind: string = "") {
    this.parts = parts;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var sexps: any = [];
    for (const p of this.parts) {
      sexps.push(p.toSexp());
    }
    return "(arith-concat " + sexps.join(" ") + ")";
  }
}

class AnsiCQuote implements Node {
  content: string;
  kind: string;

  constructor(content: string = "", kind: string = "") {
    this.content = content;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var escaped: any = this.content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    return "(ansi-c \"" + escaped + "\")";
  }
}

class LocaleString implements Node {
  content: string;
  kind: string;

  constructor(content: string = "", kind: string = "") {
    this.content = content;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var escaped: any = this.content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    return "(locale \"" + escaped + "\")";
  }
}

class ProcessSubstitution implements Node {
  direction: string;
  command: Node;
  kind: string;

  constructor(direction: string = "", command: Node = null, kind: string = "") {
    this.direction = direction;
    this.command = command;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(procsub \"" + this.direction + "\" " + this.command.toSexp() + ")";
  }
}

class Negation implements Node {
  pipeline: Node;
  kind: string;

  constructor(pipeline: Node = null, kind: string = "") {
    this.pipeline = pipeline;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    if (this.pipeline === null) {
      return "(negation (command))";
    }
    return "(negation " + this.pipeline.toSexp() + ")";
  }
}

class Time implements Node {
  pipeline: Node;
  posix: boolean;
  kind: string;

  constructor(pipeline: Node = null, posix: boolean = false, kind: string = "") {
    this.pipeline = pipeline;
    this.posix = posix;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
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
}

class ConditionalExpr implements Node {
  body: any;
  redirects: Node[];
  kind: string;

  constructor(body: any = null, redirects: Node[] = [], kind: string = "") {
    this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var body: any = this.body;
    if (typeof body === 'string') {
      var escaped: any = body.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
      var result: any = "(cond \"" + escaped + "\")";
    } else {
      var result: any = "(cond " + body.toSexp() + ")";
    }
    if (this.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of this.redirects) {
        redirectParts.push(r.toSexp());
      }
      var redirectSexps: any = redirectParts.join(" ");
      return result + " " + redirectSexps;
    }
    return result;
  }
}

class UnaryTest implements Node {
  op: string;
  operand: Node;
  kind: string;

  constructor(op: string = "", operand: Node = null, kind: string = "") {
    this.op = op;
    this.operand = operand;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var operandVal: any = (this.operand as unknown as Word).getCondFormattedValue();
    return "(cond-unary \"" + this.op + "\" (cond-term \"" + operandVal + "\"))";
  }
}

class BinaryTest implements Node {
  op: string;
  left: Node;
  right: Node;
  kind: string;

  constructor(op: string = "", left: Node = null, right: Node = null, kind: string = "") {
    this.op = op;
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    var leftVal: any = (this.left as unknown as Word).getCondFormattedValue();
    var rightVal: any = (this.right as unknown as Word).getCondFormattedValue();
    return "(cond-binary \"" + this.op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))";
  }
}

class CondAnd implements Node {
  left: Node;
  right: Node;
  kind: string;

  constructor(left: Node = null, right: Node = null, kind: string = "") {
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(cond-and " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }
}

class CondOr implements Node {
  left: Node;
  right: Node;
  kind: string;

  constructor(left: Node = null, right: Node = null, kind: string = "") {
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(cond-or " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }
}

class CondNot implements Node {
  operand: Node;
  kind: string;

  constructor(operand: Node = null, kind: string = "") {
    this.operand = operand;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return this.operand.toSexp();
  }
}

class CondParen implements Node {
  inner: Node;
  kind: string;

  constructor(inner: Node = null, kind: string = "") {
    this.inner = inner;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    return "(cond-expr " + this.inner.toSexp() + ")";
  }
}

class ArrayName implements Node {
  elements: Word[];
  kind: string;

  constructor(elements: Word[] = [], kind: string = "") {
    this.elements = elements;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    if (!(this.elements.length > 0)) {
      return "(array)";
    }
    var parts: any = [];
    for (const e of this.elements) {
      parts.push(e.toSexp());
    }
    var inner: any = parts.join(" ");
    return "(array " + inner + ")";
  }
}

class Coproc implements Node {
  command: Node;
  name: string;
  kind: string;

  constructor(command: Node = null, name: string = "", kind: string = "") {
    this.command = command;
    this.name = name;
    this.kind = kind;
  }

  getKind(): string {
    return this.kind;
  }

  toSexp(): string {
    if (this.name !== "") {
      var name: any = this.name;
    } else {
      var name: any = "COPROC";
    }
    return "(coproc \"" + name + "\" " + this.command.toSexp() + ")";
  }
}

class Parser {
  source: string;
  pos: number;
  length: number;
  PendingHeredocs: HereDoc[];
  CmdsubHeredocEnd: number;
  SawNewlineInSingleQuote: boolean;
  InProcessSub: boolean;
  Extglob: boolean;
  Ctx: ContextStack;
  Lexer: Lexer;
  TokenHistory: Token[];
  ParserState: number;
  DolbraceState: number;
  EofToken: string;
  WordContext: number;
  AtCommandStart: boolean;
  InArrayLiteral: boolean;
  InAssignBuiltin: boolean;
  ArithSrc: string;
  ArithPos: number;
  ArithLen: number;

  constructor(source: string = "", pos: number = 0, length: number = 0, PendingHeredocs: HereDoc[] = [], CmdsubHeredocEnd: number = 0, SawNewlineInSingleQuote: boolean = false, InProcessSub: boolean = false, Extglob: boolean = false, Ctx: ContextStack = null, Lexer: Lexer = null, TokenHistory: Token[] = [], ParserState: number = 0, DolbraceState: number = 0, EofToken: string = "", WordContext: number = 0, AtCommandStart: boolean = false, InArrayLiteral: boolean = false, InAssignBuiltin: boolean = false, ArithSrc: string = "", ArithPos: number = 0, ArithLen: number = 0) {
    this.source = source;
    this.pos = pos;
    this.length = length;
    this.PendingHeredocs = PendingHeredocs;
    this.CmdsubHeredocEnd = CmdsubHeredocEnd;
    this.SawNewlineInSingleQuote = SawNewlineInSingleQuote;
    this.InProcessSub = InProcessSub;
    this.Extglob = Extglob;
    this.Ctx = Ctx;
    this.Lexer = Lexer;
    this.TokenHistory = TokenHistory;
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

  SetState(flag: number): void {
    this.ParserState = this.ParserState | flag;
  }

  ClearState(flag: number): void {
    this.ParserState = this.ParserState & ~flag;
  }

  InState(flag: number): boolean {
    return (this.ParserState & flag) !== 0;
  }

  SaveParserState(): SavedParserState {
    return new SavedParserState(this.ParserState as any, this.DolbraceState as any, this.PendingHeredocs as any, this.Ctx.copyStack() as any, this.EofToken as any);
  }

  RestoreParserState(saved: SavedParserState): void {
    this.ParserState = saved.parserState;
    this.DolbraceState = saved.dolbraceState;
    this.EofToken = saved.eofToken;
    this.Ctx.restoreFrom(saved.ctxStack);
  }

  RecordToken(tok: Token): void {
    this.TokenHistory = [tok, this.TokenHistory[0], this.TokenHistory[1], this.TokenHistory[2]];
  }

  UpdateDolbraceForOp(op: string, hasParam: boolean): void {
    if (this.DolbraceState === DolbraceState_NONE) {
      return;
    }
    if (op === "" || op.length === 0) {
      return;
    }
    var firstChar: any = (op[0] as unknown as string);
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

  SyncLexer(): void {
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

  SyncParser(): void {
    this.pos = this.Lexer.pos;
  }

  LexPeekToken(): Token {
    if (this.Lexer.TokenCache !== null && this.Lexer.TokenCache.pos === this.pos && this.Lexer.CachedWordContext === this.WordContext && this.Lexer.CachedAtCommandStart === this.AtCommandStart && this.Lexer.CachedInArrayLiteral === this.InArrayLiteral && this.Lexer.CachedInAssignBuiltin === this.InAssignBuiltin) {
      return this.Lexer.TokenCache;
    }
    var savedPos: any = this.pos;
    this.SyncLexer();
    var result: any = this.Lexer.peekToken();
    this.Lexer.CachedWordContext = this.WordContext;
    this.Lexer.CachedAtCommandStart = this.AtCommandStart;
    this.Lexer.CachedInArrayLiteral = this.InArrayLiteral;
    this.Lexer.CachedInAssignBuiltin = this.InAssignBuiltin;
    this.Lexer.PostReadPos = this.Lexer.pos;
    this.pos = savedPos;
    return result;
  }

  LexNextToken(): Token {
    if (this.Lexer.TokenCache !== null && this.Lexer.TokenCache.pos === this.pos && this.Lexer.CachedWordContext === this.WordContext && this.Lexer.CachedAtCommandStart === this.AtCommandStart && this.Lexer.CachedInArrayLiteral === this.InArrayLiteral && this.Lexer.CachedInAssignBuiltin === this.InAssignBuiltin) {
      var tok: any = this.Lexer.nextToken();
      this.pos = this.Lexer.PostReadPos;
      this.Lexer.pos = this.Lexer.PostReadPos;
    } else {
      this.SyncLexer();
      var tok: any = this.Lexer.nextToken();
      this.Lexer.CachedWordContext = this.WordContext;
      this.Lexer.CachedAtCommandStart = this.AtCommandStart;
      this.Lexer.CachedInArrayLiteral = this.InArrayLiteral;
      this.Lexer.CachedInAssignBuiltin = this.InAssignBuiltin;
      this.SyncParser();
    }
    this.RecordToken(tok);
    return tok;
  }

  LexSkipBlanks(): void {
    this.SyncLexer();
    this.Lexer.skipBlanks();
    this.SyncParser();
  }

  LexSkipComment(): boolean {
    this.SyncLexer();
    var result: any = this.Lexer.SkipComment();
    this.SyncParser();
    return result;
  }

  LexIsCommandTerminator(): boolean {
    var tok: any = this.LexPeekToken();
    var t: any = tok.typeName;
    return t === TokenType_EOF || t === TokenType_NEWLINE || t === TokenType_PIPE || t === TokenType_SEMI || t === TokenType_LPAREN || t === TokenType_RPAREN || t === TokenType_AMP;
  }

  LexPeekOperator(): [number, string] {
    var tok: any = this.LexPeekToken();
    var t: any = tok.typeName;
    if (t >= TokenType_SEMI && t <= TokenType_GREATER || t >= TokenType_AND_AND && t <= TokenType_PIPE_AMP) {
      return [t, tok.value];
    }
    return [0, ""];
  }

  LexPeekReservedWord(): string {
    var tok: any = this.LexPeekToken();
    if (tok.typeName !== TokenType_WORD) {
      return "";
    }
    var word: any = tok.value;
    if (word.endsWith("\\\n")) {
      word = word.slice(0, word.length - 2);
    }
    if (RESERVED_WORDS.has(word) || (word === "{" || word === "}" || word === "[[" || word === "]]" || word === "!" || word === "time")) {
      return word;
    }
    return "";
  }

  LexIsAtReservedWord(word: string): boolean {
    var reserved: any = this.LexPeekReservedWord();
    return reserved === word;
  }

  LexConsumeWord(expected: string): boolean {
    var tok: any = this.LexPeekToken();
    if (tok.typeName !== TokenType_WORD) {
      return false;
    }
    var word: any = tok.value;
    if (word.endsWith("\\\n")) {
      word = word.slice(0, word.length - 2);
    }
    if (word === expected) {
      this.LexNextToken();
      return true;
    }
    return false;
  }

  LexPeekCaseTerminator(): string {
    var tok: any = this.LexPeekToken();
    var t: any = tok.typeName;
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

  atEnd(): boolean {
    return this.pos >= this.length;
  }

  peek(): string {
    if (this.atEnd()) {
      return "";
    }
    return (this.source[this.pos] as unknown as string);
  }

  advance(): string {
    if (this.atEnd()) {
      return "";
    }
    var ch: any = (this.source[this.pos] as unknown as string);
    this.pos += 1;
    return ch;
  }

  peekAt(offset: number): string {
    var pos: any = this.pos + offset;
    if (pos < 0 || pos >= this.length) {
      return "";
    }
    return (this.source[pos] as unknown as string);
  }

  lookahead(n: number): string {
    return Substring(this.source, this.pos, this.pos + n);
  }

  IsBangFollowedByProcsub(): boolean {
    if (this.pos + 2 >= this.length) {
      return false;
    }
    var nextChar: any = (this.source[this.pos + 1] as unknown as string);
    if (nextChar !== ">" && nextChar !== "<") {
      return false;
    }
    return (this.source[this.pos + 2] as unknown as string) === "(";
  }

  skipWhitespace(): void {
    while (!this.atEnd()) {
      this.LexSkipBlanks();
      if (this.atEnd()) {
        break;
      }
      var ch: any = this.peek();
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

  skipWhitespaceAndNewlines(): void {
    while (!this.atEnd()) {
      var ch: any = this.peek();
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

  AtListTerminatingBracket(): boolean {
    if (this.atEnd()) {
      return false;
    }
    var ch: any = this.peek();
    if (this.EofToken !== "" && ch === this.EofToken) {
      return true;
    }
    if (ch === ")") {
      return true;
    }
    if (ch === "}") {
      var nextPos: any = this.pos + 1;
      if (nextPos >= this.length) {
        return true;
      }
      return IsWordEndContext((this.source[nextPos] as unknown as string));
    }
    return false;
  }

  AtEofToken(): boolean {
    if (this.EofToken === "") {
      return false;
    }
    var tok: any = this.LexPeekToken();
    if (this.EofToken === ")") {
      return tok.typeName === TokenType_RPAREN;
    }
    if (this.EofToken === "}") {
      return tok.typeName === TokenType_WORD && tok.value === "}";
    }
    return false;
  }

  CollectRedirects(): Node[] {
    var redirects: any = [];
    while (true) {
      this.skipWhitespace();
      var redirect: any = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    return redirects.length > 0 ? redirects : null;
  }

  ParseLoopBody(context: string): Node {
    if (this.peek() === "{") {
      var brace: any = this.parseBraceGroup();
      if (brace === null) {
        throw new Error(`${`Expected brace group body in %v`} at position ${this.LexPeekToken().pos}`)
      }
      return brace.body;
    }
    if (this.LexConsumeWord("do")) {
      var body: any = this.parseListUntil(new Set(["done"]));
      if (body === null) {
        throw new Error(`${"Expected commands after 'do'"} at position ${this.LexPeekToken().pos}`)
      }
      this.skipWhitespaceAndNewlines();
      if (!this.LexConsumeWord("done")) {
        throw new Error(`${`Expected 'done' to close %v`} at position ${this.LexPeekToken().pos}`)
      }
      return body;
    }
    throw new Error(`${`Expected 'do' or '{' in %v`} at position ${this.LexPeekToken().pos}`)
  }

  peekWord(): string {
    var savedPos: any = this.pos;
    this.skipWhitespace();
    if (this.atEnd() || IsMetachar(this.peek())) {
      this.pos = savedPos;
      return "";
    }
    var chars: any = [];
    while (!this.atEnd() && !IsMetachar(this.peek())) {
      var ch: any = this.peek();
      if (IsQuote(ch)) {
        break;
      }
      if (ch === "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "\n") {
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
      var word: any = chars.join("");
    } else {
      var word: any = "";
    }
    this.pos = savedPos;
    return word;
  }

  consumeWord(expected: string): boolean {
    var savedPos: any = this.pos;
    this.skipWhitespace();
    var word: any = this.peekWord();
    var keywordWord: any = word;
    var hasLeadingBrace: any = false;
    if (word !== "" && this.InProcessSub && word.length > 1 && (word[0] as unknown as string) === "}") {
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
    while (this.peek() === "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "\n") {
      this.advance();
      this.advance();
    }
    return true;
  }

  IsWordTerminator(ctx: number, ch: string, bracketDepth: number, parenDepth: number): boolean {
    this.SyncLexer();
    return this.Lexer.IsWordTerminator(ctx, ch, bracketDepth, parenDepth);
  }

  ScanDoubleQuote(chars: string[], parts: Node[], start: number, handleLineContinuation: boolean): void {
    chars.push("\"");
    while (!this.atEnd() && this.peek() !== "\"") {
      var c: any = this.peek();
      if (c === "\\" && this.pos + 1 < this.length) {
        var nextC: any = (this.source[this.pos + 1] as unknown as string);
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
      throw new Error(`${"Unterminated double quote"} at position ${start}`)
    }
    chars.push(this.advance());
  }

  ParseDollarExpansion(chars: string[], parts: Node[], inDquote: boolean): boolean {
    if (this.pos + 2 < this.length && (this.source[this.pos + 1] as unknown as string) === "(" && (this.source[this.pos + 2] as unknown as string) === "(") {
      var [result0, result1]: any = this.ParseArithmeticExpansion();
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
    if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "[") {
      var [result0, result1]: any = this.ParseDeprecatedArithmetic();
      if (result0 !== null) {
        parts.push(result0);
        chars.push(result1);
        return true;
      }
      return false;
    }
    if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
      var [result0, result1]: any = this.ParseCommandSubstitution();
      if (result0 !== null) {
        parts.push(result0);
        chars.push(result1);
        return true;
      }
      return false;
    }
    var [result0, result1]: any = this.ParseParamExpansion(inDquote);
    if (result0 !== null) {
      parts.push(result0);
      chars.push(result1);
      return true;
    }
    return false;
  }

  ParseWordInternal(ctx: number, atCommandStart: boolean, inArrayLiteral: boolean): Word {
    this.WordContext = ctx;
    return this.parseWord(atCommandStart, inArrayLiteral, false);
  }

  parseWord(atCommandStart: boolean, inArrayLiteral: boolean, inAssignBuiltin: boolean): Word {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    this.AtCommandStart = atCommandStart;
    this.InArrayLiteral = inArrayLiteral;
    this.InAssignBuiltin = inAssignBuiltin;
    var tok: any = this.LexPeekToken();
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
  }

  ParseCommandSubstitution(): [Node, string] {
    if (this.atEnd() || this.peek() !== "$") {
      return [null, ""];
    }
    var start: any = this.pos;
    this.advance();
    if (this.atEnd() || this.peek() !== "(") {
      this.pos = start;
      return [null, ""];
    }
    this.advance();
    var saved: any = this.SaveParserState();
    this.SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN);
    this.EofToken = ")";
    var cmd: any = this.parseList(true);
    if (cmd === null) {
      cmd = new Empty("empty" as any);
    }
    this.skipWhitespaceAndNewlines();
    if (this.atEnd() || this.peek() !== ")") {
      this.RestoreParserState(saved);
      this.pos = start;
      return [null, ""];
    }
    this.advance();
    var textEnd: any = this.pos;
    var text: any = Substring(this.source, start, textEnd);
    this.RestoreParserState(saved);
    return [new CommandSubstitution(cmd as any, "cmdsub" as any), text];
  }

  ParseFunsub(start: number): [Node, string] {
    this.SyncParser();
    if (!this.atEnd() && this.peek() === "|") {
      this.advance();
    }
    var saved: any = this.SaveParserState();
    this.SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN);
    this.EofToken = "}";
    var cmd: any = this.parseList(true);
    if (cmd === null) {
      cmd = new Empty("empty" as any);
    }
    this.skipWhitespaceAndNewlines();
    if (this.atEnd() || this.peek() !== "}") {
      this.RestoreParserState(saved);
      throw new Error(`${"unexpected EOF looking for `}'"} at position ${start}`)
    }
    this.advance();
    var text: any = Substring(this.source, start, this.pos);
    this.RestoreParserState(saved);
    this.SyncLexer();
    return [new CommandSubstitution(cmd as any, true as any, "cmdsub" as any), text];
  }

  IsAssignmentWord(word: Node): boolean {
    return Assignment((word as unknown as Word).value, 0) !== -1;
  }

  ParseBacktickSubstitution(): [Node, string] {
    if (this.atEnd() || this.peek() !== "`") {
      return [null, ""];
    }
    var start: any = this.pos;
    this.advance();
    var contentChars: any = [];
    var textChars: any = ["`"];
    var pendingHeredocs: any = [];
    var inHeredocBody: any = false;
    var currentHeredocDelim: any = "";
    var currentHeredocStrip: any = false;
    while (!this.atEnd() && (inHeredocBody || this.peek() !== "`")) {
      if (inHeredocBody) {
        var lineStart: any = this.pos;
        var lineEnd: any = lineStart;
        while (lineEnd < this.length && (this.source[lineEnd] as unknown as string) !== "\n") {
          lineEnd += 1;
        }
        var line: any = Substring(this.source, lineStart, lineEnd);
        var checkLine: any = currentHeredocStrip ? line.replace(/^[\t]+/, '') : line;
        if (checkLine === currentHeredocDelim) {
          for (const ch of line) {
            contentChars.push(ch);
            textChars.push(ch);
          }
          this.pos = lineEnd;
          if (this.pos < this.length && (this.source[this.pos] as unknown as string) === "\n") {
            contentChars.push("\n");
            textChars.push("\n");
            this.advance();
          }
          inHeredocBody = false;
          if (pendingHeredocs.length > 0) {
            {
              var Entry: any = pendingHeredocs[pendingHeredocs.length - 1];
              pendingHeredocs = pendingHeredocs.slice(0, pendingHeredocs.length - 1);
              currentHeredocDelim = Entry[0];
              currentHeredocStrip = Entry[1];
            }
            inHeredocBody = true;
          }
        } else {
          if (checkLine.startsWith(currentHeredocDelim) && checkLine.length > currentHeredocDelim.length) {
            var tabsStripped: any = line.length - checkLine.length;
            var endPos: any = tabsStripped + currentHeredocDelim.length;
            for (const i of range(endPos)) {
              contentChars.push((line[i] as unknown as string));
              textChars.push((line[i] as unknown as string));
            }
            this.pos = lineStart + endPos;
            inHeredocBody = false;
            if (pendingHeredocs.length > 0) {
              {
                var Entry: any = pendingHeredocs[pendingHeredocs.length - 1];
                pendingHeredocs = pendingHeredocs.slice(0, pendingHeredocs.length - 1);
                currentHeredocDelim = Entry[0];
                currentHeredocStrip = Entry[1];
              }
              inHeredocBody = true;
            }
          } else {
            for (const ch of line) {
              contentChars.push(ch);
              textChars.push(ch);
            }
            this.pos = lineEnd;
            if (this.pos < this.length && (this.source[this.pos] as unknown as string) === "\n") {
              contentChars.push("\n");
              textChars.push("\n");
              this.advance();
            }
          }
        }
        continue;
      }
      var c: any = this.peek();
      if (c === "\\" && this.pos + 1 < this.length) {
        var nextC: any = (this.source[this.pos + 1] as unknown as string);
        if (nextC === "\n") {
          this.advance();
          this.advance();
        } else {
          if (IsEscapeCharInBacktick(nextC)) {
            this.advance();
            var escaped: any = this.advance();
            contentChars.push(escaped);
            textChars.push("\\");
            textChars.push(escaped);
          } else {
            var ch: any = this.advance();
            contentChars.push(ch);
            textChars.push(ch);
          }
        }
        continue;
      }
      if (c === "<" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "<") {
        if (this.pos + 2 < this.length && (this.source[this.pos + 2] as unknown as string) === "<") {
          contentChars.push(this.advance());
          textChars.push("<");
          contentChars.push(this.advance());
          textChars.push("<");
          contentChars.push(this.advance());
          textChars.push("<");
          while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
            var ch: any = this.advance();
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
                var quote: any = this.peek();
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
        var stripTabs: any = false;
        if (!this.atEnd() && this.peek() === "-") {
          stripTabs = true;
          contentChars.push(this.advance());
          textChars.push("-");
        }
        while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
          var ch: any = this.advance();
          contentChars.push(ch);
          textChars.push(ch);
        }
        var delimiterChars: any = [];
        if (!this.atEnd()) {
          ch = this.peek();
          if (IsQuote(ch)) {
            var quote: any = this.advance();
            contentChars.push(quote);
            textChars.push(quote);
            while (!this.atEnd() && this.peek() !== quote) {
              var dch: any = this.advance();
              contentChars.push(dch);
              textChars.push(dch);
              delimiterChars.push(dch);
            }
            if (!this.atEnd()) {
              var closing: any = this.advance();
              contentChars.push(closing);
              textChars.push(closing);
            }
          } else {
            if (ch === "\\") {
              var esc: any = this.advance();
              contentChars.push(esc);
              textChars.push(esc);
              if (!this.atEnd()) {
                var dch: any = this.advance();
                contentChars.push(dch);
                textChars.push(dch);
                delimiterChars.push(dch);
              }
              while (!this.atEnd() && !IsMetachar(this.peek())) {
                var dch: any = this.advance();
                contentChars.push(dch);
                textChars.push(dch);
                delimiterChars.push(dch);
              }
            } else {
              while (!this.atEnd() && !IsMetachar(this.peek()) && this.peek() !== "`") {
                ch = this.peek();
                if (IsQuote(ch)) {
                  var quote: any = this.advance();
                  contentChars.push(quote);
                  textChars.push(quote);
                  while (!this.atEnd() && this.peek() !== quote) {
                    var dch: any = this.advance();
                    contentChars.push(dch);
                    textChars.push(dch);
                    delimiterChars.push(dch);
                  }
                  if (!this.atEnd()) {
                    var closing: any = this.advance();
                    contentChars.push(closing);
                    textChars.push(closing);
                  }
                } else {
                  if (ch === "\\") {
                    var esc: any = this.advance();
                    contentChars.push(esc);
                    textChars.push(esc);
                    if (!this.atEnd()) {
                      var dch: any = this.advance();
                      contentChars.push(dch);
                      textChars.push(dch);
                      delimiterChars.push(dch);
                    }
                  } else {
                    var dch: any = this.advance();
                    contentChars.push(dch);
                    textChars.push(dch);
                    delimiterChars.push(dch);
                  }
                }
              }
            }
          }
        }
        var delimiter: any = delimiterChars.join("");
        if (delimiter !== "") {
          pendingHeredocs.push([delimiter, stripTabs]);
        }
        continue;
      }
      if (c === "\n") {
        var ch: any = this.advance();
        contentChars.push(ch);
        textChars.push(ch);
        if (pendingHeredocs.length > 0) {
          {
            var Entry: any = pendingHeredocs[pendingHeredocs.length - 1];
            pendingHeredocs = pendingHeredocs.slice(0, pendingHeredocs.length - 1);
            currentHeredocDelim = Entry[0];
            currentHeredocStrip = Entry[1];
          }
          inHeredocBody = true;
        }
        continue;
      }
      var ch: any = this.advance();
      contentChars.push(ch);
      textChars.push(ch);
    }
    if (this.atEnd()) {
      throw new Error(`${"Unterminated backtick"} at position ${start}`)
    }
    this.advance();
    textChars.push("`");
    var text: any = textChars.join("");
    var content: any = contentChars.join("");
    if (pendingHeredocs.length > 0) {
      var [heredocStart, heredocEnd]: any = FindHeredocContentEnd(this.source, this.pos, pendingHeredocs);
      if (heredocEnd > heredocStart) {
        content = content + Substring(this.source, heredocStart, heredocEnd);
        if (this.CmdsubHeredocEnd === -1) {
          this.CmdsubHeredocEnd = heredocEnd;
        } else {
          this.CmdsubHeredocEnd = this.CmdsubHeredocEnd > heredocEnd ? this.CmdsubHeredocEnd : heredocEnd;
        }
      }
    }
    var subParser: any = newParser(content, false, this.Extglob);
    var cmd: any = subParser.parseList(true);
    if (cmd === null) {
      cmd = new Empty("empty" as any);
    }
    return [new CommandSubstitution(cmd as any, "cmdsub" as any), text];
  }

  ParseProcessSubstitution(): [Node, string] {
    if (this.atEnd() || !IsRedirectChar(this.peek())) {
      return [null, ""];
    }
    var start: any = this.pos;
    var direction: any = this.advance();
    if (this.atEnd() || this.peek() !== "(") {
      this.pos = start;
      return [null, ""];
    }
    this.advance();
    var saved: any = this.SaveParserState();
    var oldInProcessSub: any = this.InProcessSub;
    this.InProcessSub = true;
    this.SetState(ParserStateFlags_PST_EOFTOKEN);
    this.EofToken = ")";
    try {
      var cmd: any = this.parseList(true);
      if (cmd === null) {
        cmd = new Empty("empty" as any);
      }
      this.skipWhitespaceAndNewlines();
      if (this.atEnd() || this.peek() !== ")") {
        throw new Error(`${"Invalid process substitution"} at position ${start}`)
      }
      this.advance();
      var textEnd: any = this.pos;
      var text: any = Substring(this.source, start, textEnd);
      text = StripLineContinuationsCommentAware(text);
      this.RestoreParserState(saved);
      this.InProcessSub = oldInProcessSub;
      return [new ProcessSubstitution(direction as any, cmd as any, "procsub" as any), text];
    } catch (e) {
      this.RestoreParserState(saved);
      this.InProcessSub = oldInProcessSub;
      var contentStartChar: any = start + 2 < this.length ? (this.source[start + 2] as unknown as string) : "";
      if (" \t\n".includes(contentStartChar)) {
        throw new Error(`${""} at position ${0}`)
      }
      this.pos = start + 2;
      this.Lexer.pos = this.pos;
      this.Lexer.ParseMatchedPair("(", ")", 0, false);
      this.pos = this.Lexer.pos;
      var text: any = Substring(this.source, start, this.pos);
      text = StripLineContinuationsCommentAware(text);
      return [null, text];
    }
  }

  ParseArrayLiteral(): [Node, string] {
    if (this.atEnd() || this.peek() !== "(") {
      return [null, ""];
    }
    var start: any = this.pos;
    this.advance();
    this.SetState(ParserStateFlags_PST_COMPASSIGN);
    var elements: any = [];
    while (true) {
      this.skipWhitespaceAndNewlines();
      if (this.atEnd()) {
        this.ClearState(ParserStateFlags_PST_COMPASSIGN);
        throw new Error(`${"Unterminated array literal"} at position ${start}`)
      }
      if (this.peek() === ")") {
        break;
      }
      var word: any = this.parseWord(false, true, false);
      if (word === null) {
        if (this.peek() === ")") {
          break;
        }
        this.ClearState(ParserStateFlags_PST_COMPASSIGN);
        throw new Error(`${"Expected word in array literal"} at position ${this.pos}`)
      }
      elements.push(word);
    }
    if (this.atEnd() || this.peek() !== ")") {
      this.ClearState(ParserStateFlags_PST_COMPASSIGN);
      throw new Error(`${"Expected ) to close array literal"} at position ${this.pos}`)
    }
    this.advance();
    var text: any = Substring(this.source, start, this.pos);
    this.ClearState(ParserStateFlags_PST_COMPASSIGN);
    return [new ArrayName(elements as any, "array" as any), text];
  }

  ParseArithmeticExpansion(): [Node, string] {
    if (this.atEnd() || this.peek() !== "$") {
      return [null, ""];
    }
    var start: any = this.pos;
    if (this.pos + 2 >= this.length || (this.source[this.pos + 1] as unknown as string) !== "(" || (this.source[this.pos + 2] as unknown as string) !== "(") {
      return [null, ""];
    }
    this.advance();
    this.advance();
    this.advance();
    var contentStart: any = this.pos;
    var depth: any = 2;
    var firstClosePos: any = -1;
    while (!this.atEnd() && depth > 0) {
      var c: any = this.peek();
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
        throw new Error(`${"unexpected EOF looking for `))'"} at position ${start}`)
      }
      this.pos = start;
      return [null, ""];
    }
    if (firstClosePos !== -1) {
      var content: any = Substring(this.source, contentStart, firstClosePos);
    } else {
      var content: any = Substring(this.source, contentStart, this.pos);
    }
    this.advance();
    var text: any = Substring(this.source, start, this.pos);
    try {
      var expr: any = this.ParseArithExpr(content);
    } catch (_e) {
      this.pos = start;
      return [null, ""];
    }
    return [new ArithmeticExpansion(expr as any, "arith" as any), text];
  }

  ParseArithExpr(content: string): Node {
    var savedArithSrc: any = this.ArithSrc;
    var savedArithPos: any = this.ArithPos;
    var savedArithLen: any = this.ArithLen;
    var savedParserState: any = this.ParserState;
    this.SetState(ParserStateFlags_PST_ARITH);
    this.ArithSrc = content;
    this.ArithPos = 0;
    this.ArithLen = content.length;
    this.ArithSkipWs();
    if (this.ArithAtEnd()) {
      var result: any = null;
    } else {
      var result: any = this.ArithParseComma();
    }
    this.ParserState = savedParserState;
    if (savedArithSrc !== "") {
      this.ArithSrc = savedArithSrc;
      this.ArithPos = savedArithPos;
      this.ArithLen = savedArithLen;
    }
    return result;
  }

  ArithAtEnd(): boolean {
    return this.ArithPos >= this.ArithLen;
  }

  ArithPeek(offset: number): string {
    var pos: any = this.ArithPos + offset;
    if (pos >= this.ArithLen) {
      return "";
    }
    return (this.ArithSrc[pos] as unknown as string);
  }

  ArithAdvance(): string {
    if (this.ArithAtEnd()) {
      return "";
    }
    var c: any = (this.ArithSrc[this.ArithPos] as unknown as string);
    this.ArithPos += 1;
    return c;
  }

  ArithSkipWs(): void {
    while (!this.ArithAtEnd()) {
      var c: any = (this.ArithSrc[this.ArithPos] as unknown as string);
      if (IsWhitespace(c)) {
        this.ArithPos += 1;
      } else {
        if (c === "\\" && this.ArithPos + 1 < this.ArithLen && (this.ArithSrc[this.ArithPos + 1] as unknown as string) === "\n") {
          this.ArithPos += 2;
        } else {
          break;
        }
      }
    }
  }

  ArithMatch(s: string): boolean {
    return StartsWithAt(this.ArithSrc, this.ArithPos, s);
  }

  ArithConsume(s: string): boolean {
    if (this.ArithMatch(s)) {
      this.ArithPos += s.length;
      return true;
    }
    return false;
  }

  ArithParseComma(): Node {
    var left: any = this.ArithParseAssign();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithConsume(",")) {
        this.ArithSkipWs();
        var right: any = this.ArithParseAssign();
        left = new ArithComma(left as any, right as any, "comma" as any);
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseAssign(): Node {
    var left: any = this.ArithParseTernary();
    this.ArithSkipWs();
    var assignOps: any = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="];
    for (const op of assignOps) {
      if (this.ArithMatch(op)) {
        if (op === "=" && this.ArithPeek(1) === "=") {
          break;
        }
        this.ArithConsume(op);
        this.ArithSkipWs();
        var right: any = this.ArithParseAssign();
        return new ArithAssign(op as any, left as any, right as any, "assign" as any);
      }
    }
    return left;
  }

  ArithParseTernary(): Node {
    var cond: any = this.ArithParseLogicalOr();
    this.ArithSkipWs();
    if (this.ArithConsume("?")) {
      this.ArithSkipWs();
      if (this.ArithMatch(":")) {
        var ifTrue: any = null;
      } else {
        var ifTrue: any = this.ArithParseAssign();
      }
      this.ArithSkipWs();
      if (this.ArithConsume(":")) {
        this.ArithSkipWs();
        if (this.ArithAtEnd() || this.ArithPeek(0) === ")") {
          var ifFalse: any = null;
        } else {
          var ifFalse: any = this.ArithParseTernary();
        }
      } else {
        var ifFalse: any = null;
      }
      return new ArithTernary(cond as any, ifTrue as any, ifFalse as any, "ternary" as any);
    }
    return cond;
  }

  ArithParseLeftAssoc(ops: string[], parsefn: (() => Node)): Node {
    var left: any = parsefn();
    while (true) {
      this.ArithSkipWs();
      var matched: any = false;
      for (const op of ops) {
        if (this.ArithMatch(op)) {
          this.ArithConsume(op);
          this.ArithSkipWs();
          left = new ArithBinaryOp(op as any, left as any, parsefn() as any, "binary-op" as any);
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

  ArithParseLogicalOr(): Node {
    return this.ArithParseLeftAssoc(["||"], this.ArithParseLogicalAnd);
  }

  ArithParseLogicalAnd(): Node {
    return this.ArithParseLeftAssoc(["&&"], this.ArithParseBitwiseOr);
  }

  ArithParseBitwiseOr(): Node {
    var left: any = this.ArithParseBitwiseXor();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithPeek(0) === "|" && (this.ArithPeek(1) !== "|" && this.ArithPeek(1) !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right: any = this.ArithParseBitwiseXor();
        left = new ArithBinaryOp("|" as any, left as any, right as any, "binary-op" as any);
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseBitwiseXor(): Node {
    var left: any = this.ArithParseBitwiseAnd();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithPeek(0) === "^" && this.ArithPeek(1) !== "=") {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right: any = this.ArithParseBitwiseAnd();
        left = new ArithBinaryOp("^" as any, left as any, right as any, "binary-op" as any);
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseBitwiseAnd(): Node {
    var left: any = this.ArithParseEquality();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithPeek(0) === "&" && (this.ArithPeek(1) !== "&" && this.ArithPeek(1) !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right: any = this.ArithParseEquality();
        left = new ArithBinaryOp("&" as any, left as any, right as any, "binary-op" as any);
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseEquality(): Node {
    return this.ArithParseLeftAssoc(["==", "!="], this.ArithParseComparison);
  }

  ArithParseComparison(): Node {
    var left: any = this.ArithParseShift();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithMatch("<=")) {
        this.ArithConsume("<=");
        this.ArithSkipWs();
        var right: any = this.ArithParseShift();
        left = new ArithBinaryOp("<=" as any, left as any, right as any, "binary-op" as any);
      } else {
        if (this.ArithMatch(">=")) {
          this.ArithConsume(">=");
          this.ArithSkipWs();
          var right: any = this.ArithParseShift();
          left = new ArithBinaryOp(">=" as any, left as any, right as any, "binary-op" as any);
        } else {
          if (this.ArithPeek(0) === "<" && (this.ArithPeek(1) !== "<" && this.ArithPeek(1) !== "=")) {
            this.ArithAdvance();
            this.ArithSkipWs();
            var right: any = this.ArithParseShift();
            left = new ArithBinaryOp("<" as any, left as any, right as any, "binary-op" as any);
          } else {
            if (this.ArithPeek(0) === ">" && (this.ArithPeek(1) !== ">" && this.ArithPeek(1) !== "=")) {
              this.ArithAdvance();
              this.ArithSkipWs();
              var right: any = this.ArithParseShift();
              left = new ArithBinaryOp(">" as any, left as any, right as any, "binary-op" as any);
            } else {
              break;
            }
          }
        }
      }
    }
    return left;
  }

  ArithParseShift(): Node {
    var left: any = this.ArithParseAdditive();
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
        var right: any = this.ArithParseAdditive();
        left = new ArithBinaryOp("<<" as any, left as any, right as any, "binary-op" as any);
      } else {
        if (this.ArithMatch(">>")) {
          this.ArithConsume(">>");
          this.ArithSkipWs();
          var right: any = this.ArithParseAdditive();
          left = new ArithBinaryOp(">>" as any, left as any, right as any, "binary-op" as any);
        } else {
          break;
        }
      }
    }
    return left;
  }

  ArithParseAdditive(): Node {
    var left: any = this.ArithParseMultiplicative();
    while (true) {
      this.ArithSkipWs();
      var c: any = this.ArithPeek(0);
      var c2: any = this.ArithPeek(1);
      if (c === "+" && (c2 !== "+" && c2 !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right: any = this.ArithParseMultiplicative();
        left = new ArithBinaryOp("+" as any, left as any, right as any, "binary-op" as any);
      } else {
        if (c === "-" && (c2 !== "-" && c2 !== "=")) {
          this.ArithAdvance();
          this.ArithSkipWs();
          var right: any = this.ArithParseMultiplicative();
          left = new ArithBinaryOp("-" as any, left as any, right as any, "binary-op" as any);
        } else {
          break;
        }
      }
    }
    return left;
  }

  ArithParseMultiplicative(): Node {
    var left: any = this.ArithParseExponentiation();
    while (true) {
      this.ArithSkipWs();
      var c: any = this.ArithPeek(0);
      var c2: any = this.ArithPeek(1);
      if (c === "*" && (c2 !== "*" && c2 !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right: any = this.ArithParseExponentiation();
        left = new ArithBinaryOp("*" as any, left as any, right as any, "binary-op" as any);
      } else {
        if (c === "/" && c2 !== "=") {
          this.ArithAdvance();
          this.ArithSkipWs();
          var right: any = this.ArithParseExponentiation();
          left = new ArithBinaryOp("/" as any, left as any, right as any, "binary-op" as any);
        } else {
          if (c === "%" && c2 !== "=") {
            this.ArithAdvance();
            this.ArithSkipWs();
            var right: any = this.ArithParseExponentiation();
            left = new ArithBinaryOp("%" as any, left as any, right as any, "binary-op" as any);
          } else {
            break;
          }
        }
      }
    }
    return left;
  }

  ArithParseExponentiation(): Node {
    var left: any = this.ArithParseUnary();
    this.ArithSkipWs();
    if (this.ArithMatch("**")) {
      this.ArithConsume("**");
      this.ArithSkipWs();
      var right: any = this.ArithParseExponentiation();
      return new ArithBinaryOp("**" as any, left as any, right as any, "binary-op" as any);
    }
    return left;
  }

  ArithParseUnary(): Node {
    this.ArithSkipWs();
    if (this.ArithMatch("++")) {
      this.ArithConsume("++");
      this.ArithSkipWs();
      var operand: any = this.ArithParseUnary();
      return new ArithPreIncr(operand as any, "pre-incr" as any);
    }
    if (this.ArithMatch("--")) {
      this.ArithConsume("--");
      this.ArithSkipWs();
      var operand: any = this.ArithParseUnary();
      return new ArithPreDecr(operand as any, "pre-decr" as any);
    }
    var c: any = this.ArithPeek(0);
    if (c === "!") {
      this.ArithAdvance();
      this.ArithSkipWs();
      var operand: any = this.ArithParseUnary();
      return new ArithUnaryOp("!" as any, operand as any, "unary-op" as any);
    }
    if (c === "~") {
      this.ArithAdvance();
      this.ArithSkipWs();
      var operand: any = this.ArithParseUnary();
      return new ArithUnaryOp("~" as any, operand as any, "unary-op" as any);
    }
    if (c === "+" && this.ArithPeek(1) !== "+") {
      this.ArithAdvance();
      this.ArithSkipWs();
      var operand: any = this.ArithParseUnary();
      return new ArithUnaryOp("+" as any, operand as any, "unary-op" as any);
    }
    if (c === "-" && this.ArithPeek(1) !== "-") {
      this.ArithAdvance();
      this.ArithSkipWs();
      var operand: any = this.ArithParseUnary();
      return new ArithUnaryOp("-" as any, operand as any, "unary-op" as any);
    }
    return this.ArithParsePostfix();
  }

  ArithParsePostfix(): Node {
    var left: any = this.ArithParsePrimary();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithMatch("++")) {
        this.ArithConsume("++");
        left = new ArithPostIncr(left as any, "post-incr" as any);
      } else {
        if (this.ArithMatch("--")) {
          this.ArithConsume("--");
          left = new ArithPostDecr(left as any, "post-decr" as any);
        } else {
          if (this.ArithPeek(0) === "[") {
            if (left instanceof ArithVar) {
              this.ArithAdvance();
              this.ArithSkipWs();
              var index: any = this.ArithParseComma();
              this.ArithSkipWs();
              if (!this.ArithConsume("]")) {
                throw new Error(`${"Expected ']' in array subscript"} at position ${this.ArithPos}`)
              }
              left = new ArithSubscript(left.name as any, index as any, "subscript" as any);
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

  ArithParsePrimary(): Node {
    this.ArithSkipWs();
    var c: any = this.ArithPeek(0);
    if (c === "(") {
      this.ArithAdvance();
      this.ArithSkipWs();
      var expr: any = this.ArithParseComma();
      this.ArithSkipWs();
      if (!this.ArithConsume(")")) {
        throw new Error(`${"Expected ')' in arithmetic expression"} at position ${this.ArithPos}`)
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
        throw new Error(`${"Unexpected end after backslash in arithmetic"} at position ${this.ArithPos}`)
      }
      var escapedChar: any = this.ArithAdvance();
      return new ArithEscape(escapedChar as any, "escape" as any);
    }
    if (this.ArithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".includes(c)) {
      return new ArithEmpty("empty" as any);
    }
    return this.ArithParseNumberOrVar();
  }

  ArithParseExpansion(): Node {
    if (!this.ArithConsume("$")) {
      throw new Error(`${"Expected '$'"} at position ${this.ArithPos}`)
    }
    var c: any = this.ArithPeek(0);
    if (c === "(") {
      return this.ArithParseCmdsub();
    }
    if (c === "{") {
      return this.ArithParseBracedParam();
    }
    var nameChars: any = [];
    while (!this.ArithAtEnd()) {
      var ch: any = this.ArithPeek(0);
      if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
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
      throw new Error(`${"Expected variable name after $"} at position ${this.ArithPos}`)
    }
    return new ParamExpansion(nameChars.join("") as any, "param" as any);
  }

  ArithParseCmdsub(): Node {
    this.ArithAdvance();
    if (this.ArithPeek(0) === "(") {
      this.ArithAdvance();
      var depth: any = 1;
      var contentStart: any = this.ArithPos;
      while (!this.ArithAtEnd() && depth > 0) {
        var ch: any = this.ArithPeek(0);
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
      var content: any = Substring(this.ArithSrc, contentStart, this.ArithPos);
      this.ArithAdvance();
      this.ArithAdvance();
      var innerExpr: any = this.ParseArithExpr(content);
      return new ArithmeticExpansion(innerExpr as any, "arith" as any);
    }
    var depth: any = 1;
    var contentStart: any = this.ArithPos;
    while (!this.ArithAtEnd() && depth > 0) {
      var ch: any = this.ArithPeek(0);
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
    var content: any = Substring(this.ArithSrc, contentStart, this.ArithPos);
    this.ArithAdvance();
    var subParser: any = newParser(content, false, this.Extglob);
    var cmd: any = subParser.parseList(true);
    return new CommandSubstitution(cmd as any, "cmdsub" as any);
  }

  ArithParseBracedParam(): Node {
    this.ArithAdvance();
    if (this.ArithPeek(0) === "!") {
      this.ArithAdvance();
      var nameChars: any = [];
      while (!this.ArithAtEnd() && this.ArithPeek(0) !== "}") {
        nameChars.push(this.ArithAdvance());
      }
      this.ArithConsume("}");
      return new ParamIndirect(nameChars.join("") as any, "param-indirect" as any);
    }
    if (this.ArithPeek(0) === "#") {
      this.ArithAdvance();
      var nameChars: any = [];
      while (!this.ArithAtEnd() && this.ArithPeek(0) !== "}") {
        nameChars.push(this.ArithAdvance());
      }
      this.ArithConsume("}");
      return new ParamLength(nameChars.join("") as any, "param-len" as any);
    }
    var nameChars: any = [];
    while (!this.ArithAtEnd()) {
      var ch: any = this.ArithPeek(0);
      if (ch === "}") {
        this.ArithAdvance();
        return new ParamExpansion(nameChars.join("") as any, "param" as any);
      }
      if (IsParamExpansionOp(ch)) {
        break;
      }
      nameChars.push(this.ArithAdvance());
    }
    var name: any = nameChars.join("");
    var opChars: any = [];
    var depth: any = 1;
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
    var opStr: any = opChars.join("");
    if (opStr.startsWith(":-")) {
      return new ParamExpansion(name as any, ":-" as any, Substring(opStr, 2, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith(":=")) {
      return new ParamExpansion(name as any, ":=" as any, Substring(opStr, 2, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith(":+")) {
      return new ParamExpansion(name as any, ":+" as any, Substring(opStr, 2, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith(":?")) {
      return new ParamExpansion(name as any, ":?" as any, Substring(opStr, 2, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith(":")) {
      return new ParamExpansion(name as any, ":" as any, Substring(opStr, 1, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith("##")) {
      return new ParamExpansion(name as any, "##" as any, Substring(opStr, 2, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith("#")) {
      return new ParamExpansion(name as any, "#" as any, Substring(opStr, 1, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith("%%")) {
      return new ParamExpansion(name as any, "%%" as any, Substring(opStr, 2, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith("%")) {
      return new ParamExpansion(name as any, "%" as any, Substring(opStr, 1, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith("//")) {
      return new ParamExpansion(name as any, "//" as any, Substring(opStr, 2, opStr.length) as any, "param" as any);
    }
    if (opStr.startsWith("/")) {
      return new ParamExpansion(name as any, "/" as any, Substring(opStr, 1, opStr.length) as any, "param" as any);
    }
    return new ParamExpansion(name as any, "" as any, opStr as any, "param" as any);
  }

  ArithParseSingleQuote(): Node {
    this.ArithAdvance();
    var contentStart: any = this.ArithPos;
    while (!this.ArithAtEnd() && this.ArithPeek(0) !== "'") {
      this.ArithAdvance();
    }
    var content: any = Substring(this.ArithSrc, contentStart, this.ArithPos);
    if (!this.ArithConsume("'")) {
      throw new Error(`${"Unterminated single quote in arithmetic"} at position ${this.ArithPos}`)
    }
    return new ArithNumber(content as any, "number" as any);
  }

  ArithParseDoubleQuote(): Node {
    this.ArithAdvance();
    var contentStart: any = this.ArithPos;
    while (!this.ArithAtEnd() && this.ArithPeek(0) !== "\"") {
      var c: any = this.ArithPeek(0);
      if (c === "\\" && !this.ArithAtEnd()) {
        this.ArithAdvance();
        this.ArithAdvance();
      } else {
        this.ArithAdvance();
      }
    }
    var content: any = Substring(this.ArithSrc, contentStart, this.ArithPos);
    if (!this.ArithConsume("\"")) {
      throw new Error(`${"Unterminated double quote in arithmetic"} at position ${this.ArithPos}`)
    }
    return new ArithNumber(content as any, "number" as any);
  }

  ArithParseBacktick(): Node {
    this.ArithAdvance();
    var contentStart: any = this.ArithPos;
    while (!this.ArithAtEnd() && this.ArithPeek(0) !== "`") {
      var c: any = this.ArithPeek(0);
      if (c === "\\" && !this.ArithAtEnd()) {
        this.ArithAdvance();
        this.ArithAdvance();
      } else {
        this.ArithAdvance();
      }
    }
    var content: any = Substring(this.ArithSrc, contentStart, this.ArithPos);
    if (!this.ArithConsume("`")) {
      throw new Error(`${"Unterminated backtick in arithmetic"} at position ${this.ArithPos}`)
    }
    var subParser: any = newParser(content, false, this.Extglob);
    var cmd: any = subParser.parseList(true);
    return new CommandSubstitution(cmd as any, "cmdsub" as any);
  }

  ArithParseNumberOrVar(): Node {
    this.ArithSkipWs();
    var chars: any = [];
    var c: any = this.ArithPeek(0);
    if (/^[0-9]$/.test(c)) {
      while (!this.ArithAtEnd()) {
        var ch: any = this.ArithPeek(0);
        if (/^[a-zA-Z0-9]$/.test(ch) || (ch === "#" || ch === "_")) {
          chars.push(this.ArithAdvance());
        } else {
          break;
        }
      }
      var prefix: any = chars.join("");
      if (!this.ArithAtEnd() && this.ArithPeek(0) === "$") {
        var expansion: any = this.ArithParseExpansion();
        return new ArithConcat([new ArithNumber(prefix as any, "number" as any), expansion] as any, "arith-concat" as any);
      }
      return new ArithNumber(prefix as any, "number" as any);
    }
    if (/^[a-zA-Z]$/.test(c) || c === "_") {
      while (!this.ArithAtEnd()) {
        var ch: any = this.ArithPeek(0);
        if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
          chars.push(this.ArithAdvance());
        } else {
          break;
        }
      }
      return new ArithVar(chars.join("") as any, "var" as any);
    }
    throw new Error(`${"Unexpected character '" + c + "' in arithmetic expression"} at position ${this.ArithPos}`)
  }

  ParseDeprecatedArithmetic(): [Node, string] {
    if (this.atEnd() || this.peek() !== "$") {
      return [null, ""];
    }
    var start: any = this.pos;
    if (this.pos + 1 >= this.length || (this.source[this.pos + 1] as unknown as string) !== "[") {
      return [null, ""];
    }
    this.advance();
    this.advance();
    this.Lexer.pos = this.pos;
    var content: any = this.Lexer.ParseMatchedPair("[", "]", MatchedPairFlags_ARITH, false);
    this.pos = this.Lexer.pos;
    var text: any = Substring(this.source, start, this.pos);
    return [new ArithDeprecated(content as any, "arith-deprecated" as any), text];
  }

  ParseParamExpansion(inDquote: boolean): [Node, string] {
    this.SyncLexer();
    var [result0, result1]: any = this.Lexer.ReadParamExpansion(inDquote);
    this.SyncParser();
    return [result0, result1];
  }

  parseRedirect(): Node {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    var start: any = this.pos;
    var fd: any = -1;
    var varfd: any = "";
    if (this.peek() === "{") {
      var saved: any = this.pos;
      this.advance();
      var varnameChars: any = [];
      var inBracket: any = false;
      while (!this.atEnd() && !IsRedirectChar(this.peek())) {
        var ch: any = this.peek();
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
              if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
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
      var varname: any = varnameChars.join("");
      var isValidVarfd: any = false;
      if (varname !== "") {
        if (/^[a-zA-Z]$/.test((varname[0] as unknown as string)) || (varname[0] as unknown as string) === "_") {
          if (varname.includes("[") || varname.includes("]")) {
            var left: any = varname.indexOf("[");
            var right: any = varname.lastIndexOf("]");
            if (left !== -1 && right === varname.length - 1 && right > left + 1) {
              var base: any = varname.slice(0, left);
              if (base !== "" && (/^[a-zA-Z]$/.test((base[0] as unknown as string)) || (base[0] as unknown as string) === "_")) {
                isValidVarfd = true;
                for (const c of base.slice(1)) {
                  if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
                    isValidVarfd = false;
                    break;
                  }
                }
              }
            }
          } else {
            isValidVarfd = true;
            for (const c of varname.slice(1)) {
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
      } else {
        this.pos = saved;
      }
    }
    if (varfd === "" && this.peek() !== "" && /^[0-9]$/.test(this.peek())) {
      var fdChars: any = [];
      while (!this.atEnd() && /^[0-9]$/.test(this.peek())) {
        fdChars.push(this.advance());
      }
      fd = parseInt(fdChars.join(""), 10);
    }
    var ch: any = this.peek();
    if (ch === "&" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === ">") {
      if (fd !== -1 || varfd !== "") {
        this.pos = start;
        return null;
      }
      this.advance();
      this.advance();
      if (!this.atEnd() && this.peek() === ">") {
        this.advance();
        var op: any = "&>>";
      } else {
        var op: any = "&>";
      }
      this.skipWhitespace();
      var target: any = this.parseWord(false, false, false);
      if (target === null) {
        throw new Error(`${"Expected target for redirect " + op} at position ${this.pos}`)
      }
      return new Redirect(op as any, target as any, "redirect" as any);
    }
    if (ch === "" || !IsRedirectChar(ch)) {
      this.pos = start;
      return null;
    }
    if (fd === -1 && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
      this.pos = start;
      return null;
    }
    var op: any = this.advance();
    var stripTabs: any = false;
    if (!this.atEnd()) {
      var nextCh: any = this.peek();
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
                if (this.pos + 1 >= this.length || !IsDigitOrDash((this.source[this.pos + 1] as unknown as string))) {
                  this.advance();
                  op = ">&";
                }
              } else {
                if (fd === -1 && varfd === "" && op === "<" && nextCh === "&") {
                  if (this.pos + 1 >= this.length || !IsDigitOrDash((this.source[this.pos + 1] as unknown as string))) {
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
        if (this.pos + 1 < this.length && !IsMetachar((this.source[this.pos + 1] as unknown as string))) {
          this.advance();
          var target: any = new Word("&-" as any, "word" as any);
        } else {
          var target: any = null;
        }
      } else {
        var target: any = null;
      }
      if (target === null) {
        if (!this.atEnd() && (/^[0-9]$/.test(this.peek()) || this.peek() === "-")) {
          var wordStart: any = this.pos;
          var fdChars: any = [];
          while (!this.atEnd() && /^[0-9]$/.test(this.peek())) {
            fdChars.push(this.advance());
          }
          if (fdChars.length > 0) {
            var fdTarget: any = fdChars.join("");
          } else {
            var fdTarget: any = "";
          }
          if (!this.atEnd() && this.peek() === "-") {
            fdTarget += this.advance();
          }
          if (fdTarget !== "-" && !this.atEnd() && !IsMetachar(this.peek())) {
            this.pos = wordStart;
            var innerWord: any = this.parseWord(false, false, false);
            if (innerWord !== null) {
              var target: any = new Word("&" + innerWord.value as any, "word" as any);
              target.parts = innerWord.parts;
            } else {
              throw new Error(`${"Expected target for redirect " + op} at position ${this.pos}`)
            }
          } else {
            var target: any = new Word("&" + fdTarget as any, "word" as any);
          }
        } else {
          var innerWord: any = this.parseWord(false, false, false);
          if (innerWord !== null) {
            var target: any = new Word("&" + innerWord.value as any, "word" as any);
            target.parts = innerWord.parts;
          } else {
            throw new Error(`${"Expected target for redirect " + op} at position ${this.pos}`)
          }
        }
      }
    } else {
      this.skipWhitespace();
      if ((op === ">&" || op === "<&") && !this.atEnd() && this.peek() === "-") {
        if (this.pos + 1 < this.length && !IsMetachar((this.source[this.pos + 1] as unknown as string))) {
          this.advance();
          var target: any = new Word("&-" as any, "word" as any);
        } else {
          var target: any = this.parseWord(false, false, false);
        }
      } else {
        var target: any = this.parseWord(false, false, false);
      }
    }
    if (target === null) {
      throw new Error(`${"Expected target for redirect " + op} at position ${this.pos}`)
    }
    return new Redirect(op as any, target as any, "redirect" as any);
  }

  ParseHeredocDelimiter(): [string, boolean] {
    this.skipWhitespace();
    var quoted: any = false;
    var delimiterChars: any = [];
    while (true) {
      while (!this.atEnd() && !IsMetachar(this.peek())) {
        var ch: any = this.peek();
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
              var c: any = this.advance();
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
                var nextCh: any = this.peek();
                if (nextCh === "\n") {
                  this.advance();
                } else {
                  quoted = true;
                  delimiterChars.push(this.advance());
                }
              }
            } else {
              if (ch === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "'") {
                quoted = true;
                this.advance();
                this.advance();
                while (!this.atEnd() && this.peek() !== "'") {
                  var c: any = this.peek();
                  if (c === "\\" && this.pos + 1 < this.length) {
                    this.advance();
                    var esc: any = this.peek();
                    var escVal: any = GetAnsiEscape(esc);
                    if (escVal >= 0) {
                      delimiterChars.push((escVal as unknown as string));
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
                  var depth: any = 1;
                  while (!this.atEnd() && depth > 0) {
                    var c: any = this.peek();
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
                  if (ch === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "{") {
                    var dollarCount: any = 0;
                    var j: any = this.pos - 1;
                    while (j >= 0 && (this.source[j] as unknown as string) === "$") {
                      dollarCount += 1;
                      j -= 1;
                    }
                    if (j >= 0 && (this.source[j] as unknown as string) === "\\") {
                      dollarCount -= 1;
                    }
                    if (dollarCount % 2 === 1) {
                      delimiterChars.push(this.advance());
                    } else {
                      delimiterChars.push(this.advance());
                      delimiterChars.push(this.advance());
                      var depth: any = 0;
                      while (!this.atEnd()) {
                        var c: any = this.peek();
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
                    if (ch === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "[") {
                      var dollarCount: any = 0;
                      var j: any = this.pos - 1;
                      while (j >= 0 && (this.source[j] as unknown as string) === "$") {
                        dollarCount += 1;
                        j -= 1;
                      }
                      if (j >= 0 && (this.source[j] as unknown as string) === "\\") {
                        dollarCount -= 1;
                      }
                      if (dollarCount % 2 === 1) {
                        delimiterChars.push(this.advance());
                      } else {
                        delimiterChars.push(this.advance());
                        delimiterChars.push(this.advance());
                        var depth: any = 1;
                        while (!this.atEnd() && depth > 0) {
                          var c: any = this.peek();
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
                          var c: any = this.peek();
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
      if (!this.atEnd() && "<>".includes(this.peek()) && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
        delimiterChars.push(this.advance());
        delimiterChars.push(this.advance());
        var depth: any = 1;
        while (!this.atEnd() && depth > 0) {
          var c: any = this.peek();
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

  ReadHeredocLine(quoted: boolean): [string, number] {
    var lineStart: any = this.pos;
    var lineEnd: any = this.pos;
    while (lineEnd < this.length && (this.source[lineEnd] as unknown as string) !== "\n") {
      lineEnd += 1;
    }
    var line: any = Substring(this.source, lineStart, lineEnd);
    if (!quoted) {
      while (lineEnd < this.length) {
        var trailingBs: any = CountTrailingBackslashes(line);
        if (trailingBs % 2 === 0) {
          break;
        }
        line = Substring(line, 0, line.length - 1);
        lineEnd += 1;
        var nextLineStart: any = lineEnd;
        while (lineEnd < this.length && (this.source[lineEnd] as unknown as string) !== "\n") {
          lineEnd += 1;
        }
        line = line + Substring(this.source, nextLineStart, lineEnd);
      }
    }
    return [line, lineEnd];
  }

  LineMatchesDelimiter(line: string, delimiter: string, stripTabs: boolean): [boolean, string] {
    var checkLine: any = stripTabs ? line.replace(/^[\t]+/, '') : line;
    var normalizedCheck: any = NormalizeHeredocDelimiter(checkLine);
    var normalizedDelim: any = NormalizeHeredocDelimiter(delimiter);
    return [normalizedCheck === normalizedDelim, checkLine];
  }

  GatherHeredocBodies(): void {
    for (const heredoc of this.PendingHeredocs) {
      var contentLines: any = [];
      var lineStart: any = this.pos;
      while (this.pos < this.length) {
        lineStart = this.pos;
        var [line, lineEnd]: any = this.ReadHeredocLine(heredoc.quoted);
        var [matches, checkLine]: any = this.LineMatchesDelimiter(line, heredoc.delimiter, heredoc.stripTabs);
        if (matches) {
          this.pos = lineEnd < this.length ? lineEnd + 1 : lineEnd;
          break;
        }
        var normalizedCheck: any = NormalizeHeredocDelimiter(checkLine);
        var normalizedDelim: any = NormalizeHeredocDelimiter(heredoc.delimiter);
        if (this.EofToken === ")" && normalizedCheck.startsWith(normalizedDelim)) {
          var tabsStripped: any = line.length - checkLine.length;
          this.pos = lineStart + tabsStripped + heredoc.delimiter.length;
          break;
        }
        if (lineEnd >= this.length && normalizedCheck.startsWith(normalizedDelim) && this.InProcessSub) {
          var tabsStripped: any = line.length - checkLine.length;
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
          var addNewline: any = true;
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
  }

  ParseHeredoc(fd: number | null, stripTabs: boolean): HereDoc {
    var startPos: any = this.pos;
    this.SetState(ParserStateFlags_PST_HEREDOC);
    var [delimiter, quoted]: any = this.ParseHeredocDelimiter();
    for (const existing of this.PendingHeredocs) {
      if (existing.StartPos === startPos && existing.delimiter === delimiter) {
        this.ClearState(ParserStateFlags_PST_HEREDOC);
        return existing;
      }
    }
    var heredoc: any = new HereDoc(delimiter as any, "" as any, stripTabs as any, quoted as any, fd as any, false as any, "heredoc" as any);
    heredoc.StartPos = startPos;
    this.PendingHeredocs.push(heredoc);
    this.ClearState(ParserStateFlags_PST_HEREDOC);
    return heredoc;
  }

  parseCommand(): Command {
    var words: any = [];
    var redirects: any = [];
    while (true) {
      this.skipWhitespace();
      if (this.LexIsCommandTerminator()) {
        break;
      }
      if (words.length === 0) {
        var reserved: any = this.LexPeekReservedWord();
        if (reserved === "}" || reserved === "]]") {
          break;
        }
      }
      var redirect: any = this.parseRedirect();
      if (redirect !== null) {
        redirects.push(redirect);
        continue;
      }
      var allAssignments: any = true;
      for (const w of words) {
        if (!this.IsAssignmentWord(w)) {
          allAssignments = false;
          break;
        }
      }
      var inAssignBuiltin: any = words.length > 0 && ASSIGNMENT_BUILTINS.has(words[0].value);
      var word: any = this.parseWord(!(words.length > 0) || allAssignments && redirects.length === 0, false, inAssignBuiltin);
      if (word === null) {
        break;
      }
      words.push(word);
    }
    if (!(words.length > 0) && !(redirects.length > 0)) {
      return null;
    }
    return new Command(words as any, redirects as any, "command" as any);
  }

  parseSubshell(): Subshell {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== "(") {
      return null;
    }
    this.advance();
    this.SetState(ParserStateFlags_PST_SUBSHELL);
    var body: any = this.parseList(true);
    if (body === null) {
      this.ClearState(ParserStateFlags_PST_SUBSHELL);
      throw new Error(`${"Expected command in subshell"} at position ${this.pos}`)
    }
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== ")") {
      this.ClearState(ParserStateFlags_PST_SUBSHELL);
      throw new Error(`${"Expected ) to close subshell"} at position ${this.pos}`)
    }
    this.advance();
    this.ClearState(ParserStateFlags_PST_SUBSHELL);
    return new Subshell(body as any, this.CollectRedirects() as any, "subshell" as any);
  }

  parseArithmeticCommand(): ArithmeticCommand {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== "(" || this.pos + 1 >= this.length || (this.source[this.pos + 1] as unknown as string) !== "(") {
      return null;
    }
    var savedPos: any = this.pos;
    this.advance();
    this.advance();
    var contentStart: any = this.pos;
    var depth: any = 1;
    while (!this.atEnd() && depth > 0) {
      var c: any = this.peek();
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
                if (depth === 1 && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === ")") {
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
      throw new Error(`${"unexpected EOF looking for `))'"} at position ${savedPos}`)
    }
    if (depth !== 1) {
      this.pos = savedPos;
      return null;
    }
    var content: any = Substring(this.source, contentStart, this.pos);
    content = content.replace("\\\n", "");
    this.advance();
    this.advance();
    var expr: any = this.ParseArithExpr(content);
    return new ArithmeticCommand(expr as any, this.CollectRedirects() as any, content as any, "arith-cmd" as any);
  }

  parseConditionalExpr(): ConditionalExpr {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== "[" || this.pos + 1 >= this.length || (this.source[this.pos + 1] as unknown as string) !== "[") {
      return null;
    }
    var nextPos: any = this.pos + 2;
    if (nextPos < this.length && !(IsWhitespace((this.source[nextPos] as unknown as string)) || (this.source[nextPos] as unknown as string) === "\\" && nextPos + 1 < this.length && (this.source[nextPos + 1] as unknown as string) === "\n")) {
      return null;
    }
    this.advance();
    this.advance();
    this.SetState(ParserStateFlags_PST_CONDEXPR);
    this.WordContext = WORD_CTX_COND;
    var body: any = this.ParseCondOr();
    while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
      this.advance();
    }
    if (this.atEnd() || this.peek() !== "]" || this.pos + 1 >= this.length || (this.source[this.pos + 1] as unknown as string) !== "]") {
      this.ClearState(ParserStateFlags_PST_CONDEXPR);
      this.WordContext = WORD_CTX_NORMAL;
      throw new Error(`${"Expected ]] to close conditional expression"} at position ${this.pos}`)
    }
    this.advance();
    this.advance();
    this.ClearState(ParserStateFlags_PST_CONDEXPR);
    this.WordContext = WORD_CTX_NORMAL;
    return new ConditionalExpr(body as any, this.CollectRedirects() as any, "cond-expr" as any);
  }

  CondSkipWhitespace(): void {
    while (!this.atEnd()) {
      if (IsWhitespaceNoNewline(this.peek())) {
        this.advance();
      } else {
        if (this.peek() === "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "\n") {
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

  CondAtEnd(): boolean {
    return this.atEnd() || this.peek() === "]" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "]";
  }

  ParseCondOr(): Node {
    this.CondSkipWhitespace();
    var left: any = this.ParseCondAnd();
    this.CondSkipWhitespace();
    if (!this.CondAtEnd() && this.peek() === "|" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "|") {
      this.advance();
      this.advance();
      var right: any = this.ParseCondOr();
      return new CondOr(left as any, right as any, "cond-or" as any);
    }
    return left;
  }

  ParseCondAnd(): Node {
    this.CondSkipWhitespace();
    var left: any = this.ParseCondTerm();
    this.CondSkipWhitespace();
    if (!this.CondAtEnd() && this.peek() === "&" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "&") {
      this.advance();
      this.advance();
      var right: any = this.ParseCondAnd();
      return new CondAnd(left as any, right as any, "cond-and" as any);
    }
    return left;
  }

  ParseCondTerm(): Node {
    this.CondSkipWhitespace();
    if (this.CondAtEnd()) {
      throw new Error(`${"Unexpected end of conditional expression"} at position ${this.pos}`)
    }
    if (this.peek() === "!") {
      if (this.pos + 1 < this.length && !IsWhitespaceNoNewline((this.source[this.pos + 1] as unknown as string))) {
      } else {
        this.advance();
        var operand: any = this.ParseCondTerm();
        return new CondNot(operand as any, "cond-not" as any);
      }
    }
    if (this.peek() === "(") {
      this.advance();
      var inner: any = this.ParseCondOr();
      this.CondSkipWhitespace();
      if (this.atEnd() || this.peek() !== ")") {
        throw new Error(`${"Expected ) in conditional expression"} at position ${this.pos}`)
      }
      this.advance();
      return new CondParen(inner as any, "cond-paren" as any);
    }
    var word1: any = this.ParseCondWord();
    if (word1 === null) {
      throw new Error(`${"Expected word in conditional expression"} at position ${this.pos}`)
    }
    this.CondSkipWhitespace();
    if (COND_UNARY_OPS.has(word1.value)) {
      var operand: any = this.ParseCondWord();
      if (operand === null) {
        throw new Error(`${"Expected operand after " + word1.value} at position ${this.pos}`)
      }
      return new UnaryTest(word1.value as any, operand as any, "unary-test" as any);
    }
    if (!this.CondAtEnd() && (this.peek() !== "&" && this.peek() !== "|" && this.peek() !== ")")) {
      if (IsRedirectChar(this.peek()) && !(this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(")) {
        var op: any = this.advance();
        this.CondSkipWhitespace();
        var word2: any = this.ParseCondWord();
        if (word2 === null) {
          throw new Error(`${"Expected operand after " + op} at position ${this.pos}`)
        }
        return new BinaryTest(op as any, word1 as any, word2 as any, "binary-test" as any);
      }
      var savedPos: any = this.pos;
      var opWord: any = this.ParseCondWord();
      if (opWord !== null && COND_BINARY_OPS.has(opWord.value)) {
        this.CondSkipWhitespace();
        if (opWord.value === "=~") {
          var word2: any = this.ParseCondRegexWord();
        } else {
          var word2: any = this.ParseCondWord();
        }
        if (word2 === null) {
          throw new Error(`${"Expected operand after " + opWord.value} at position ${this.pos}`)
        }
        return new BinaryTest(opWord.value as any, word1 as any, word2 as any, "binary-test" as any);
      } else {
        this.pos = savedPos;
      }
    }
    return new UnaryTest("-n" as any, word1 as any, "unary-test" as any);
  }

  ParseCondWord(): Word {
    this.CondSkipWhitespace();
    if (this.CondAtEnd()) {
      return null;
    }
    var c: any = this.peek();
    if (IsParen(c)) {
      return null;
    }
    if (c === "&" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "&") {
      return null;
    }
    if (c === "|" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "|") {
      return null;
    }
    return this.ParseWordInternal(WORD_CTX_COND, false, false);
  }

  ParseCondRegexWord(): Word {
    this.CondSkipWhitespace();
    if (this.CondAtEnd()) {
      return null;
    }
    this.SetState(ParserStateFlags_PST_REGEXP);
    var result: any = this.ParseWordInternal(WORD_CTX_REGEX, false, false);
    this.ClearState(ParserStateFlags_PST_REGEXP);
    this.WordContext = WORD_CTX_COND;
    return result;
  }

  parseBraceGroup(): BraceGroup {
    this.skipWhitespace();
    if (!this.LexConsumeWord("{")) {
      return null;
    }
    this.skipWhitespaceAndNewlines();
    var body: any = this.parseList(true);
    if (body === null) {
      throw new Error(`${"Expected command in brace group"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespace();
    if (!this.LexConsumeWord("}")) {
      throw new Error(`${"Expected } to close brace group"} at position ${this.LexPeekToken().pos}`)
    }
    return new BraceGroup(body as any, this.CollectRedirects() as any, "brace-group" as any);
  }

  parseIf(): If {
    this.skipWhitespace();
    if (!this.LexConsumeWord("if")) {
      return null;
    }
    var condition: any = this.parseListUntil(new Set(["then"]));
    if (condition === null) {
      throw new Error(`${"Expected condition after 'if'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("then")) {
      throw new Error(`${"Expected 'then' after if condition"} at position ${this.LexPeekToken().pos}`)
    }
    var thenBody: any = this.parseListUntil(new Set(["elif", "else", "fi"]));
    if (thenBody === null) {
      throw new Error(`${"Expected commands after 'then'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    var elseBody: any = null;
    if (this.LexIsAtReservedWord("elif")) {
      this.LexConsumeWord("elif");
      var elifCondition: any = this.parseListUntil(new Set(["then"]));
      if (elifCondition === null) {
        throw new Error(`${"Expected condition after 'elif'"} at position ${this.LexPeekToken().pos}`)
      }
      this.skipWhitespaceAndNewlines();
      if (!this.LexConsumeWord("then")) {
        throw new Error(`${"Expected 'then' after elif condition"} at position ${this.LexPeekToken().pos}`)
      }
      var elifThenBody: any = this.parseListUntil(new Set(["elif", "else", "fi"]));
      if (elifThenBody === null) {
        throw new Error(`${"Expected commands after 'then'"} at position ${this.LexPeekToken().pos}`)
      }
      this.skipWhitespaceAndNewlines();
      var innerElse: any = null;
      if (this.LexIsAtReservedWord("elif")) {
        innerElse = this.ParseElifChain();
      } else {
        if (this.LexIsAtReservedWord("else")) {
          this.LexConsumeWord("else");
          innerElse = this.parseListUntil(new Set(["fi"]));
          if (innerElse === null) {
            throw new Error(`${"Expected commands after 'else'"} at position ${this.LexPeekToken().pos}`)
          }
        }
      }
      elseBody = new If(elifCondition as any, elifThenBody as any, innerElse as any, "if" as any);
    } else {
      if (this.LexIsAtReservedWord("else")) {
        this.LexConsumeWord("else");
        elseBody = this.parseListUntil(new Set(["fi"]));
        if (elseBody === null) {
          throw new Error(`${"Expected commands after 'else'"} at position ${this.LexPeekToken().pos}`)
        }
      }
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("fi")) {
      throw new Error(`${"Expected 'fi' to close if statement"} at position ${this.LexPeekToken().pos}`)
    }
    return new If(condition as any, thenBody as any, elseBody as any, this.CollectRedirects() as any, "if" as any);
  }

  ParseElifChain(): If {
    this.LexConsumeWord("elif");
    var condition: any = this.parseListUntil(new Set(["then"]));
    if (condition === null) {
      throw new Error(`${"Expected condition after 'elif'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("then")) {
      throw new Error(`${"Expected 'then' after elif condition"} at position ${this.LexPeekToken().pos}`)
    }
    var thenBody: any = this.parseListUntil(new Set(["elif", "else", "fi"]));
    if (thenBody === null) {
      throw new Error(`${"Expected commands after 'then'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    var elseBody: any = null;
    if (this.LexIsAtReservedWord("elif")) {
      elseBody = this.ParseElifChain();
    } else {
      if (this.LexIsAtReservedWord("else")) {
        this.LexConsumeWord("else");
        elseBody = this.parseListUntil(new Set(["fi"]));
        if (elseBody === null) {
          throw new Error(`${"Expected commands after 'else'"} at position ${this.LexPeekToken().pos}`)
        }
      }
    }
    return new If(condition as any, thenBody as any, elseBody as any, "if" as any);
  }

  parseWhile(): While {
    this.skipWhitespace();
    if (!this.LexConsumeWord("while")) {
      return null;
    }
    var condition: any = this.parseListUntil(new Set(["do"]));
    if (condition === null) {
      throw new Error(`${"Expected condition after 'while'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("do")) {
      throw new Error(`${"Expected 'do' after while condition"} at position ${this.LexPeekToken().pos}`)
    }
    var body: any = this.parseListUntil(new Set(["done"]));
    if (body === null) {
      throw new Error(`${"Expected commands after 'do'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("done")) {
      throw new Error(`${"Expected 'done' to close while loop"} at position ${this.LexPeekToken().pos}`)
    }
    return new While(condition as any, body as any, this.CollectRedirects() as any, "while" as any);
  }

  parseUntil(): Until {
    this.skipWhitespace();
    if (!this.LexConsumeWord("until")) {
      return null;
    }
    var condition: any = this.parseListUntil(new Set(["do"]));
    if (condition === null) {
      throw new Error(`${"Expected condition after 'until'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("do")) {
      throw new Error(`${"Expected 'do' after until condition"} at position ${this.LexPeekToken().pos}`)
    }
    var body: any = this.parseListUntil(new Set(["done"]));
    if (body === null) {
      throw new Error(`${"Expected commands after 'do'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("done")) {
      throw new Error(`${"Expected 'done' to close until loop"} at position ${this.LexPeekToken().pos}`)
    }
    return new Until(condition as any, body as any, this.CollectRedirects() as any, "until" as any);
  }

  parseFor(): Node {
    this.skipWhitespace();
    if (!this.LexConsumeWord("for")) {
      return null;
    }
    this.skipWhitespace();
    if (this.peek() === "(" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
      return this.ParseForArith();
    }
    if (this.peek() === "$") {
      var varWord: any = this.parseWord(false, false, false);
      if (varWord === null) {
        throw new Error(`${"Expected variable name after 'for'"} at position ${this.LexPeekToken().pos}`)
      }
      var varName: any = varWord.value;
    } else {
      var varName: any = this.peekWord();
      if (varName === "") {
        throw new Error(`${"Expected variable name after 'for'"} at position ${this.LexPeekToken().pos}`)
      }
      this.consumeWord(varName);
    }
    this.skipWhitespace();
    if (this.peek() === ";") {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    var words: any = null;
    if (this.LexIsAtReservedWord("in")) {
      this.LexConsumeWord("in");
      this.skipWhitespace();
      var sawDelimiter: any = IsSemicolonOrNewline(this.peek());
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
          throw new Error(`${"Expected ';' or newline before 'do'"} at position ${this.LexPeekToken().pos}`)
        }
        var word: any = this.parseWord(false, false, false);
        if (word === null) {
          break;
        }
        words.push(word);
      }
    }
    this.skipWhitespaceAndNewlines();
    if (this.peek() === "{") {
      var braceGroup: any = this.parseBraceGroup();
      if (braceGroup === null) {
        throw new Error(`${"Expected brace group in for loop"} at position ${this.LexPeekToken().pos}`)
      }
      return new For(varName as any, words as any, braceGroup.body as any, this.CollectRedirects() as any, "for" as any);
    }
    if (!this.LexConsumeWord("do")) {
      throw new Error(`${"Expected 'do' in for loop"} at position ${this.LexPeekToken().pos}`)
    }
    var body: any = this.parseListUntil(new Set(["done"]));
    if (body === null) {
      throw new Error(`${"Expected commands after 'do'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("done")) {
      throw new Error(`${"Expected 'done' to close for loop"} at position ${this.LexPeekToken().pos}`)
    }
    return new For(varName as any, words as any, body as any, this.CollectRedirects() as any, "for" as any);
  }

  ParseForArith(): ForArith {
    this.advance();
    this.advance();
    var parts: any = [];
    var current: any = [];
    var parenDepth: any = 0;
    while (!this.atEnd()) {
      var ch: any = this.peek();
      if (ch === "(") {
        parenDepth += 1;
        current.push(this.advance());
      } else {
        if (ch === ")") {
          if (parenDepth > 0) {
            parenDepth -= 1;
            current.push(this.advance());
          } else {
            if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === ")") {
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
      throw new Error(`${"Expected three expressions in for ((;;))"} at position ${this.pos}`)
    }
    var init: any = parts[0];
    var cond: any = parts[1];
    var incr: any = parts[2];
    this.skipWhitespace();
    if (!this.atEnd() && this.peek() === ";") {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    var body: any = this.ParseLoopBody("for loop");
    return new ForArith(init as any, cond as any, incr as any, body as any, this.CollectRedirects() as any, "for-arith" as any);
  }

  parseSelect(): Select {
    this.skipWhitespace();
    if (!this.LexConsumeWord("select")) {
      return null;
    }
    this.skipWhitespace();
    var varName: any = this.peekWord();
    if (varName === "") {
      throw new Error(`${"Expected variable name after 'select'"} at position ${this.LexPeekToken().pos}`)
    }
    this.consumeWord(varName);
    this.skipWhitespace();
    if (this.peek() === ";") {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    var words: any = null;
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
        var word: any = this.parseWord(false, false, false);
        if (word === null) {
          break;
        }
        words.push(word);
      }
    }
    this.skipWhitespaceAndNewlines();
    var body: any = this.ParseLoopBody("select");
    return new Select(varName as any, words as any, body as any, this.CollectRedirects() as any, "select" as any);
  }

  ConsumeCaseTerminator(): string {
    var term: any = this.LexPeekCaseTerminator();
    if (term !== "") {
      this.LexNextToken();
      return term;
    }
    return ";;";
  }

  parseCase(): Case {
    if (!this.consumeWord("case")) {
      return null;
    }
    this.SetState(ParserStateFlags_PST_CASESTMT);
    this.skipWhitespace();
    var word: any = this.parseWord(false, false, false);
    if (word === null) {
      throw new Error(`${"Expected word after 'case'"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("in")) {
      throw new Error(`${"Expected 'in' after case word"} at position ${this.LexPeekToken().pos}`)
    }
    this.skipWhitespaceAndNewlines();
    var patterns: any = [];
    this.SetState(ParserStateFlags_PST_CASEPAT);
    while (true) {
      this.skipWhitespaceAndNewlines();
      if (this.LexIsAtReservedWord("esac")) {
        var saved: any = this.pos;
        this.skipWhitespace();
        while (!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek())) {
          this.advance();
        }
        this.skipWhitespace();
        var isPattern: any = false;
        if (!this.atEnd() && this.peek() === ")") {
          if (this.EofToken === ")") {
            isPattern = false;
          } else {
            this.advance();
            this.skipWhitespace();
            if (!this.atEnd()) {
              var nextCh: any = this.peek();
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
      var patternChars: any = [];
      var extglobDepth: any = 0;
      while (!this.atEnd()) {
        var ch: any = this.peek();
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
            if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "\n") {
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
                var parenDepth: any = 2;
                while (!this.atEnd() && parenDepth > 0) {
                  var c: any = this.peek();
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
                if (this.Extglob && IsExtglobPrefix(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
                  patternChars.push(this.advance());
                  patternChars.push(this.advance());
                  extglobDepth += 1;
                } else {
                  if (ch === "[") {
                    var isCharClass: any = false;
                    var scanPos: any = this.pos + 1;
                    var scanDepth: any = 0;
                    var hasFirstBracketLiteral: any = false;
                    if (scanPos < this.length && IsCaretOrBang((this.source[scanPos] as unknown as string))) {
                      scanPos += 1;
                    }
                    if (scanPos < this.length && (this.source[scanPos] as unknown as string) === "]") {
                      if (this.source.indexOf("]", scanPos + 1) !== -1) {
                        scanPos += 1;
                        hasFirstBracketLiteral = true;
                      }
                    }
                    while (scanPos < this.length) {
                      var sc: any = (this.source[scanPos] as unknown as string);
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
      var pattern: any = patternChars.join("");
      if (!(pattern !== "")) {
        throw new Error(`${"Expected pattern in case statement"} at position ${this.LexPeekToken().pos}`)
      }
      this.skipWhitespace();
      var body: any = null;
      var isEmptyBody: any = this.LexPeekCaseTerminator() !== "";
      if (!isEmptyBody) {
        this.skipWhitespaceAndNewlines();
        if (!this.atEnd() && !this.LexIsAtReservedWord("esac")) {
          var isAtTerminator: any = this.LexPeekCaseTerminator() !== "";
          if (!isAtTerminator) {
            body = this.parseListUntil(new Set(["esac"]));
            this.skipWhitespace();
          }
        }
      }
      var terminator: any = this.ConsumeCaseTerminator();
      this.skipWhitespaceAndNewlines();
      patterns.push(new CasePattern(pattern as any, body as any, terminator as any, "pattern" as any));
    }
    this.ClearState(ParserStateFlags_PST_CASEPAT);
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("esac")) {
      this.ClearState(ParserStateFlags_PST_CASESTMT);
      throw new Error(`${"Expected 'esac' to close case statement"} at position ${this.LexPeekToken().pos}`)
    }
    this.ClearState(ParserStateFlags_PST_CASESTMT);
    return new Case(word as any, patterns as any, this.CollectRedirects() as any, "case" as any);
  }

  parseCoproc(): Coproc {
    this.skipWhitespace();
    if (!this.LexConsumeWord("coproc")) {
      return null;
    }
    this.skipWhitespace();
    var name: any = "";
    var ch: any = "";
    if (!this.atEnd()) {
      ch = this.peek();
    }
    if (ch === "{") {
      var body: any = this.parseBraceGroup();
      if (body !== null) {
        return new Coproc(body as any, name as any, "coproc" as any);
      }
    }
    if (ch === "(") {
      if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
        var body: any = this.parseArithmeticCommand();
        if (body !== null) {
          return new Coproc(body as any, name as any, "coproc" as any);
        }
      }
      var body: any = this.parseSubshell();
      if (body !== null) {
        return new Coproc(body as any, name as any, "coproc" as any);
      }
    }
    var nextWord: any = this.LexPeekReservedWord();
    if (nextWord !== "" && COMPOUND_KEYWORDS.has(nextWord)) {
      var body: any = this.parseCompoundCommand();
      if (body !== null) {
        return new Coproc(body as any, name as any, "coproc" as any);
      }
    }
    var wordStart: any = this.pos;
    var potentialName: any = this.peekWord();
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
          var body: any = this.parseBraceGroup();
          if (body !== null) {
            return new Coproc(body as any, name as any, "coproc" as any);
          }
        } else {
          if (ch === "(") {
            name = potentialName;
            if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
              var body: any = this.parseArithmeticCommand();
            } else {
              var body: any = this.parseSubshell();
            }
            if (body !== null) {
              return new Coproc(body as any, name as any, "coproc" as any);
            }
          } else {
            if (nextWord !== "" && COMPOUND_KEYWORDS.has(nextWord)) {
              name = potentialName;
              var body: any = this.parseCompoundCommand();
              if (body !== null) {
                return new Coproc(body as any, name as any, "coproc" as any);
              }
            }
          }
        }
      }
      this.pos = wordStart;
    }
    var body: any = this.parseCommand();
    if (body !== null) {
      return new Coproc(body as any, name as any, "coproc" as any);
    }
    throw new Error(`${"Expected command after coproc"} at position ${this.pos}`)
  }

  parseFunction(): FunctionName {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    var savedPos: any = this.pos;
    if (this.LexIsAtReservedWord("function")) {
      this.LexConsumeWord("function");
      this.skipWhitespace();
      var name: any = this.peekWord();
      if (name === "") {
        this.pos = savedPos;
        return null;
      }
      this.consumeWord(name);
      this.skipWhitespace();
      if (!this.atEnd() && this.peek() === "(") {
        if (this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === ")") {
          this.advance();
          this.advance();
        }
      }
      this.skipWhitespaceAndNewlines();
      var body: any = this.ParseCompoundCommand();
      if (body === null) {
        throw new Error(`${"Expected function body"} at position ${this.pos}`)
      }
      return new FunctionName(name as any, body as any, "function" as any);
    }
    var name: any = this.peekWord();
    if (name === "" || RESERVED_WORDS.has(name)) {
      return null;
    }
    if (LooksLikeAssignment(name)) {
      return null;
    }
    this.skipWhitespace();
    var nameStart: any = this.pos;
    while (!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek()) && !IsParen(this.peek())) {
      this.advance();
    }
    name = Substring(this.source, nameStart, this.pos);
    if (!(name !== "")) {
      this.pos = savedPos;
      return null;
    }
    var braceDepth: any = 0;
    var i: any = 0;
    while (i < name.length) {
      if (IsExpansionStart(name, i, "${")) {
        braceDepth += 1;
        i += 2;
        continue;
      }
      if ((name[i] as unknown as string) === "}") {
        braceDepth -= 1;
      }
      i += 1;
    }
    if (braceDepth > 0) {
      this.pos = savedPos;
      return null;
    }
    var posAfterName: any = this.pos;
    this.skipWhitespace();
    var hasWhitespace: any = this.pos > posAfterName;
    if (!hasWhitespace && name !== "" && "*?@+!$".includes((name[name.length - 1] as unknown as string))) {
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
    var body: any = this.ParseCompoundCommand();
    if (body === null) {
      throw new Error(`${"Expected function body"} at position ${this.pos}`)
    }
    return new FunctionName(name as any, body as any, "function" as any);
  }

  ParseCompoundCommand(): Node {
    var result: any = this.parseBraceGroup();
    if (result !== null) {
      return result;
    }
    if (!this.atEnd() && this.peek() === "(" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
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

  AtListUntilTerminator(stopWords: Set<string>): boolean {
    if (this.atEnd()) {
      return true;
    }
    if (this.peek() === ")") {
      return true;
    }
    if (this.peek() === "}") {
      var nextPos: any = this.pos + 1;
      if (nextPos >= this.length || IsWordEndContext((this.source[nextPos] as unknown as string))) {
        return true;
      }
    }
    var reserved: any = this.LexPeekReservedWord();
    if (reserved !== "" && stopWords.has(reserved)) {
      return true;
    }
    if (this.LexPeekCaseTerminator() !== "") {
      return true;
    }
    return false;
  }

  parseListUntil(stopWords: Set<string>): Node {
    this.skipWhitespaceAndNewlines();
    var reserved: any = this.LexPeekReservedWord();
    if (reserved !== "" && stopWords.has(reserved)) {
      return null;
    }
    var pipeline: any = this.parsePipeline();
    if (pipeline === null) {
      return null;
    }
    var parts: any = [pipeline];
    while (true) {
      this.skipWhitespace();
      var op: any = this.parseListOperator();
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
          var nextOp: any = this.PeekListOperator();
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
        parts.push(new Operator(op as any, "operator" as any));
      } else {
        if (op === "&") {
          parts.push(new Operator(op as any, "operator" as any));
          this.skipWhitespaceAndNewlines();
          if (this.AtListUntilTerminator(stopWords)) {
            break;
          }
        } else {
          if (op === "&&" || op === "||") {
            parts.push(new Operator(op as any, "operator" as any));
            this.skipWhitespaceAndNewlines();
          } else {
            parts.push(new Operator(op as any, "operator" as any));
          }
        }
      }
      if (this.AtListUntilTerminator(stopWords)) {
        break;
      }
      pipeline = this.parsePipeline();
      if (pipeline === null) {
        throw new Error(`${"Expected command after " + op} at position ${this.pos}`)
      }
      parts.push(pipeline);
    }
    if (parts.length === 1) {
      return parts[0];
    }
    return new List(parts as any, "list" as any);
  }

  parseCompoundCommand(): Node {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    var ch: any = this.peek();
    if (ch === "(" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "(") {
      var result: any = this.parseArithmeticCommand();
      if (result !== null) {
        return result;
      }
    }
    if (ch === "(") {
      return this.parseSubshell();
    }
    if (ch === "{") {
      var result: any = this.parseBraceGroup();
      if (result !== null) {
        return result;
      }
    }
    if (ch === "[" && this.pos + 1 < this.length && (this.source[this.pos + 1] as unknown as string) === "[") {
      var result: any = this.parseConditionalExpr();
      if (result !== null) {
        return result;
      }
    }
    var reserved: any = this.LexPeekReservedWord();
    if (reserved === "" && this.InProcessSub) {
      var word: any = this.peekWord();
      if (word !== "" && word.length > 1 && (word[0] as unknown as string) === "}") {
        var keywordWord: any = word.slice(1);
        if (RESERVED_WORDS.has(keywordWord) || (keywordWord === "{" || keywordWord === "}" || keywordWord === "[[" || keywordWord === "]]" || keywordWord === "!" || keywordWord === "time")) {
          reserved = keywordWord;
        }
      }
    }
    if (reserved === "fi" || reserved === "then" || reserved === "elif" || reserved === "else" || reserved === "done" || reserved === "esac" || reserved === "do" || reserved === "in") {
      throw new Error(`${`Unexpected reserved word '%v'`} at position ${this.LexPeekToken().pos}`)
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
    var func: any = this.parseFunction();
    if (func !== null) {
      return func;
    }
    return this.parseCommand();
  }

  parsePipeline(): Node {
    this.skipWhitespace();
    var prefixOrder: any = "";
    var timePosix: any = false;
    if (this.LexIsAtReservedWord("time")) {
      this.LexConsumeWord("time");
      prefixOrder = "time";
      this.skipWhitespace();
      if (!this.atEnd() && this.peek() === "-") {
        var saved: any = this.pos;
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
        if (this.pos + 2 >= this.length || IsWhitespace((this.source[this.pos + 2] as unknown as string))) {
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
          var saved: any = this.pos;
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
        if ((this.pos + 1 >= this.length || IsNegationBoundary((this.source[this.pos + 1] as unknown as string))) && !this.IsBangFollowedByProcsub()) {
          this.advance();
          prefixOrder = "time_negation";
          this.skipWhitespace();
        }
      }
    } else {
      if (!this.atEnd() && this.peek() === "!") {
        if ((this.pos + 1 >= this.length || IsNegationBoundary((this.source[this.pos + 1] as unknown as string))) && !this.IsBangFollowedByProcsub()) {
          this.advance();
          this.skipWhitespace();
          var inner: any = this.parsePipeline();
          if (inner !== null && inner.kind === "negation") {
            if ((inner as unknown as Negation).pipeline !== null) {
              return (inner as unknown as Negation).pipeline;
            } else {
              return new Command([] as any, "command" as any);
            }
          }
          return new Negation(inner as any, "negation" as any);
        }
      }
    }
    var result: any = this.ParseSimplePipeline();
    if (prefixOrder === "time") {
      result = new Time(result as any, timePosix as any, "time" as any);
    } else {
      if (prefixOrder === "negation") {
        result = new Negation(result as any, "negation" as any);
      } else {
        if (prefixOrder === "time_negation") {
          result = new Time(result as any, timePosix as any, "time" as any);
          result = new Negation(result as any, "negation" as any);
        } else {
          if (prefixOrder === "negation_time") {
            result = new Time(result as any, timePosix as any, "time" as any);
            result = new Negation(result as any, "negation" as any);
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

  ParseSimplePipeline(): Node {
    var cmd: any = this.parseCompoundCommand();
    if (cmd === null) {
      return null;
    }
    var commands: any = [cmd];
    while (true) {
      this.skipWhitespace();
      var [tokenType, value]: any = this.LexPeekOperator();
      if (tokenType === 0) {
        break;
      }
      if (tokenType !== TokenType_PIPE && tokenType !== TokenType_PIPE_AMP) {
        break;
      }
      this.LexNextToken();
      var isPipeBoth: any = tokenType === TokenType_PIPE_AMP;
      this.skipWhitespaceAndNewlines();
      if (isPipeBoth) {
        commands.push(new PipeBoth("pipe-both" as any));
      }
      cmd = this.parseCompoundCommand();
      if (cmd === null) {
        throw new Error(`${"Expected command after |"} at position ${this.pos}`)
      }
      commands.push(cmd);
    }
    if (commands.length === 1) {
      return commands[0];
    }
    return new Pipeline(commands as any, "pipeline" as any);
  }

  parseListOperator(): string {
    this.skipWhitespace();
    var [tokenType, ]: any = this.LexPeekOperator();
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

  PeekListOperator(): string {
    var savedPos: any = this.pos;
    var op: any = this.parseListOperator();
    this.pos = savedPos;
    return op;
  }

  parseList(newlineAsSeparator: boolean): Node {
    if (newlineAsSeparator) {
      this.skipWhitespaceAndNewlines();
    } else {
      this.skipWhitespace();
    }
    var pipeline: any = this.parsePipeline();
    if (pipeline === null) {
      return null;
    }
    var parts: any = [pipeline];
    if (this.InState(ParserStateFlags_PST_EOFTOKEN) && this.AtEofToken()) {
      return parts.length === 1 ? parts[0] : new List(parts as any, "list" as any);
    }
    while (true) {
      this.skipWhitespace();
      var op: any = this.parseListOperator();
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
          var nextOp: any = this.PeekListOperator();
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
      parts.push(new Operator(op as any, "operator" as any));
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
        throw new Error(`${"Expected command after " + op} at position ${this.pos}`)
      }
      parts.push(pipeline);
      if (this.InState(ParserStateFlags_PST_EOFTOKEN) && this.AtEofToken()) {
        break;
      }
    }
    if (parts.length === 1) {
      return parts[0];
    }
    return new List(parts as any, "list" as any);
  }

  parseComment(): Node {
    if (this.atEnd() || this.peek() !== "#") {
      return null;
    }
    var start: any = this.pos;
    while (!this.atEnd() && this.peek() !== "\n") {
      this.advance();
    }
    var text: any = Substring(this.source, start, this.pos);
    return new Comment(text as any, "comment" as any);
  }

  parse(): Node[] {
    var source: any = this.source.trim();
    if (!(source !== "")) {
      return [new Empty("empty" as any)];
    }
    var results: any = [];
    while (true) {
      this.skipWhitespace();
      while (!this.atEnd() && this.peek() === "\n") {
        this.advance();
      }
      if (this.atEnd()) {
        break;
      }
      var comment: any = this.parseComment();
      if (!comment !== null) {
        break;
      }
    }
    while (!this.atEnd()) {
      var result: any = this.parseList(false);
      if (result !== null) {
        results.push(result);
      }
      this.skipWhitespace();
      var foundNewline: any = false;
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
        throw new Error(`${"Syntax error"} at position ${this.pos}`)
      }
    }
    if (!(results.length > 0)) {
      return [new Empty("empty" as any)];
    }
    if (this.SawNewlineInSingleQuote && this.source !== "" && (this.source[this.source.length - 1] as unknown as string) === "\\" && !(this.source.length >= 3 && this.source.slice(this.source.length - 3, this.source.length - 1) === "\\\n")) {
      if (!this.LastWordOnOwnLine(results)) {
        this.StripTrailingBackslashFromLastWord(results);
      }
    }
    return results;
  }

  LastWordOnOwnLine(nodes: Node[]): boolean {
    return nodes.length >= 2;
  }

  StripTrailingBackslashFromLastWord(nodes: Node[]): void {
    if (!(nodes.length > 0)) {
      return;
    }
    var lastNode: any = nodes[nodes.length - 1];
    var lastWord: any = this.FindLastWord(lastNode);
    if (lastWord !== null && lastWord.value.endsWith("\\")) {
      lastWord.value = Substring(lastWord.value, 0, lastWord.value.length - 1);
      if (!(lastWord.value !== "") && lastNode instanceof Command && (lastNode as unknown as Command).words.length > 0) {
        (lastNode as unknown as Command).words.pop();
      }
    }
  }

  FindLastWord(node: Node): Word {
    if (node instanceof Word) {
      return node;
    }
    if (node instanceof Command) {
      if (node.words.length > 0) {
        var lastWord: any = node.words[node.words.length - 1];
        if (lastWord.value.endsWith("\\")) {
          return lastWord;
        }
      }
      if (node.redirects.length > 0) {
        var lastRedirect: any = node.redirects[node.redirects.length - 1];
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
  }
}

function IsHexDigit(c: string): boolean {
  return c >= "0" && c <= "9" || c >= "a" && c <= "f" || c >= "A" && c <= "F";
}

function IsOctalDigit(c: string): boolean {
  return c >= "0" && c <= "7";
}

function GetAnsiEscape(c: string): number {
  return ANSI_C_ESCAPES.get(c) ?? -1;
}

function IsWhitespace(c: string): boolean {
  return c === " " || c === "\t" || c === "\n";
}

function IsWhitespaceNoNewline(c: string): boolean {
  return c === " " || c === "\t";
}

function Substring(s: string, start: number, end: number): string {
  if (end > s.length) {
    end = s.length;
  }
  return s.slice(start, end);
}

function StartsWithAt(s: string, pos: number, prefix: string): boolean {
  return s.startsWith(prefix, pos);
}

function CountConsecutiveDollarsBefore(s: string, pos: number): number {
  var count: any = 0;
  var k: any = pos - 1;
  while (k >= 0 && (s[k] as unknown as string) === "$") {
    var bsCount: any = 0;
    var j: any = k - 1;
    while (j >= 0 && (s[j] as unknown as string) === "\\") {
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

function IsExpansionStart(s: string, pos: number, delimiter: string): boolean {
  if (!StartsWithAt(s, pos, delimiter)) {
    return false;
  }
  return CountConsecutiveDollarsBefore(s, pos) % 2 === 0;
}

function Sublist(lst: Node[], start: number, end: number): Node[] {
  return lst.slice(start, end);
}

function RepeatStr(s: string, n: number): string {
  var result: any = [];
  var i: any = 0;
  while (i < n) {
    result.push(s);
    i += 1;
  }
  return result.join("");
}

function StripLineContinuationsCommentAware(text: string): string {
  var result: any = [];
  var i: any = 0;
  var inComment: any = false;
  var quote: any = newQuoteState();
  while (i < text.length) {
    var c: any = (text[i] as unknown as string);
    if (c === "\\" && i + 1 < text.length && (text[i + 1] as unknown as string) === "\n") {
      var numPrecedingBackslashes: any = 0;
      var j: any = i - 1;
      while (j >= 0 && (text[j] as unknown as string) === "\\") {
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

function AppendRedirects(base: string, redirects: Node[]): string {
  if (redirects.length > 0) {
    var parts: any = [];
    for (const r of redirects) {
      parts.push(r.toSexp());
    }
    return base + " " + parts.join(" ");
  }
  return base;
}

function FormatArithVal(s: string): string {
  var w: any = new Word(s as any, [] as any, "word" as any);
  var val: any = w.ExpandAllAnsiCQuotes(s);
  val = w.StripLocaleStringDollars(val);
  val = w.FormatCommandSubstitutions(val, false);
  val = val.replace("\\", "\\\\").replace("\"", "\\\"");
  val = val.replace("\n", "\\n").replace("\t", "\\t");
  return val;
}

function ConsumeSingleQuote(s: string, start: number): [number, string[]] {
  var chars: any = ["'"];
  var i: any = start + 1;
  while (i < s.length && (s[i] as unknown as string) !== "'") {
    chars.push((s[i] as unknown as string));
    i += 1;
  }
  if (i < s.length) {
    chars.push((s[i] as unknown as string));
    i += 1;
  }
  return [i, chars];
}

function ConsumeDoubleQuote(s: string, start: number): [number, string[]] {
  var chars: any = ["\""];
  var i: any = start + 1;
  while (i < s.length && (s[i] as unknown as string) !== "\"") {
    if ((s[i] as unknown as string) === "\\" && i + 1 < s.length) {
      chars.push((s[i] as unknown as string));
      i += 1;
    }
    chars.push((s[i] as unknown as string));
    i += 1;
  }
  if (i < s.length) {
    chars.push((s[i] as unknown as string));
    i += 1;
  }
  return [i, chars];
}

function HasBracketClose(s: string, start: number, depth: number): boolean {
  var i: any = start;
  while (i < s.length) {
    if ((s[i] as unknown as string) === "]") {
      return true;
    }
    if (((s[i] as unknown as string) === "|" || (s[i] as unknown as string) === ")") && depth === 0) {
      return false;
    }
    i += 1;
  }
  return false;
}

function ConsumeBracketClass(s: string, start: number, depth: number): [number, string[], boolean] {
  var scanPos: any = start + 1;
  if (scanPos < s.length && ((s[scanPos] as unknown as string) === "!" || (s[scanPos] as unknown as string) === "^")) {
    scanPos += 1;
  }
  if (scanPos < s.length && (s[scanPos] as unknown as string) === "]") {
    if (HasBracketClose(s, scanPos + 1, depth)) {
      scanPos += 1;
    }
  }
  var isBracket: any = false;
  while (scanPos < s.length) {
    if ((s[scanPos] as unknown as string) === "]") {
      isBracket = true;
      break;
    }
    if ((s[scanPos] as unknown as string) === ")" && depth === 0) {
      break;
    }
    if ((s[scanPos] as unknown as string) === "|" && depth === 0) {
      break;
    }
    scanPos += 1;
  }
  if (!isBracket) {
    return [start + 1, ["["], false];
  }
  var chars: any = ["["];
  var i: any = start + 1;
  if (i < s.length && ((s[i] as unknown as string) === "!" || (s[i] as unknown as string) === "^")) {
    chars.push((s[i] as unknown as string));
    i += 1;
  }
  if (i < s.length && (s[i] as unknown as string) === "]") {
    if (HasBracketClose(s, i + 1, depth)) {
      chars.push((s[i] as unknown as string));
      i += 1;
    }
  }
  while (i < s.length && (s[i] as unknown as string) !== "]") {
    chars.push((s[i] as unknown as string));
    i += 1;
  }
  if (i < s.length) {
    chars.push((s[i] as unknown as string));
    i += 1;
  }
  return [i, chars, true];
}

function FormatCondBody(node: Node): string {
  var kind: any = node.kind;
  if (kind === "unary-test") {
    var operandVal: any = ((node as unknown as UnaryTest).operand as unknown as Word).getCondFormattedValue();
    return (node as unknown as UnaryTest).op + " " + operandVal;
  }
  if (kind === "binary-test") {
    var leftVal: any = ((node as unknown as BinaryTest).left as unknown as Word).getCondFormattedValue();
    var rightVal: any = ((node as unknown as BinaryTest).right as unknown as Word).getCondFormattedValue();
    return leftVal + " " + (node as unknown as BinaryTest).op + " " + rightVal;
  }
  if (kind === "cond-and") {
    return FormatCondBody((node as unknown as CondAnd).left) + " && " + FormatCondBody((node as unknown as CondAnd).right);
  }
  if (kind === "cond-or") {
    return FormatCondBody((node as unknown as CondOr).left) + " || " + FormatCondBody((node as unknown as CondOr).right);
  }
  if (kind === "cond-not") {
    return "! " + FormatCondBody((node as unknown as CondNot).operand);
  }
  if (kind === "cond-paren") {
    return "( " + FormatCondBody((node as unknown as CondParen).inner) + " )";
  }
  return "";
}

function StartsWithSubshell(node: Node): boolean {
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
    if (node.commands.length > 0) {
      return StartsWithSubshell(node.commands[0]);
    }
    return false;
  }
  return false;
}

function FormatCmdsubNode(node: Node, indent: number, inProcsub: boolean, compactRedirects: boolean, procsubFirst: boolean): string {
  if (node === null) {
    return "";
  }
  var sp: any = RepeatStr(" ", indent);
  var innerSp: any = RepeatStr(" ", indent + 4);
  if (node instanceof ArithEmpty) {
    return "";
  }
  if (node instanceof Command) {
    var parts: any = [];
    for (const w of node.words) {
      var val: any = w.ExpandAllAnsiCQuotes(w.value);
      val = w.StripLocaleStringDollars(val);
      val = w.NormalizeArrayWhitespace(val);
      val = w.FormatCommandSubstitutions(val, false);
      parts.push(val);
    }
    var heredocs: any = [];
    for (const r of node.redirects) {
      if (r instanceof HereDoc) {
        heredocs.push(r);
      }
    }
    for (const r of node.redirects) {
      parts.push(FormatRedirect(r, compactRedirects, true));
    }
    if (compactRedirects && node.words.length > 0 && node.redirects.length > 0) {
      var wordParts: any = parts.slice(0, node.words.length);
      var redirectParts: any = parts.slice(node.words.length);
      var result: any = wordParts.join(" ") + redirectParts.join("");
    } else {
      var result: any = parts.join(" ");
    }
    for (const h of heredocs) {
      var result: any = result + FormatHeredocBody(h);
    }
    return result;
  }
  if (node instanceof Pipeline) {
    var cmds: any = [];
    var i: any = 0;
    while (i < node.commands.length) {
      var cmd: any = node.commands[i];
      if (cmd instanceof PipeBoth) {
        i += 1;
        continue;
      }
      var needsRedirect: any = i + 1 < node.commands.length && node.commands[i + 1].kind === "pipe-both";
      cmds.push([cmd, needsRedirect]);
      i += 1;
    }
    var resultParts: any = [];
    var idx: any = 0;
    while (idx < cmds.length) {
      {
        var Entry: any = cmds[idx];
        cmd = Entry[0];
        needsRedirect = Entry[1];
      }
      var formatted: any = FormatCmdsubNode(cmd, indent, inProcsub, false, procsubFirst && idx === 0);
      var isLast: any = idx === cmds.length - 1;
      var hasHeredoc: any = false;
      if (cmd.kind === "command" && (cmd as unknown as Command).redirects.length > 0) {
        for (const r of (cmd as unknown as Command).redirects) {
          if (r instanceof HereDoc) {
            hasHeredoc = true;
            break;
          }
        }
      }
      if (needsRedirect) {
        if (hasHeredoc) {
          var firstNl: any = formatted.indexOf("\n");
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
        var firstNl: any = formatted.indexOf("\n");
        if (firstNl !== -1) {
          formatted = formatted.slice(0, firstNl) + " |" + formatted.slice(firstNl);
        }
        resultParts.push(formatted);
      } else {
        resultParts.push(formatted);
      }
      idx += 1;
    }
    var compactPipe: any = inProcsub && cmds.length > 0 && cmds[0][0].kind === "subshell";
    var result: any = "";
    idx = 0;
    while (idx < resultParts.length) {
      var part: any = resultParts[idx];
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
    var hasHeredoc: any = false;
    for (const p of node.parts) {
      if (p.kind === "command" && (p as unknown as Command).redirects.length > 0) {
        for (const r of (p as unknown as Command).redirects) {
          if (r instanceof HereDoc) {
            hasHeredoc = true;
            break;
          }
        }
      } else {
        if (p instanceof Pipeline) {
          for (const cmd of p.commands) {
            if (cmd.kind === "command" && (cmd as unknown as Command).redirects.length > 0) {
              for (const r of (cmd as unknown as Command).redirects) {
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
    var result: any = [];
    var skippedSemi: any = false;
    var cmdCount: any = 0;
    for (const p of node.parts) {
      if (p instanceof Operator) {
        if (p.op === ";") {
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
        } else {
          if (p.op === "\n") {
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
          } else {
            if (p.op === "&") {
              if (result.length > 0 && result[result.length - 1].includes("<<") && result[result.length - 1].includes("\n")) {
                var last: any = result[result.length - 1];
                if (last.includes(" |") || last.startsWith("|")) {
                  result[result.length - 1] = last + " &";
                } else {
                  var firstNl: any = last.indexOf("\n");
                  result[result.length - 1] = last.slice(0, firstNl) + " &" + last.slice(firstNl);
                }
              } else {
                result.push(" &");
              }
            } else {
              if (result.length > 0 && result[result.length - 1].includes("<<") && result[result.length - 1].includes("\n")) {
                var last: any = result[result.length - 1];
                var firstNl: any = last.indexOf("\n");
                result[result.length - 1] = last.slice(0, firstNl) + " " + p.op + " " + last.slice(firstNl);
              } else {
                result.push(" " + p.op);
              }
            }
          }
        }
      } else {
        if (result.length > 0 && !result[result.length - 1].endsWith([" ", "\n"])) {
          result.push(" ");
        }
        var formattedCmd: any = FormatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount === 0);
        if (result.length > 0) {
          var last: any = result[result.length - 1];
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
    var s: any = result.join("");
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
    var cond: any = FormatCmdsubNode(node.condition, indent, false, false, false);
    var thenBody: any = FormatCmdsubNode(node.thenBody, indent + 4, false, false, false);
    var result: any = "if " + cond + "; then\n" + innerSp + thenBody + ";";
    if (node.elseBody !== null) {
      var elseBody: any = FormatCmdsubNode(node.elseBody, indent + 4, false, false, false);
      result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";";
    }
    result = result + "\n" + sp + "fi";
    return result;
  }
  if (node instanceof While) {
    var cond: any = FormatCmdsubNode(node.condition, indent, false, false, false);
    var body: any = FormatCmdsubNode(node.body, indent + 4, false, false, false);
    var result: any = "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
    if (node.redirects.length > 0) {
      for (const r of node.redirects) {
        result = result + " " + FormatRedirect(r, false, false);
      }
    }
    return result;
  }
  if (node instanceof Until) {
    var cond: any = FormatCmdsubNode(node.condition, indent, false, false, false);
    var body: any = FormatCmdsubNode(node.body, indent + 4, false, false, false);
    var result: any = "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
    if (node.redirects.length > 0) {
      for (const r of node.redirects) {
        result = result + " " + FormatRedirect(r, false, false);
      }
    }
    return result;
  }
  if (node instanceof For) {
    var varName: any = node.varName;
    var body: any = FormatCmdsubNode(node.body, indent + 4, false, false, false);
    if (node.words !== null) {
      var wordVals: any = [];
      for (const w of node.words) {
        wordVals.push(w.value);
      }
      var words: any = wordVals.join(" ");
      if (words !== "") {
        var result: any = "for " + varName + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
      } else {
        var result: any = "for " + varName + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
      }
    } else {
      var result: any = "for " + varName + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
    }
    if (node.redirects.length > 0) {
      for (const r of node.redirects) {
        var result: any = result + " " + FormatRedirect(r, false, false);
      }
    }
    return result;
  }
  if (node instanceof ForArith) {
    var body: any = FormatCmdsubNode(node.body, indent + 4, false, false, false);
    var result: any = "for ((" + node.init + "; " + node.cond + "; " + node.incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done";
    if (node.redirects.length > 0) {
      for (const r of node.redirects) {
        result = result + " " + FormatRedirect(r, false, false);
      }
    }
    return result;
  }
  if (node instanceof Case) {
    var word: any = (node.word as unknown as Word).value;
    var patterns: any = [];
    var i: any = 0;
    while (i < node.patterns.length) {
      var p: any = node.patterns[i];
      var pat: any = (p as unknown as CasePattern).pattern.replace("|", " | ");
      if ((p as unknown as CasePattern).body !== null) {
        var body: any = FormatCmdsubNode((p as unknown as CasePattern).body, indent + 8, false, false, false);
      } else {
        var body: any = "";
      }
      var term: any = (p as unknown as CasePattern).terminator;
      var patIndent: any = RepeatStr(" ", indent + 8);
      var termIndent: any = RepeatStr(" ", indent + 4);
      var bodyPart: any = body !== "" ? patIndent + body + "\n" : "\n";
      if (i === 0) {
        patterns.push(" " + pat + ")\n" + bodyPart + termIndent + term);
      } else {
        patterns.push(pat + ")\n" + bodyPart + termIndent + term);
      }
      i += 1;
    }
    var patternStr: any = patterns.join("\n" + RepeatStr(" ", indent + 4));
    var redirects: any = "";
    if (node.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of node.redirects) {
        redirectParts.push(FormatRedirect(r, false, false));
      }
      redirects = " " + redirectParts.join(" ");
    }
    return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects;
  }
  if (node instanceof FunctionName) {
    var name: any = node.name;
    var innerBody: any = node.body.kind === "brace-group" ? (node.body as unknown as BraceGroup).body : node.body;
    var body: any = FormatCmdsubNode(innerBody, indent + 4, false, false, false).replace(/[;]+$/, '');
    return `function %v () 
{ 
%v%v
}`;
  }
  if (node instanceof Subshell) {
    var body: any = FormatCmdsubNode(node.body, indent, inProcsub, compactRedirects, false);
    var redirects: any = "";
    if (node.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of node.redirects) {
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
    var body: any = FormatCmdsubNode(node.body, indent, false, false, false);
    body = body.replace(/[;]+$/, '');
    var terminator: any = body.endsWith(" &") ? " }" : "; }";
    var redirects: any = "";
    if (node.redirects.length > 0) {
      var redirectParts: any = [];
      for (const r of node.redirects) {
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
    var body: any = FormatCondBody((node.body as unknown as Node));
    return "[[ " + body + " ]]";
  }
  if (node instanceof Negation) {
    if (node.pipeline !== null) {
      return "! " + FormatCmdsubNode(node.pipeline, indent, false, false, false);
    }
    return "! ";
  }
  if (node instanceof Time) {
    var prefix: any = node.posix ? "time -p " : "time ";
    if (node.pipeline !== null) {
      return prefix + FormatCmdsubNode(node.pipeline, indent, false, false, false);
    }
    return prefix;
  }
  return "";
}

function FormatRedirect(r: Node, compact: boolean, heredocOpOnly: boolean): string {
  if (r instanceof HereDoc) {
    if (r.stripTabs) {
      var op: any = "<<-";
    } else {
      var op: any = "<<";
    }
    if (r.fd !== null && r.fd !== 0) {
      var op: any = String(r.fd) + op;
    }
    if (r.quoted) {
      var delim: any = "'" + r.delimiter + "'";
    } else {
      var delim: any = r.delimiter;
    }
    if (heredocOpOnly) {
      return op + delim;
    }
    return op + delim + "\n" + r.content + r.delimiter + "\n";
  }
  var op: any = (r as unknown as Redirect).op;
  if (op === "1>") {
    op = ">";
  } else {
    if (op === "0<") {
      op = "<";
    }
  }
  var target: any = (r as unknown as Redirect).target.value;
  target = (r as unknown as Redirect).target.ExpandAllAnsiCQuotes(target);
  target = (r as unknown as Redirect).target.StripLocaleStringDollars(target);
  target = (r as unknown as Redirect).target.FormatCommandSubstitutions(target, false);
  if (target.startsWith("&")) {
    var wasInputClose: any = false;
    if (target === "&-" && op.endsWith("<")) {
      wasInputClose = true;
      op = Substring(op, 0, op.length - 1) + ">";
    }
    var afterAmp: any = Substring(target, 1, target.length);
    var isLiteralFd: any = afterAmp === "-" || afterAmp.length > 0 && /^[0-9]$/.test((afterAmp[0] as unknown as string));
    if (isLiteralFd) {
      if (op === ">" || op === ">&") {
        op = wasInputClose ? "0>" : "1>";
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

function FormatHeredocBody(r: Node): string {
  return "\n" + (r as unknown as HereDoc).content + (r as unknown as HereDoc).delimiter + "\n";
}

function LookaheadForEsac(value: string, start: number, caseDepth: number): boolean {
  var i: any = start;
  var depth: any = caseDepth;
  var quote: any = newQuoteState();
  while (i < value.length) {
    var c: any = (value[i] as unknown as string);
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

function SkipBacktick(value: string, start: number): number {
  var i: any = start + 1;
  while (i < value.length && (value[i] as unknown as string) !== "`") {
    if ((value[i] as unknown as string) === "\\" && i + 1 < value.length) {
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

function SkipSingleQuoted(s: string, start: number): number {
  var i: any = start;
  while (i < s.length && (s[i] as unknown as string) !== "'") {
    i += 1;
  }
  return i < s.length ? i + 1 : i;
}

function SkipDoubleQuoted(s: string, start: number): number {
  {
    var i: any = start;
    var n: any = s.length;
  }
  {
    var passNext: any = false;
    var backq: any = false;
  }
  while (i < n) {
    var c: any = (s[i] as unknown as string);
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
      if ((s[i + 1] as unknown as string) === "(") {
        i = FindCmdsubEnd(s, i + 2);
        continue;
      }
      if ((s[i + 1] as unknown as string) === "{") {
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

function IsValidArithmeticStart(value: string, start: number): boolean {
  var scanParen: any = 0;
  var scanI: any = start + 3;
  while (scanI < value.length) {
    var scanC: any = (value[scanI] as unknown as string);
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
          if (scanI + 1 < value.length && (value[scanI + 1] as unknown as string) === ")") {
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

function FindFunsubEnd(value: string, start: number): number {
  var depth: any = 1;
  var i: any = start;
  var quote: any = newQuoteState();
  while (i < value.length && depth > 0) {
    var c: any = (value[i] as unknown as string);
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

function FindCmdsubEnd(value: string, start: number): number {
  var depth: any = 1;
  var i: any = start;
  var caseDepth: any = 0;
  var inCasePatterns: any = false;
  var arithDepth: any = 0;
  var arithParenDepth: any = 0;
  while (i < value.length && depth > 0) {
    var c: any = (value[i] as unknown as string);
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
    if (c === "#" && arithDepth === 0 && (i === start || (value[i - 1] as unknown as string) === " " || (value[i - 1] as unknown as string) === "\t" || (value[i - 1] as unknown as string) === "\n" || (value[i - 1] as unknown as string) === ";" || (value[i - 1] as unknown as string) === "|" || (value[i - 1] as unknown as string) === "&" || (value[i - 1] as unknown as string) === "(" || (value[i - 1] as unknown as string) === ")")) {
      while (i < value.length && (value[i] as unknown as string) !== "\n") {
        i += 1;
      }
      continue;
    }
    if (StartsWithAt(value, i, "<<<")) {
      i += 3;
      while (i < value.length && ((value[i] as unknown as string) === " " || (value[i] as unknown as string) === "\t")) {
        i += 1;
      }
      if (i < value.length && (value[i] as unknown as string) === "\"") {
        i += 1;
        while (i < value.length && (value[i] as unknown as string) !== "\"") {
          if ((value[i] as unknown as string) === "\\" && i + 1 < value.length) {
            i += 2;
          } else {
            i += 1;
          }
        }
        if (i < value.length) {
          i += 1;
        }
      } else {
        if (i < value.length && (value[i] as unknown as string) === "'") {
          i += 1;
          while (i < value.length && (value[i] as unknown as string) !== "'") {
            i += 1;
          }
          if (i < value.length) {
            i += 1;
          }
        } else {
          while (i < value.length && !" \t\n;|&<>()".includes((value[i] as unknown as string))) {
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
      var j: any = FindCmdsubEnd(value, i + 2);
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

function FindBracedParamEnd(value: string, start: number): number {
  var depth: any = 1;
  var i: any = start;
  var inDouble: any = false;
  var dolbraceState: any = DolbraceState_PARAM;
  while (i < value.length && depth > 0) {
    var c: any = (value[i] as unknown as string);
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
      var end: any = SkipSubscript(value, i, 0);
      if (end !== -1) {
        i = end;
        continue;
      }
    }
    if ((c === "<" || c === ">") && i + 1 < value.length && (value[i + 1] as unknown as string) === "(") {
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

function SkipHeredoc(value: string, start: number): number {
  var i: any = start + 2;
  if (i < value.length && (value[i] as unknown as string) === "-") {
    i += 1;
  }
  while (i < value.length && IsWhitespaceNoNewline((value[i] as unknown as string))) {
    i += 1;
  }
  var delimStart: any = i;
  var quoteChar: any = null;
  if (i < value.length && ((value[i] as unknown as string) === "\"" || (value[i] as unknown as string) === "'")) {
    quoteChar = (value[i] as unknown as string);
    i += 1;
    delimStart = i;
    while (i < value.length && (value[i] as unknown as string) !== quoteChar) {
      i += 1;
    }
    var delimiter: any = Substring(value, delimStart, i);
    if (i < value.length) {
      i += 1;
    }
  } else {
    if (i < value.length && (value[i] as unknown as string) === "\\") {
      i += 1;
      delimStart = i;
      if (i < value.length) {
        i += 1;
      }
      while (i < value.length && !IsMetachar((value[i] as unknown as string))) {
        i += 1;
      }
      var delimiter: any = Substring(value, delimStart, i);
    } else {
      while (i < value.length && !IsMetachar((value[i] as unknown as string))) {
        i += 1;
      }
      var delimiter: any = Substring(value, delimStart, i);
    }
  }
  var parenDepth: any = 0;
  var quote: any = newQuoteState();
  var inBacktick: any = false;
  while (i < value.length && (value[i] as unknown as string) !== "\n") {
    var c: any = (value[i] as unknown as string);
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
  if (i < value.length && (value[i] as unknown as string) === ")") {
    return i;
  }
  if (i < value.length && (value[i] as unknown as string) === "\n") {
    i += 1;
  }
  while (i < value.length) {
    var lineStart: any = i;
    var lineEnd: any = i;
    while (lineEnd < value.length && (value[lineEnd] as unknown as string) !== "\n") {
      lineEnd += 1;
    }
    var line: any = Substring(value, lineStart, lineEnd);
    while (lineEnd < value.length) {
      var trailingBs: any = 0;
      for (const j of range(line.length - 1, -1, -1)) {
        if ((line[j] as unknown as string) === "\\") {
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
      var nextLineStart: any = lineEnd;
      while (lineEnd < value.length && (value[lineEnd] as unknown as string) !== "\n") {
        lineEnd += 1;
      }
      line = line + Substring(value, nextLineStart, lineEnd);
    }
    if (start + 2 < value.length && (value[start + 2] as unknown as string) === "-") {
      var stripped: any = line.replace(/^[\t]+/, '');
    } else {
      var stripped: any = line;
    }
    if (stripped === delimiter) {
      if (lineEnd < value.length) {
        return lineEnd + 1;
      } else {
        return lineEnd;
      }
    }
    if (stripped.startsWith(delimiter) && stripped.length > delimiter.length) {
      var tabsStripped: any = line.length - stripped.length;
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

function FindHeredocContentEnd(source: string, start: number, delimiters: [string, boolean][]): [number, number] {
  if (!(delimiters.length > 0)) {
    return [start, start];
  }
  var pos: any = start;
  while (pos < source.length && (source[pos] as unknown as string) !== "\n") {
    pos += 1;
  }
  if (pos >= source.length) {
    return [start, start];
  }
  var contentStart: any = pos;
  pos += 1;
  for (const Item of delimiters) {
    var delimiter: any = Item[0];
    var stripTabs: any = Item[1];
    while (pos < source.length) {
      var lineStart: any = pos;
      var lineEnd: any = pos;
      while (lineEnd < source.length && (source[lineEnd] as unknown as string) !== "\n") {
        lineEnd += 1;
      }
      var line: any = Substring(source, lineStart, lineEnd);
      while (lineEnd < source.length) {
        var trailingBs: any = 0;
        for (const j of range(line.length - 1, -1, -1)) {
          if ((line[j] as unknown as string) === "\\") {
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
        var nextLineStart: any = lineEnd;
        while (lineEnd < source.length && (source[lineEnd] as unknown as string) !== "\n") {
          lineEnd += 1;
        }
        line = line + Substring(source, nextLineStart, lineEnd);
      }
      if (stripTabs) {
        var lineStripped: any = line.replace(/^[\t]+/, '');
      } else {
        var lineStripped: any = line;
      }
      if (lineStripped === delimiter) {
        pos = lineEnd < source.length ? lineEnd + 1 : lineEnd;
        break;
      }
      if (lineStripped.startsWith(delimiter) && lineStripped.length > delimiter.length) {
        var tabsStripped: any = line.length - lineStripped.length;
        pos = lineStart + tabsStripped + delimiter.length;
        break;
      }
      pos = lineEnd < source.length ? lineEnd + 1 : lineEnd;
    }
  }
  return [contentStart, pos];
}

function IsWordBoundary(s: string, pos: number, wordLen: number): boolean {
  if (pos > 0) {
    var prev: any = (s[pos - 1] as unknown as string);
    if (/^[a-zA-Z0-9]$/.test(prev) || prev === "_") {
      return false;
    }
    if ("{}!".includes(prev)) {
      return false;
    }
  }
  var end: any = pos + wordLen;
  if (end < s.length && (/^[a-zA-Z0-9]$/.test((s[end] as unknown as string)) || (s[end] as unknown as string) === "_")) {
    return false;
  }
  return true;
}

function IsQuote(c: string): boolean {
  return c === "'" || c === "\"";
}

function CollapseWhitespace(s: string): string {
  var result: any = [];
  var prevWasWs: any = false;
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
  var joined: any = result.join("");
  return joined.replace(/^[ \t]+/, '').replace(/[ \t]+$/, '');
}

function CountTrailingBackslashes(s: string): number {
  var count: any = 0;
  for (const i of range(s.length - 1, -1, -1)) {
    if ((s[i] as unknown as string) === "\\") {
      count += 1;
    } else {
      break;
    }
  }
  return count;
}

function NormalizeHeredocDelimiter(delimiter: string): string {
  var result: any = [];
  var i: any = 0;
  while (i < delimiter.length) {
    if (i + 1 < delimiter.length && delimiter.slice(i, i + 2) === "$(") {
      result.push("$(");
      i += 2;
      var depth: any = 1;
      var inner: any = [];
      while (i < delimiter.length && depth > 0) {
        if ((delimiter[i] as unknown as string) === "(") {
          depth += 1;
          inner.push((delimiter[i] as unknown as string));
        } else {
          if ((delimiter[i] as unknown as string) === ")") {
            depth -= 1;
            if (depth === 0) {
              var innerStr: any = inner.join("");
              innerStr = CollapseWhitespace(innerStr);
              result.push(innerStr);
              result.push(")");
            } else {
              inner.push((delimiter[i] as unknown as string));
            }
          } else {
            inner.push((delimiter[i] as unknown as string));
          }
        }
        i += 1;
      }
    } else {
      if (i + 1 < delimiter.length && delimiter.slice(i, i + 2) === "${") {
        result.push("${");
        i += 2;
        var depth: any = 1;
        var inner: any = [];
        while (i < delimiter.length && depth > 0) {
          if ((delimiter[i] as unknown as string) === "{") {
            depth += 1;
            inner.push((delimiter[i] as unknown as string));
          } else {
            if ((delimiter[i] as unknown as string) === "}") {
              depth -= 1;
              if (depth === 0) {
                var innerStr: any = inner.join("");
                innerStr = CollapseWhitespace(innerStr);
                result.push(innerStr);
                result.push("}");
              } else {
                inner.push((delimiter[i] as unknown as string));
              }
            } else {
              inner.push((delimiter[i] as unknown as string));
            }
          }
          i += 1;
        }
      } else {
        if (i + 1 < delimiter.length && "<>".includes((delimiter[i] as unknown as string)) && (delimiter[i + 1] as unknown as string) === "(") {
          result.push((delimiter[i] as unknown as string));
          result.push("(");
          i += 2;
          var depth: any = 1;
          var inner: any = [];
          while (i < delimiter.length && depth > 0) {
            if ((delimiter[i] as unknown as string) === "(") {
              depth += 1;
              inner.push((delimiter[i] as unknown as string));
            } else {
              if ((delimiter[i] as unknown as string) === ")") {
                depth -= 1;
                if (depth === 0) {
                  var innerStr: any = inner.join("");
                  innerStr = CollapseWhitespace(innerStr);
                  result.push(innerStr);
                  result.push(")");
                } else {
                  inner.push((delimiter[i] as unknown as string));
                }
              } else {
                inner.push((delimiter[i] as unknown as string));
              }
            }
            i += 1;
          }
        } else {
          result.push((delimiter[i] as unknown as string));
          i += 1;
        }
      }
    }
  }
  return result.join("");
}

function IsMetachar(c: string): boolean {
  return c === " " || c === "\t" || c === "\n" || c === "|" || c === "&" || c === ";" || c === "(" || c === ")" || c === "<" || c === ">";
}

function IsFunsubChar(c: string): boolean {
  return c === " " || c === "\t" || c === "\n" || c === "|";
}

function IsExtglobPrefix(c: string): boolean {
  return c === "@" || c === "?" || c === "*" || c === "+" || c === "!";
}

function IsRedirectChar(c: string): boolean {
  return c === "<" || c === ">";
}

function IsSpecialParam(c: string): boolean {
  return c === "?" || c === "$" || c === "!" || c === "#" || c === "@" || c === "*" || c === "-" || c === "&";
}

function IsSpecialParamUnbraced(c: string): boolean {
  return c === "?" || c === "$" || c === "!" || c === "#" || c === "@" || c === "*" || c === "-";
}

function IsDigit(c: string): boolean {
  return c >= "0" && c <= "9";
}

function IsSemicolonOrNewline(c: string): boolean {
  return c === ";" || c === "\n";
}

function IsWordEndContext(c: string): boolean {
  return c === " " || c === "\t" || c === "\n" || c === ";" || c === "|" || c === "&" || c === "<" || c === ">" || c === "(" || c === ")";
}

function SkipMatchedPair(s: string, start: number, open: string, close: string, flags: number): number {
  var n: any = s.length;
  if ((flags & _SMP_PAST_OPEN) !== 0) {
    var i: any = start;
  } else {
    if (start >= n || (s[start] as unknown as string) !== open) {
      return -1;
    }
    var i: any = start + 1;
  }
  var depth: any = 1;
  var passNext: any = false;
  var backq: any = false;
  while (i < n && depth > 0) {
    var c: any = (s[i] as unknown as string);
    if (passNext) {
      passNext = false;
      i += 1;
      continue;
    }
    var literal: any = flags & _SMP_LITERAL;
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
      var i: any = SkipSingleQuoted(s, i + 1);
      continue;
    }
    if (!(literal !== 0) && c === "\"") {
      var i: any = SkipDoubleQuoted(s, i + 1);
      continue;
    }
    if (!(literal !== 0) && IsExpansionStart(s, i, "$(")) {
      var i: any = FindCmdsubEnd(s, i + 2);
      continue;
    }
    if (!(literal !== 0) && IsExpansionStart(s, i, "${")) {
      var i: any = FindBracedParamEnd(s, i + 2);
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
  return depth === 0 ? i : -1;
}

function SkipSubscript(s: string, start: number, flags: number): number {
  return SkipMatchedPair(s, start, "[", "]", flags);
}

function Assignment(s: string, flags: number): number {
  if (!(s !== "")) {
    return -1;
  }
  if (!(/^[a-zA-Z]$/.test((s[0] as unknown as string)) || (s[0] as unknown as string) === "_")) {
    return -1;
  }
  var i: any = 1;
  while (i < s.length) {
    var c: any = (s[i] as unknown as string);
    if (c === "=") {
      return i;
    }
    if (c === "[") {
      var subFlags: any = (flags & 2) !== 0 ? _SMP_LITERAL : 0;
      var end: any = SkipSubscript(s, i, subFlags);
      if (end === -1) {
        return -1;
      }
      i = end;
      if (i < s.length && (s[i] as unknown as string) === "+") {
        i += 1;
      }
      if (i < s.length && (s[i] as unknown as string) === "=") {
        return i;
      }
      return -1;
    }
    if (c === "+") {
      if (i + 1 < s.length && (s[i + 1] as unknown as string) === "=") {
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

function IsArrayAssignmentPrefix(chars: string[]): boolean {
  if (!(chars.length > 0)) {
    return false;
  }
  if (!(/^[a-zA-Z]$/.test(chars[0]) || chars[0] === "_")) {
    return false;
  }
  var s: any = chars.join("");
  var i: any = 1;
  while (i < s.length && (/^[a-zA-Z0-9]$/.test((s[i] as unknown as string)) || (s[i] as unknown as string) === "_")) {
    i += 1;
  }
  while (i < s.length) {
    if ((s[i] as unknown as string) !== "[") {
      return false;
    }
    var end: any = SkipSubscript(s, i, _SMP_LITERAL);
    if (end === -1) {
      return false;
    }
    i = end;
  }
  return true;
}

function IsSpecialParamOrDigit(c: string): boolean {
  return IsSpecialParam(c) || IsDigit(c);
}

function IsParamExpansionOp(c: string): boolean {
  return c === ":" || c === "-" || c === "=" || c === "+" || c === "?" || c === "#" || c === "%" || c === "/" || c === "^" || c === "," || c === "@" || c === "*" || c === "[";
}

function IsSimpleParamOp(c: string): boolean {
  return c === "-" || c === "=" || c === "?" || c === "+";
}

function IsEscapeCharInBacktick(c: string): boolean {
  return c === "$" || c === "`" || c === "\\";
}

function IsNegationBoundary(c: string): boolean {
  return IsWhitespace(c) || c === ";" || c === "|" || c === ")" || c === "&" || c === ">" || c === "<";
}

function IsBackslashEscaped(value: string, idx: number): boolean {
  var bsCount: any = 0;
  var j: any = idx - 1;
  while (j >= 0 && (value[j] as unknown as string) === "\\") {
    bsCount += 1;
    j -= 1;
  }
  return bsCount % 2 === 1;
}

function IsDollarDollarParen(value: string, idx: number): boolean {
  var dollarCount: any = 0;
  var j: any = idx - 1;
  while (j >= 0 && (value[j] as unknown as string) === "$") {
    dollarCount += 1;
    j -= 1;
  }
  return dollarCount % 2 === 1;
}

function IsParen(c: string): boolean {
  return c === "(" || c === ")";
}

function IsCaretOrBang(c: string): boolean {
  return c === "!" || c === "^";
}

function IsAtOrStar(c: string): boolean {
  return c === "@" || c === "*";
}

function IsDigitOrDash(c: string): boolean {
  return IsDigit(c) || c === "-";
}

function IsNewlineOrRightParen(c: string): boolean {
  return c === "\n" || c === ")";
}

function IsSemicolonNewlineBrace(c: string): boolean {
  return c === ";" || c === "\n" || c === "{";
}

function LooksLikeAssignment(s: string): boolean {
  return Assignment(s, 0) !== -1;
}

function IsValidIdentifier(name: string): boolean {
  if (!(name !== "")) {
    return false;
  }
  if (!(/^[a-zA-Z]$/.test((name[0] as unknown as string)) || (name[0] as unknown as string) === "_")) {
    return false;
  }
  for (const c of name.slice(1)) {
    if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
      return false;
    }
  }
  return true;
}

function parse(source: string, extglob: boolean): Node[] {
  var parser: any = newParser(source, false, extglob);
  return parser.parse();
}

function newParseError(message: string, pos: number, line: number): ParseError {
  var self: any = new ParseError();
  self.message = message;
  self.pos = pos;
  self.line = line;
  return self;
}

function newMatchedPairError(message: string, pos: number, line: number): MatchedPairError {
  return new MatchedPairError();
}

function newQuoteState(): QuoteState {
  var self: any = new QuoteState();
  self.single = false;
  self.double = false;
  self.Stack = [];
  return self;
}

function newParseContext(kind: number): ParseContext {
  var self: any = new ParseContext();
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

function newContextStack(): ContextStack {
  var self: any = new ContextStack();
  self.Stack = [newParseContext(0)];
  return self;
}

function newLexer(source: string, extglob: boolean): Lexer {
  var self: any = new Lexer();
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

function newParser(source: string, inProcessSub: boolean, extglob: boolean): Parser {
  var self: any = new Parser();
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
declare var module: any;
if (typeof module !== 'undefined') {
  module.exports = { parse, ParseError };
}
