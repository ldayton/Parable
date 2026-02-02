// ignore_for_file: unnecessary_null_comparison
// ignore_for_file: unnecessary_non_null_assertion
// ignore_for_file: return_of_invalid_type
// ignore_for_file: argument_type_not_assignable
// ignore_for_file: invalid_assignment
// ignore_for_file: unchecked_use_of_nullable_value

import 'dart:io';
import 'dart:convert';

final Map<String, int> ansiCEscapes = <String, int>{"a": 7, "b": 8, "e": 27, "E": 27, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11, "\\": 92, "\"": 34, "?": 63};
const int tokentypeEof = 0;
const int tokentypeWord = 1;
const int tokentypeNewline = 2;
const int tokentypeSemi = 10;
const int tokentypePipe = 11;
const int tokentypeAmp = 12;
const int tokentypeLparen = 13;
const int tokentypeRparen = 14;
const int tokentypeLbrace = 15;
const int tokentypeRbrace = 16;
const int tokentypeLess = 17;
const int tokentypeGreater = 18;
const int tokentypeAndAnd = 30;
const int tokentypeOrOr = 31;
const int tokentypeSemiSemi = 32;
const int tokentypeSemiAmp = 33;
const int tokentypeSemiSemiAmp = 34;
const int tokentypeLessLess = 35;
const int tokentypeGreaterGreater = 36;
const int tokentypeLessAmp = 37;
const int tokentypeGreaterAmp = 38;
const int tokentypeLessGreater = 39;
const int tokentypeGreaterPipe = 40;
const int tokentypeLessLessMinus = 41;
const int tokentypeLessLessLess = 42;
const int tokentypeAmpGreater = 43;
const int tokentypeAmpGreaterGreater = 44;
const int tokentypePipeAmp = 45;
const int tokentypeIf = 50;
const int tokentypeThen = 51;
const int tokentypeElse = 52;
const int tokentypeElif = 53;
const int tokentypeFi = 54;
const int tokentypeCase = 55;
const int tokentypeEsac = 56;
const int tokentypeFor = 57;
const int tokentypeWhile = 58;
const int tokentypeUntil = 59;
const int tokentypeDo = 60;
const int tokentypeDone = 61;
const int tokentypeIn = 62;
const int tokentypeFunction = 63;
const int tokentypeSelect = 64;
const int tokentypeCoproc = 65;
const int tokentypeTime = 66;
const int tokentypeBang = 67;
const int tokentypeLbracketLbracket = 68;
const int tokentypeRbracketRbracket = 69;
const int tokentypeAssignmentWord = 80;
const int tokentypeNumber = 81;
const int parserstateflagsNone = 0;
const int parserstateflagsPstCasepat = 1;
const int parserstateflagsPstCmdsubst = 2;
const int parserstateflagsPstCasestmt = 4;
const int parserstateflagsPstCondexpr = 8;
const int parserstateflagsPstCompassign = 16;
const int parserstateflagsPstArith = 32;
const int parserstateflagsPstHeredoc = 64;
const int parserstateflagsPstRegexp = 128;
const int parserstateflagsPstExtpat = 256;
const int parserstateflagsPstSubshell = 512;
const int parserstateflagsPstRedirlist = 1024;
const int parserstateflagsPstComment = 2048;
const int parserstateflagsPstEoftoken = 4096;
const int dolbracestateNone = 0;
const int dolbracestateParam = 1;
const int dolbracestateOp = 2;
const int dolbracestateWord = 4;
const int dolbracestateQuote = 64;
const int dolbracestateQuote2 = 128;
const int matchedpairflagsNone = 0;
const int matchedpairflagsDquote = 1;
const int matchedpairflagsDolbrace = 2;
const int matchedpairflagsCommand = 4;
const int matchedpairflagsArith = 8;
const int matchedpairflagsAllowesc = 16;
const int matchedpairflagsExtglob = 32;
const int matchedpairflagsFirstclose = 64;
const int matchedpairflagsArraysub = 128;
const int matchedpairflagsBackquote = 256;
const int parsecontextNormal = 0;
const int parsecontextCommandSub = 1;
const int parsecontextArithmetic = 2;
const int parsecontextCasePattern = 3;
const int parsecontextBraceExpansion = 4;
final Set<String> reservedWords = <String>{"if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"};
final Set<String> condUnaryOps = <String>{"-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"};
final Set<String> condBinaryOps = <String>{"==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"};
final Set<String> compoundKeywords = <String>{"while", "until", "for", "if", "case", "select"};
final Set<String> assignmentBuiltins = <String>{"alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"};
const int _smpLiteral = 1;
const int _smpPastOpen = 2;
const int wordCtxNormal = 0;
const int wordCtxCond = 1;
const int wordCtxRegex = 2;

abstract class Node {
  String get kind;
  String getKind();
  String toSexp();
}

class ParseError implements Exception {
  late String message;
  late int pos;
  late int line;

  ParseError(String message, int pos, int line) {
    this.message = message;
    this.pos = pos;
    this.line = line;
  }

  String _formatMessage() {
    if (this.line != 0 && this.pos != 0) {
      return "Parse error at line ${this.line}, position ${this.pos}: ${this.message}";
    } else {
      if (this.pos != 0) {
        return "Parse error at position ${this.pos}: ${this.message}";
      }
    }
    return "Parse error: ${this.message}";
  }
}

class MatchedPairError extends ParseError {
  MatchedPairError(String message, int pos, int code) : super(message, pos, code);
}

class TokenType {
  TokenType();
}

class Token {
  late int type;
  late String value;
  late int pos;
  late List<Node> parts;
  Word? word;

  Token(int type, String value, int pos, List<Node> parts, Word? word) {
    this.type = type;
    this.value = value;
    this.pos = pos;
    this.parts = parts;
    this.word = word;
  }

  String _Repr() {
    if (this.word != null) {
      return "Token(${this.type}, ${this.value}, ${this.pos}, word=${this.word})";
    }
    if ((this.parts.isNotEmpty)) {
      return "Token(${this.type}, ${this.value}, ${this.pos}, parts=${this.parts.length})";
    }
    return "Token(${this.type}, ${this.value}, ${this.pos})";
  }
}

class ParserStateFlags {
  ParserStateFlags();
}

class DolbraceState {
  DolbraceState();
}

class MatchedPairFlags {
  MatchedPairFlags();
}

class SavedParserState {
  late int parserState;
  late int dolbraceState;
  late List<Node> pendingHeredocs;
  late List<ParseContext> ctxStack;
  late String eofToken;

  SavedParserState(int parserState, int dolbraceState, List<Node> pendingHeredocs, List<ParseContext> ctxStack, String eofToken) {
    this.parserState = parserState;
    this.dolbraceState = dolbraceState;
    this.pendingHeredocs = pendingHeredocs;
    this.ctxStack = ctxStack;
    this.eofToken = eofToken;
  }
}

class QuoteState {
  late bool single;
  late bool double;
  late List<(bool, bool)> _stack;

  QuoteState(bool single, bool double, List<(bool, bool)> _stack) {
    this.single = single;
    this.double = double;
    this._stack = _stack;
  }

  void push() {
    this._stack.add((this.single, this.double));
    this.single = false;
    this.double = false;
  }

  void pop() {
    if ((this._stack.isNotEmpty)) {
      final _entry1 = this._stack[this._stack.length - 1];
      this._stack.removeAt(this._stack.length - 1);
      this.single = _entry1.$1;
      this.double = _entry1.$2;
    }
  }

  bool inQuotes() {
    return this.single || this.double;
  }

  QuoteState copy() {
    dynamic qs = newQuoteState();
    qs.single = this.single;
    qs.double = this.double;
    qs._stack = List<(bool, bool)>.from(this._stack);
    return qs;
  }

  bool outerDouble() {
    if (this._stack.length == 0) {
      return false;
    }
    return this._stack[this._stack.length - 1].$2;
  }
}

class ParseContext {
  late int kind;
  late int parenDepth;
  late int braceDepth;
  late int bracketDepth;
  late int caseDepth;
  late int arithDepth;
  late int arithParenDepth;
  late QuoteState quote;

  ParseContext(int kind, int parenDepth, int braceDepth, int bracketDepth, int caseDepth, int arithDepth, int arithParenDepth, QuoteState? quote) {
    this.kind = kind;
    this.parenDepth = parenDepth;
    this.braceDepth = braceDepth;
    this.bracketDepth = bracketDepth;
    this.caseDepth = caseDepth;
    this.arithDepth = arithDepth;
    this.arithParenDepth = arithParenDepth;
    if (quote != null) this.quote = quote;
  }

  ParseContext copy() {
    dynamic ctx = newParseContext(this.kind);
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
  late List<ParseContext> _stack;

  ContextStack(List<ParseContext> _stack) {
    this._stack = _stack;
  }

  ParseContext getCurrent() {
    return this._stack[this._stack.length - 1];
  }

  void push(int kind) {
    this._stack.add(newParseContext(kind));
  }

  ParseContext pop() {
    if (this._stack.length > 1) {
      return this._stack.removeLast();
    }
    return this._stack[0];
  }

  List<ParseContext> copyStack() {
    List<ParseContext> result = <ParseContext>[]; 
    for (final ctx in this._stack) {
      result.add(ctx.copy());
    }
    return result;
  }

  void restoreFrom(List<ParseContext> savedStack) {
    List<ParseContext> result = <ParseContext>[]; 
    for (final ctx in savedStack) {
      result.add(ctx.copy());
    }
    this._stack = result;
  }
}

class Lexer {
  late Map<String, int> reservedWords;
  late String source;
  late int pos;
  late int length;
  late QuoteState quote;
  Token? _tokenCache;
  late int _parserState;
  late int _dolbraceState;
  late List<Node> _pendingHeredocs;
  late bool _extglob;
  Parser? _parser;
  late String _eofToken;
  Token? _lastReadToken;
  late int _wordContext;
  late bool _atCommandStart;
  late bool _inArrayLiteral;
  late bool _inAssignBuiltin;
  late int _postReadPos;
  late int _cachedWordContext;
  late bool _cachedAtCommandStart;
  late bool _cachedInArrayLiteral;
  late bool _cachedInAssignBuiltin;

  Lexer(Map<String, int> reservedWords, String source, int pos, int length, QuoteState? quote, Token? _tokenCache, int _parserState, int _dolbraceState, List<Node> _pendingHeredocs, bool _extglob, Parser? _parser, String _eofToken, Token? _lastReadToken, int _wordContext, bool _atCommandStart, bool _inArrayLiteral, bool _inAssignBuiltin, int _postReadPos, int _cachedWordContext, bool _cachedAtCommandStart, bool _cachedInArrayLiteral, bool _cachedInAssignBuiltin) {
    this.reservedWords = reservedWords;
    this.source = source;
    this.pos = pos;
    this.length = length;
    if (quote != null) this.quote = quote;
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

  String peek() {
    if (this.pos >= this.length) {
      return "";
    }
    return (this.source[this.pos]).toString();
  }

  String advance() {
    if (this.pos >= this.length) {
      return "";
    }
    String c = (this.source[this.pos]).toString(); 
    this.pos += 1;
    return c;
  }

  bool atEnd() {
    return this.pos >= this.length;
  }

  String lookahead(int n) {
    return _substring(this.source, this.pos, this.pos + n);
  }

  bool isMetachar(String c) {
    return "|&;()<> \t\n".contains(c);
  }

  dynamic _readOperator() {
    int start = this.pos; 
    String c = this.peek(); 
    if (c == "") {
      return null as dynamic;
    }
    String two = this.lookahead(2); 
    String three = this.lookahead(3); 
    if (three == ";;&") {
      this.pos += 3;
      return Token(tokentypeSemiSemiAmp, three, start, <Node>[], null);
    }
    if (three == "<<-") {
      this.pos += 3;
      return Token(tokentypeLessLessMinus, three, start, <Node>[], null);
    }
    if (three == "<<<") {
      this.pos += 3;
      return Token(tokentypeLessLessLess, three, start, <Node>[], null);
    }
    if (three == "&>>") {
      this.pos += 3;
      return Token(tokentypeAmpGreaterGreater, three, start, <Node>[], null);
    }
    if (two == "&&") {
      this.pos += 2;
      return Token(tokentypeAndAnd, two, start, <Node>[], null);
    }
    if (two == "||") {
      this.pos += 2;
      return Token(tokentypeOrOr, two, start, <Node>[], null);
    }
    if (two == ";;") {
      this.pos += 2;
      return Token(tokentypeSemiSemi, two, start, <Node>[], null);
    }
    if (two == ";&") {
      this.pos += 2;
      return Token(tokentypeSemiAmp, two, start, <Node>[], null);
    }
    if (two == "<<") {
      this.pos += 2;
      return Token(tokentypeLessLess, two, start, <Node>[], null);
    }
    if (two == ">>") {
      this.pos += 2;
      return Token(tokentypeGreaterGreater, two, start, <Node>[], null);
    }
    if (two == "<&") {
      this.pos += 2;
      return Token(tokentypeLessAmp, two, start, <Node>[], null);
    }
    if (two == ">&") {
      this.pos += 2;
      return Token(tokentypeGreaterAmp, two, start, <Node>[], null);
    }
    if (two == "<>") {
      this.pos += 2;
      return Token(tokentypeLessGreater, two, start, <Node>[], null);
    }
    if (two == ">|") {
      this.pos += 2;
      return Token(tokentypeGreaterPipe, two, start, <Node>[], null);
    }
    if (two == "&>") {
      this.pos += 2;
      return Token(tokentypeAmpGreater, two, start, <Node>[], null);
    }
    if (two == "|&") {
      this.pos += 2;
      return Token(tokentypePipeAmp, two, start, <Node>[], null);
    }
    if (c == ";") {
      this.pos += 1;
      return Token(tokentypeSemi, c, start, <Node>[], null);
    }
    if (c == "|") {
      this.pos += 1;
      return Token(tokentypePipe, c, start, <Node>[], null);
    }
    if (c == "&") {
      this.pos += 1;
      return Token(tokentypeAmp, c, start, <Node>[], null);
    }
    if (c == "(") {
      if (this._wordContext == wordCtxRegex) {
        return null as dynamic;
      }
      this.pos += 1;
      return Token(tokentypeLparen, c, start, <Node>[], null);
    }
    if (c == ")") {
      if (this._wordContext == wordCtxRegex) {
        return null as dynamic;
      }
      this.pos += 1;
      return Token(tokentypeRparen, c, start, <Node>[], null);
    }
    if (c == "<") {
      if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
        return null as dynamic;
      }
      this.pos += 1;
      return Token(tokentypeLess, c, start, <Node>[], null);
    }
    if (c == ">") {
      if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
        return null as dynamic;
      }
      this.pos += 1;
      return Token(tokentypeGreater, c, start, <Node>[], null);
    }
    if (c == "\n") {
      this.pos += 1;
      return Token(tokentypeNewline, c, start, <Node>[], null);
    }
    return null as dynamic;
  }

  void skipBlanks() {
    while (this.pos < this.length) {
      String c = (this.source[this.pos]).toString(); 
      if (c != " " && c != "\t") {
        break;
      }
      this.pos += 1;
    }
  }

  bool _skipComment() {
    if (this.pos >= this.length) {
      return false;
    }
    if ((this.source[this.pos]).toString() != "#") {
      return false;
    }
    if (this.quote.inQuotes()) {
      return false;
    }
    if (this.pos > 0) {
      String prev = (this.source[this.pos - 1]).toString(); 
      if (!" \t\n;|&(){}".contains(prev)) {
        return false;
      }
    }
    while (this.pos < this.length && (this.source[this.pos]).toString() != "\n") {
      this.pos += 1;
    }
    return true;
  }

  (String, bool) _readSingleQuote(int start) {
    List<String> chars = <String>["'"]; 
    bool sawNewline = false; 
    while (this.pos < this.length) {
      String c = (this.source[this.pos]).toString(); 
      if (c == "\n") {
        sawNewline = true;
      }
      chars.add(c);
      this.pos += 1;
      if (c == "'") {
        return (chars.join(""), sawNewline);
      }
    }
    throw ParseError("Unterminated single quote", start, 0);
  }

  bool _isWordTerminator(int ctx, String ch, int bracketDepth, int parenDepth) {
    if (ctx == wordCtxRegex) {
      if (ch == "]" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "]") {
        return true;
      }
      if (ch == "&" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "&") {
        return true;
      }
      if (ch == ")" && parenDepth == 0) {
        return true;
      }
      return _isWhitespace(ch) && parenDepth == 0;
    }
    if (ctx == wordCtxCond) {
      if (ch == "]" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "]") {
        return true;
      }
      if (ch == ")") {
        return true;
      }
      if (ch == "&") {
        return true;
      }
      if (ch == "|") {
        return true;
      }
      if (ch == ";") {
        return true;
      }
      if (_isRedirectChar(ch) && !(this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(")) {
        return true;
      }
      return _isWhitespace(ch);
    }
    if ((this._parserState & parserstateflagsPstEoftoken != 0) && this._eofToken != "" && ch == this._eofToken && bracketDepth == 0) {
      return true;
    }
    if (_isRedirectChar(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
      return false;
    }
    return _isMetachar(ch) && bracketDepth == 0;
  }

  bool _readBracketExpression(List<String> chars, List<Node> parts, bool forRegex, int parenDepth) {
    if (forRegex) {
      int scan = this.pos + 1; 
      if (scan < this.length && (this.source[scan]).toString() == "^") {
        scan += 1;
      }
      if (scan < this.length && (this.source[scan]).toString() == "]") {
        scan += 1;
      }
      bool bracketWillClose = false; 
      while (scan < this.length) {
        String sc = (this.source[scan]).toString(); 
        if (sc == "]" && scan + 1 < this.length && (this.source[scan + 1]).toString() == "]") {
          break;
        }
        if (sc == ")" && parenDepth > 0) {
          break;
        }
        if (sc == "&" && scan + 1 < this.length && (this.source[scan + 1]).toString() == "&") {
          break;
        }
        if (sc == "]") {
          bracketWillClose = true;
          break;
        }
        if (sc == "[" && scan + 1 < this.length && (this.source[scan + 1]).toString() == ":") {
          scan += 2;
          while (scan < this.length && !((this.source[scan]).toString() == ":" && scan + 1 < this.length && (this.source[scan + 1]).toString() == "]")) {
            scan += 1;
          }
          if (scan < this.length) {
            scan += 2;
          }
          continue;
        }
        scan += 1;
      }
      if (!(bracketWillClose)) {
        return false;
      }
    } else {
      if (this.pos + 1 >= this.length) {
        return false;
      }
      String nextCh = (this.source[this.pos + 1]).toString(); 
      if (_isWhitespaceNoNewline(nextCh) || nextCh == "&" || nextCh == "|") {
        return false;
      }
    }
    chars.add(this.advance());
    if (!(this.atEnd()) && this.peek() == "^") {
      chars.add(this.advance());
    }
    if (!(this.atEnd()) && this.peek() == "]") {
      chars.add(this.advance());
    }
    while (!(this.atEnd())) {
      String c = this.peek(); 
      if (c == "]") {
        chars.add(this.advance());
        break;
      }
      if (c == "[" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == ":") {
        chars.add(this.advance());
        chars.add(this.advance());
        while (!(this.atEnd()) && !(this.peek() == ":" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "]")) {
          chars.add(this.advance());
        }
        if (!(this.atEnd())) {
          chars.add(this.advance());
          chars.add(this.advance());
        }
      } else {
        if (!(forRegex) && c == "[" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "=") {
          chars.add(this.advance());
          chars.add(this.advance());
          while (!(this.atEnd()) && !(this.peek() == "=" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "]")) {
            chars.add(this.advance());
          }
          if (!(this.atEnd())) {
            chars.add(this.advance());
            chars.add(this.advance());
          }
        } else {
          if (!(forRegex) && c == "[" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == ".") {
            chars.add(this.advance());
            chars.add(this.advance());
            while (!(this.atEnd()) && !(this.peek() == "." && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "]")) {
              chars.add(this.advance());
            }
            if (!(this.atEnd())) {
              chars.add(this.advance());
              chars.add(this.advance());
            }
          } else {
            if (forRegex && c == "\$") {
              this._syncToParser();
              if (!(this._parser!._parseDollarExpansion(chars, parts, false))) {
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

  String _parseMatchedPair(String openChar, String closeChar, int flags, bool initialWasDollar) {
    int start = this.pos; 
    int count = 1; 
    List<String> chars = <String>[]; 
    bool passNext = false; 
    bool wasDollar = initialWasDollar; 
    bool wasGtlt = false; 
    while (count > 0) {
      if (this.atEnd()) {
        throw MatchedPairError("unexpected EOF while looking for matching `${closeChar}'", start, 0);
      }
      String ch = this.advance(); 
      if ((flags & matchedpairflagsDolbrace != 0) && this._dolbraceState == dolbracestateOp) {
        if (!"#%^,~:-=?+/".contains(ch)) {
          this._dolbraceState = dolbracestateWord;
        }
      }
      if (passNext) {
        passNext = false;
        chars.add(ch);
        wasDollar = ch == "\$";
        wasGtlt = "<>".contains(ch);
        continue;
      }
      if (openChar == "'") {
        if (ch == closeChar) {
          count -= 1;
          if (count == 0) {
            break;
          }
        }
        if (ch == "\\" && (flags & matchedpairflagsAllowesc != 0)) {
          passNext = true;
        }
        chars.add(ch);
        wasDollar = false;
        wasGtlt = false;
        continue;
      }
      if (ch == "\\") {
        if (!(this.atEnd()) && this.peek() == "\n") {
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
      if (ch == closeChar) {
        count -= 1;
        if (count == 0) {
          break;
        }
        chars.add(ch);
        wasDollar = false;
        wasGtlt = "<>".contains(ch);
        continue;
      }
      if (ch == openChar && openChar != closeChar) {
        if (!((flags & matchedpairflagsDolbrace != 0) && openChar == "{")) {
          count += 1;
        }
        chars.add(ch);
        wasDollar = false;
        wasGtlt = "<>".contains(ch);
        continue;
      }
      if ("'\"`".contains(ch) && openChar != closeChar) {
        String nested = "";
        if (ch == "'") {
          chars.add(ch);
          int quoteFlags = (wasDollar ? flags | matchedpairflagsAllowesc : flags); 
          nested = this._parseMatchedPair("'", "'", quoteFlags, false);
          chars.add(nested);
          chars.add("'");
          wasDollar = false;
          wasGtlt = false;
          continue;
        } else {
          if (ch == "\"") {
            chars.add(ch);
            nested = this._parseMatchedPair("\"", "\"", flags | matchedpairflagsDquote, false);
            chars.add(nested);
            chars.add("\"");
            wasDollar = false;
            wasGtlt = false;
            continue;
          } else {
            if (ch == "`") {
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
      if (ch == "\$" && !(this.atEnd()) && !((flags & matchedpairflagsExtglob != 0))) {
        String nextCh = this.peek(); 
        if (wasDollar) {
          chars.add(ch);
          wasDollar = false;
          wasGtlt = false;
          continue;
        }
        if (nextCh == "{") {
          if ((flags & matchedpairflagsArith != 0)) {
            int afterBracePos = this.pos + 1; 
            if (afterBracePos >= this.length || !(_isFunsubChar((this.source[afterBracePos]).toString()))) {
              chars.add(ch);
              wasDollar = true;
              wasGtlt = false;
              continue;
            }
          }
          this.pos -= 1;
          this._syncToParser();
          bool inDquote = flags & matchedpairflagsDquote != 0; 
          final _tuple2 = this._parser!._parseParamExpansion(inDquote);
          Node? paramNode = _tuple2.$1;
          String paramText = _tuple2.$2;
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
          dynamic arithNode;
          String arithText = "";
          if (nextCh == "(") {
            this.pos -= 1;
            this._syncToParser();
            dynamic cmdNode;
            String cmdText = "";
            if (this.pos + 2 < this.length && (this.source[this.pos + 2]).toString() == "(") {
              final _tuple3 = this._parser!._parseArithmeticExpansion();
              arithNode = _tuple3.$1;
              arithText = _tuple3.$2;
              this._syncFromParser();
              if (arithNode != null) {
                chars.add(arithText);
                wasDollar = false;
                wasGtlt = false;
              } else {
                this._syncToParser();
                final _tuple4 = this._parser!._parseCommandSubstitution();
                cmdNode = _tuple4.$1;
                cmdText = _tuple4.$2;
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
              final _tuple5 = this._parser!._parseCommandSubstitution();
              cmdNode = _tuple5.$1;
              cmdText = _tuple5.$2;
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
            if (nextCh == "[") {
              this.pos -= 1;
              this._syncToParser();
              final _tuple6 = this._parser!._parseDeprecatedArithmetic();
              arithNode = _tuple6.$1;
              arithText = _tuple6.$2;
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
      if (ch == "(" && wasGtlt && (flags & matchedpairflagsDolbrace | matchedpairflagsArraysub != 0)) {
        String direction = chars[chars.length - 1]; 
        chars = chars.sublist(0, chars.length - 1);
        this.pos -= 1;
        this._syncToParser();
        final _tuple7 = this._parser!._parseProcessSubstitution();
        Node? procsubNode = _tuple7.$1;
        String procsubText = _tuple7.$2;
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
      wasDollar = ch == "\$";
      wasGtlt = "<>".contains(ch);
    }
    return chars.join("");
  }

  String _collectParamArgument(int flags, bool wasDollar) {
    return this._parseMatchedPair("{", "}", flags | matchedpairflagsDolbrace, wasDollar);
  }

  dynamic _readWordInternal(int ctx, bool atCommandStart, bool inArrayLiteral, bool inAssignBuiltin) {
    int start = this.pos; 
    List<String> chars = <String>[]; 
    List<Node> parts = <Node>[]; 
    int bracketDepth = 0; 
    int bracketStartPos = -1; 
    bool seenEquals = false; 
    int parenDepth = 0; 
    while (!(this.atEnd())) {
      String ch = this.peek(); 
      if (ctx == wordCtxRegex) {
        if (ch == "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "\n") {
          this.advance();
          this.advance();
          continue;
        }
      }
      if (ctx != wordCtxNormal && this._isWordTerminator(ctx, ch, bracketDepth, parenDepth)) {
        break;
      }
      if (ctx == wordCtxNormal && ch == "[") {
        if (bracketDepth > 0) {
          bracketDepth += 1;
          chars.add(this.advance());
          continue;
        }
        if ((chars.isNotEmpty) && atCommandStart && !(seenEquals) && _isArrayAssignmentPrefix(chars)) {
          String prevChar = chars[chars.length - 1]; 
          if ((prevChar.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(prevChar)) || prevChar == "_") {
            bracketStartPos = this.pos;
            bracketDepth += 1;
            chars.add(this.advance());
            continue;
          }
        }
        if (!((chars.isNotEmpty)) && !(seenEquals) && inArrayLiteral) {
          bracketStartPos = this.pos;
          bracketDepth += 1;
          chars.add(this.advance());
          continue;
        }
      }
      if (ctx == wordCtxNormal && ch == "]" && bracketDepth > 0) {
        bracketDepth -= 1;
        chars.add(this.advance());
        continue;
      }
      if (ctx == wordCtxNormal && ch == "=" && bracketDepth == 0) {
        seenEquals = true;
      }
      if (ctx == wordCtxRegex && ch == "(") {
        parenDepth += 1;
        chars.add(this.advance());
        continue;
      }
      if (ctx == wordCtxRegex && ch == ")") {
        if (parenDepth > 0) {
          parenDepth -= 1;
          chars.add(this.advance());
          continue;
        }
        break;
      }
      if ((ctx == wordCtxCond || ctx == wordCtxRegex) && ch == "[") {
        bool forRegex = ctx == wordCtxRegex; 
        if (this._readBracketExpression(chars, parts, forRegex, parenDepth)) {
          continue;
        }
        chars.add(this.advance());
        continue;
      }
      String content = "";
      if (ctx == wordCtxCond && ch == "(") {
        if (this._extglob && (chars.isNotEmpty) && _isExtglobPrefix(chars[chars.length - 1])) {
          chars.add(this.advance());
          content = this._parseMatchedPair("(", ")", matchedpairflagsExtglob, false);
          chars.add(content);
          chars.add(")");
          continue;
        } else {
          break;
        }
      }
      if (ctx == wordCtxRegex && _isWhitespace(ch) && parenDepth > 0) {
        chars.add(this.advance());
        continue;
      }
      if (ch == "'") {
        this.advance();
        bool trackNewline = ctx == wordCtxNormal; 
        final _tuple8 = this._readSingleQuote(start);
        content = _tuple8.$1;
        bool sawNewline = _tuple8.$2;
        chars.add(content);
        if (trackNewline && sawNewline && this._parser != null) {
          this._parser!._sawNewlineInSingleQuote = true;
        }
        continue;
      }
      dynamic cmdsubResult0;
      String cmdsubResult1 = "";
      if (ch == "\"") {
        this.advance();
        if (ctx == wordCtxNormal) {
          chars.add("\"");
          bool inSingleInDquote = false; 
          while (!(this.atEnd()) && (inSingleInDquote || this.peek() != "\"")) {
            String c = this.peek(); 
            if (inSingleInDquote) {
              chars.add(this.advance());
              if (c == "'") {
                inSingleInDquote = false;
              }
              continue;
            }
            if (c == "\\" && this.pos + 1 < this.length) {
              String nextC = (this.source[this.pos + 1]).toString(); 
              if (nextC == "\n") {
                this.advance();
                this.advance();
              } else {
                chars.add(this.advance());
                chars.add(this.advance());
              }
            } else {
              if (c == "\$") {
                this._syncToParser();
                if (!(this._parser!._parseDollarExpansion(chars, parts, true))) {
                  this._syncFromParser();
                  chars.add(this.advance());
                } else {
                  this._syncFromParser();
                }
              } else {
                if (c == "`") {
                  this._syncToParser();
                  final _tuple9 = this._parser!._parseBacktickSubstitution();
                  cmdsubResult0 = _tuple9.$1;
                  cmdsubResult1 = _tuple9.$2;
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
            throw ParseError("Unterminated double quote", start, 0);
          }
          chars.add(this.advance());
        } else {
          bool handleLineContinuation = ctx == wordCtxCond; 
          this._syncToParser();
          this._parser!._scanDoubleQuote(chars, parts, start, handleLineContinuation);
          this._syncFromParser();
        }
        continue;
      }
      if (ch == "\\" && this.pos + 1 < this.length) {
        String nextCh = (this.source[this.pos + 1]).toString(); 
        if (ctx != wordCtxRegex && nextCh == "\n") {
          this.advance();
          this.advance();
        } else {
          chars.add(this.advance());
          chars.add(this.advance());
        }
        continue;
      }
      if (ctx != wordCtxRegex && ch == "\$" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "'") {
        final _tuple10 = this._readAnsiCQuote();
        Node? ansiResult0 = _tuple10.$1;
        String ansiResult1 = _tuple10.$2;
        if (ansiResult0 != null) {
          parts.add(ansiResult0);
          chars.add(ansiResult1);
        } else {
          chars.add(this.advance());
        }
        continue;
      }
      if (ctx != wordCtxRegex && ch == "\$" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "\"") {
        final _tuple11 = this._readLocaleString();
        Node? localeResult0 = _tuple11.$1;
        String localeResult1 = _tuple11.$2;
        List<Node> localeResult2 = _tuple11.$3;
        if (localeResult0 != null) {
          parts.add(localeResult0);
          parts.addAll(localeResult2);
          chars.add(localeResult1);
        } else {
          chars.add(this.advance());
        }
        continue;
      }
      if (ch == "\$") {
        this._syncToParser();
        if (!(this._parser!._parseDollarExpansion(chars, parts, false))) {
          this._syncFromParser();
          chars.add(this.advance());
        } else {
          this._syncFromParser();
          if (this._extglob && ctx == wordCtxNormal && (chars.isNotEmpty) && chars[chars.length - 1].length == 2 && (chars[chars.length - 1][0]).toString() == "\$" && "?*@".contains((chars[chars.length - 1][1]).toString()) && !(this.atEnd()) && this.peek() == "(") {
            chars.add(this.advance());
            content = this._parseMatchedPair("(", ")", matchedpairflagsExtglob, false);
            chars.add(content);
            chars.add(")");
          }
        }
        continue;
      }
      if (ctx != wordCtxRegex && ch == "`") {
        this._syncToParser();
        final _tuple12 = this._parser!._parseBacktickSubstitution();
        cmdsubResult0 = _tuple12.$1;
        cmdsubResult1 = _tuple12.$2;
        this._syncFromParser();
        if (cmdsubResult0 != null) {
          parts.add(cmdsubResult0);
          chars.add(cmdsubResult1);
        } else {
          chars.add(this.advance());
        }
        continue;
      }
      if (ctx != wordCtxRegex && _isRedirectChar(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
        this._syncToParser();
        final _tuple13 = this._parser!._parseProcessSubstitution();
        Node? procsubResult0 = _tuple13.$1;
        String procsubResult1 = _tuple13.$2;
        this._syncFromParser();
        if (procsubResult0 != null) {
          parts.add(procsubResult0);
          chars.add(procsubResult1);
        } else {
          if ((procsubResult1.isNotEmpty)) {
            chars.add(procsubResult1);
          } else {
            chars.add(this.advance());
            if (ctx == wordCtxNormal) {
              chars.add(this.advance());
            }
          }
        }
        continue;
      }
      if (ctx == wordCtxNormal && ch == "(" && (chars.isNotEmpty) && bracketDepth == 0) {
        bool isArrayAssign = false; 
        if (chars.length >= 3 && chars[chars.length - 2] == "+" && chars[chars.length - 1] == "=") {
          isArrayAssign = _isArrayAssignmentPrefix(chars.sublist(0, chars.length - 2));
        } else {
          if (chars[chars.length - 1] == "=" && chars.length >= 2) {
            isArrayAssign = _isArrayAssignmentPrefix(chars.sublist(0, chars.length - 1));
          }
        }
        if (isArrayAssign && (atCommandStart || inAssignBuiltin)) {
          this._syncToParser();
          final _tuple14 = this._parser!._parseArrayLiteral();
          Node? arrayResult0 = _tuple14.$1;
          String arrayResult1 = _tuple14.$2;
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
      if (this._extglob && ctx == wordCtxNormal && _isExtglobPrefix(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
        chars.add(this.advance());
        chars.add(this.advance());
        content = this._parseMatchedPair("(", ")", matchedpairflagsExtglob, false);
        chars.add(content);
        chars.add(")");
        continue;
      }
      if (ctx == wordCtxNormal && (this._parserState & parserstateflagsPstEoftoken != 0) && this._eofToken != "" && ch == this._eofToken && bracketDepth == 0) {
        if (!((chars.isNotEmpty))) {
          chars.add(this.advance());
        }
        break;
      }
      if (ctx == wordCtxNormal && _isMetachar(ch) && bracketDepth == 0) {
        break;
      }
      chars.add(this.advance());
    }
    if (bracketDepth > 0 && bracketStartPos != -1 && this.atEnd()) {
      throw MatchedPairError("unexpected EOF looking for `]'", bracketStartPos, 0);
    }
    if (!((chars.isNotEmpty))) {
      return null as dynamic;
    }
    if ((parts.isNotEmpty)) {
      return Word(chars.join(""), parts, "word");
    }
    return Word(chars.join(""), <Node>[], "word");
  }

  dynamic _readWord() {
    int start = this.pos; 
    if (this.pos >= this.length) {
      return null as dynamic;
    }
    String c = this.peek(); 
    if (c == "") {
      return null as dynamic;
    }
    bool isProcsub = (c == "<" || c == ">") && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "("; 
    bool isRegexParen = this._wordContext == wordCtxRegex && (c == "(" || c == ")"); 
    if (this.isMetachar(c) && !(isProcsub) && !(isRegexParen)) {
      return null as dynamic;
    }
    dynamic word = this._readWordInternal(this._wordContext, this._atCommandStart, this._inArrayLiteral, this._inAssignBuiltin);
    if (word == null) {
      return null as dynamic;
    }
    return Token(tokentypeWord, word.value, start, <Node>[], word);
  }

  Token nextToken() {
    dynamic tok;
    if (this._tokenCache != null) {
      tok = this._tokenCache!;
      this._tokenCache = null as dynamic;
      this._lastReadToken = tok;
      return tok!;
    }
    this.skipBlanks();
    if (this.atEnd()) {
      tok = Token(tokentypeEof, "", this.pos, <Node>[], null);
      this._lastReadToken = tok;
      return tok!;
    }
    if (this._eofToken != "" && this.peek() == this._eofToken && !((this._parserState & parserstateflagsPstCasepat != 0)) && !((this._parserState & parserstateflagsPstEoftoken != 0))) {
      tok = Token(tokentypeEof, "", this.pos, <Node>[], null);
      this._lastReadToken = tok;
      return tok!;
    }
    while (this._skipComment()) {
      this.skipBlanks();
      if (this.atEnd()) {
        tok = Token(tokentypeEof, "", this.pos, <Node>[], null);
        this._lastReadToken = tok;
        return tok!;
      }
      if (this._eofToken != "" && this.peek() == this._eofToken && !((this._parserState & parserstateflagsPstCasepat != 0)) && !((this._parserState & parserstateflagsPstEoftoken != 0))) {
        tok = Token(tokentypeEof, "", this.pos, <Node>[], null);
        this._lastReadToken = tok;
        return tok!;
      }
    }
    tok = this._readOperator();
    if (tok != null) {
      this._lastReadToken = tok;
      return tok!;
    }
    tok = this._readWord();
    if (tok != null) {
      this._lastReadToken = tok;
      return tok!;
    }
    tok = Token(tokentypeEof, "", this.pos, <Node>[], null);
    this._lastReadToken = tok;
    return tok!;
  }

  Token peekToken() {
    if (this._tokenCache == null) {
      Token? savedLast = this._lastReadToken; 
      this._tokenCache = this.nextToken();
      this._lastReadToken = savedLast;
    }
    return this._tokenCache!;
  }

  (Node?, String) _readAnsiCQuote() {
    if (this.atEnd() || this.peek() != "\$") {
      return (null, "");
    }
    if (this.pos + 1 >= this.length || (this.source[this.pos + 1]).toString() != "'") {
      return (null, "");
    }
    int start = this.pos; 
    this.advance();
    this.advance();
    List<String> contentChars = <String>[]; 
    bool foundClose = false; 
    while (!(this.atEnd())) {
      String ch = this.peek(); 
      if (ch == "'") {
        this.advance();
        foundClose = true;
        break;
      } else {
        if (ch == "\\") {
          contentChars.add(this.advance());
          if (!(this.atEnd())) {
            contentChars.add(this.advance());
          }
        } else {
          contentChars.add(this.advance());
        }
      }
    }
    if (!(foundClose)) {
      throw MatchedPairError("unexpected EOF while looking for matching `''", start, 0);
    }
    String text = _substring(this.source, start, this.pos); 
    String content = contentChars.join(""); 
    AnsiCQuote node = AnsiCQuote(content, "ansi-c"); 
    return (node, text);
  }

  void _syncToParser() {
    if (this._parser != null) {
      this._parser!.pos = this.pos;
    }
  }

  void _syncFromParser() {
    if (this._parser != null) {
      this.pos = this._parser!.pos;
    }
  }

  (Node?, String, List<Node>) _readLocaleString() {
    if (this.atEnd() || this.peek() != "\$") {
      return (null, "", <Node>[]);
    }
    if (this.pos + 1 >= this.length || (this.source[this.pos + 1]).toString() != "\"") {
      return (null, "", <Node>[]);
    }
    int start = this.pos; 
    this.advance();
    this.advance();
    List<String> contentChars = <String>[]; 
    List<Node> innerParts = <Node>[]; 
    bool foundClose = false; 
    while (!(this.atEnd())) {
      String ch = this.peek(); 
      if (ch == "\"") {
        this.advance();
        foundClose = true;
        break;
      } else {
        if (ch == "\\" && this.pos + 1 < this.length) {
          String nextCh = (this.source[this.pos + 1]).toString(); 
          if (nextCh == "\n") {
            this.advance();
            this.advance();
          } else {
            contentChars.add(this.advance());
            contentChars.add(this.advance());
          }
        } else {
          dynamic cmdsubNode;
          String cmdsubText = "";
          if (ch == "\$" && this.pos + 2 < this.length && (this.source[this.pos + 1]).toString() == "(" && (this.source[this.pos + 2]).toString() == "(") {
            this._syncToParser();
            final _tuple15 = this._parser!._parseArithmeticExpansion();
            Node? arithNode = _tuple15.$1;
            String arithText = _tuple15.$2;
            this._syncFromParser();
            if (arithNode != null) {
              innerParts.add(arithNode);
              contentChars.add(arithText);
            } else {
              this._syncToParser();
              final _tuple16 = this._parser!._parseCommandSubstitution();
              cmdsubNode = _tuple16.$1;
              cmdsubText = _tuple16.$2;
              this._syncFromParser();
              if (cmdsubNode != null) {
                innerParts.add(cmdsubNode);
                contentChars.add(cmdsubText);
              } else {
                contentChars.add(this.advance());
              }
            }
          } else {
            if (_isExpansionStart(this.source, this.pos, "\$(")) {
              this._syncToParser();
              final _tuple17 = this._parser!._parseCommandSubstitution();
              cmdsubNode = _tuple17.$1;
              cmdsubText = _tuple17.$2;
              this._syncFromParser();
              if (cmdsubNode != null) {
                innerParts.add(cmdsubNode);
                contentChars.add(cmdsubText);
              } else {
                contentChars.add(this.advance());
              }
            } else {
              if (ch == "\$") {
                this._syncToParser();
                final _tuple18 = this._parser!._parseParamExpansion(false);
                Node? paramNode = _tuple18.$1;
                String paramText = _tuple18.$2;
                this._syncFromParser();
                if (paramNode != null) {
                  innerParts.add(paramNode);
                  contentChars.add(paramText);
                } else {
                  contentChars.add(this.advance());
                }
              } else {
                if (ch == "`") {
                  this._syncToParser();
                  final _tuple19 = this._parser!._parseBacktickSubstitution();
                  cmdsubNode = _tuple19.$1;
                  cmdsubText = _tuple19.$2;
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
    if (!(foundClose)) {
      this.pos = start;
      return (null, "", <Node>[]);
    }
    String content = contentChars.join(""); 
    String text = "\$\"" + content + "\""; 
    return (LocaleString(content, "locale"), text, innerParts);
  }

  void _updateDolbraceForOp(String op, bool hasParam) {
    if (this._dolbraceState == dolbracestateNone) {
      return;
    }
    if (op == "" || op.length == 0) {
      return;
    }
    String firstChar = (op[0]).toString(); 
    if (this._dolbraceState == dolbracestateParam && hasParam) {
      if ("%#^,".contains(firstChar)) {
        this._dolbraceState = dolbracestateQuote;
        return;
      }
      if (firstChar == "/") {
        this._dolbraceState = dolbracestateQuote2;
        return;
      }
    }
    if (this._dolbraceState == dolbracestateParam) {
      if ("#%^,~:-=?+/".contains(firstChar)) {
        this._dolbraceState = dolbracestateOp;
      }
    }
  }

  String _consumeParamOperator() {
    if (this.atEnd()) {
      return "";
    }
    String ch = this.peek(); 
    String nextCh = "";
    if (ch == ":") {
      this.advance();
      if (this.atEnd()) {
        return ":";
      }
      nextCh = this.peek();
      if (_isSimpleParamOp(nextCh)) {
        this.advance();
        return ":" + nextCh;
      }
      return ":";
    }
    if (_isSimpleParamOp(ch)) {
      this.advance();
      return ch;
    }
    if (ch == "#") {
      this.advance();
      if (!(this.atEnd()) && this.peek() == "#") {
        this.advance();
        return "##";
      }
      return "#";
    }
    if (ch == "%") {
      this.advance();
      if (!(this.atEnd()) && this.peek() == "%") {
        this.advance();
        return "%%";
      }
      return "%";
    }
    if (ch == "/") {
      this.advance();
      if (!(this.atEnd())) {
        nextCh = this.peek();
        if (nextCh == "/") {
          this.advance();
          return "//";
        } else {
          if (nextCh == "#") {
            this.advance();
            return "/#";
          } else {
            if (nextCh == "%") {
              this.advance();
              return "/%";
            }
          }
        }
      }
      return "/";
    }
    if (ch == "^") {
      this.advance();
      if (!(this.atEnd()) && this.peek() == "^") {
        this.advance();
        return "^^";
      }
      return "^";
    }
    if (ch == ",") {
      this.advance();
      if (!(this.atEnd()) && this.peek() == ",") {
        this.advance();
        return ",,";
      }
      return ",";
    }
    if (ch == "@") {
      this.advance();
      return "@";
    }
    return "";
  }

  bool _paramSubscriptHasClose(int startPos) {
    int depth = 1; 
    int i = startPos + 1; 
    dynamic quote = newQuoteState();
    while (i < this.length) {
      String c = (this.source[i]).toString(); 
      if (quote.single) {
        if (c == "'") {
          quote.single = false;
        }
        i += 1;
        continue;
      }
      if (quote.double) {
        if (c == "\\" && i + 1 < this.length) {
          i += 2;
          continue;
        }
        if (c == "\"") {
          quote.double = false;
        }
        i += 1;
        continue;
      }
      if (c == "'") {
        quote.single = true;
        i += 1;
        continue;
      }
      if (c == "\"") {
        quote.double = true;
        i += 1;
        continue;
      }
      if (c == "\\") {
        i += 2;
        continue;
      }
      if (c == "}") {
        return false;
      }
      if (c == "[") {
        depth += 1;
      } else {
        if (c == "]") {
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

  String _consumeParamName() {
    if (this.atEnd()) {
      return "";
    }
    String ch = this.peek(); 
    if (_isSpecialParam(ch)) {
      if (ch == "\$" && this.pos + 1 < this.length && "{'\"".contains((this.source[this.pos + 1]).toString())) {
        return "";
      }
      this.advance();
      return ch;
    }
    if ((ch.isNotEmpty && RegExp(r'^\d+$').hasMatch(ch))) {
      List<String> nameChars = <String>[]; 
      while (!(this.atEnd()) && (this.peek().isNotEmpty && RegExp(r'^\d+$').hasMatch(this.peek()))) {
        nameChars.add(this.advance());
      }
      return nameChars.join("");
    }
    if ((ch.isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch(ch)) || ch == "_") {
      List<String> nameChars = <String>[]; 
      while (!(this.atEnd())) {
        String c = this.peek(); 
        if ((c.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(c)) || c == "_") {
          nameChars.add(this.advance());
        } else {
          if (c == "[") {
            if (!(this._paramSubscriptHasClose(this.pos))) {
              break;
            }
            nameChars.add(this.advance());
            String content = this._parseMatchedPair("[", "]", matchedpairflagsArraysub, false); 
            nameChars.add(content);
            nameChars.add("]");
            break;
          } else {
            break;
          }
        }
      }
      if ((nameChars.isNotEmpty)) {
        return nameChars.join("");
      } else {
        return "";
      }
    }
    return "";
  }

  (Node?, String) _readParamExpansion(bool inDquote) {
    if (this.atEnd() || this.peek() != "\$") {
      return (null, "");
    }
    int start = this.pos; 
    this.advance();
    if (this.atEnd()) {
      this.pos = start;
      return (null, "");
    }
    String ch = this.peek(); 
    if (ch == "{") {
      this.advance();
      return this._readBracedParam(start, inDquote);
    }
    String text = "";
    if (_isSpecialParamUnbraced(ch) || _isDigit(ch) || ch == "#") {
      this.advance();
      text = _substring(this.source, start, this.pos);
      return (ParamExpansion(ch, "", "", "param"), text);
    }
    if ((ch.isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch(ch)) || ch == "_") {
      int nameStart = this.pos; 
      while (!(this.atEnd())) {
        String c = this.peek(); 
        if ((c.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(c)) || c == "_") {
          this.advance();
        } else {
          break;
        }
      }
      String name = _substring(this.source, nameStart, this.pos); 
      text = _substring(this.source, start, this.pos);
      return (ParamExpansion(name, "", "", "param"), text);
    }
    this.pos = start;
    return (null, "");
  }

  (Node?, String) _readBracedParam(int start, bool inDquote) {
    if (this.atEnd()) {
      throw MatchedPairError("unexpected EOF looking for `}'", start, 0);
    }
    int savedDolbrace = this._dolbraceState; 
    this._dolbraceState = dolbracestateParam;
    String ch = this.peek(); 
    if (_isFunsubChar(ch)) {
      this._dolbraceState = savedDolbrace;
      return this._readFunsub(start);
    }
    String param = "";
    String text = "";
    if (ch == "#") {
      this.advance();
      param = this._consumeParamName();
      if ((param.isNotEmpty) && !(this.atEnd()) && this.peek() == "}") {
        this.advance();
        text = _substring(this.source, start, this.pos);
        this._dolbraceState = savedDolbrace;
        return (ParamLength(param, "param-len"), text);
      }
      this.pos = start + 2;
    }
    String op = "";
    String arg = "";
    if (ch == "!") {
      this.advance();
      while (!(this.atEnd()) && _isWhitespaceNoNewline(this.peek())) {
        this.advance();
      }
      param = this._consumeParamName();
      if ((param.isNotEmpty)) {
        while (!(this.atEnd()) && _isWhitespaceNoNewline(this.peek())) {
          this.advance();
        }
        if (!(this.atEnd()) && this.peek() == "}") {
          this.advance();
          text = _substring(this.source, start, this.pos);
          this._dolbraceState = savedDolbrace;
          return (ParamIndirect(param, "", "", "param-indirect"), text);
        }
        if (!(this.atEnd()) && _isAtOrStar(this.peek())) {
          String suffix = this.advance(); 
          String trailing = this._parseMatchedPair("{", "}", matchedpairflagsDolbrace, false); 
          text = _substring(this.source, start, this.pos);
          this._dolbraceState = savedDolbrace;
          return (ParamIndirect(param + suffix + trailing, "", "", "param-indirect"), text);
        }
        op = this._consumeParamOperator();
        if (op == "" && !(this.atEnd()) && !"}\"'`".contains(this.peek())) {
          op = this.advance();
        }
        if (op != "" && !"\"'`".contains(op)) {
          arg = this._parseMatchedPair("{", "}", matchedpairflagsDolbrace, false);
          text = _substring(this.source, start, this.pos);
          this._dolbraceState = savedDolbrace;
          return (ParamIndirect(param, op, arg, "param-indirect"), text);
        }
        if (this.atEnd()) {
          this._dolbraceState = savedDolbrace;
          throw MatchedPairError("unexpected EOF looking for `}'", start, 0);
        }
        this.pos = start + 2;
      } else {
        this.pos = start + 2;
      }
    }
    param = this._consumeParamName();
    if (!((param.isNotEmpty))) {
      if (!(this.atEnd()) && ("-=+?".contains(this.peek()) || this.peek() == ":" && this.pos + 1 < this.length && _isSimpleParamOp((this.source[this.pos + 1]).toString()))) {
        param = "";
      } else {
        String content = this._parseMatchedPair("{", "}", matchedpairflagsDolbrace, false); 
        text = "\${" + content + "}";
        this._dolbraceState = savedDolbrace;
        return (ParamExpansion(content, "", "", "param"), text);
      }
    }
    if (this.atEnd()) {
      this._dolbraceState = savedDolbrace;
      throw MatchedPairError("unexpected EOF looking for `}'", start, 0);
    }
    if (this.peek() == "}") {
      this.advance();
      text = _substring(this.source, start, this.pos);
      this._dolbraceState = savedDolbrace;
      return (ParamExpansion(param, "", "", "param"), text);
    }
    op = this._consumeParamOperator();
    if (op == "") {
      if (!(this.atEnd()) && this.peek() == "\$" && this.pos + 1 < this.length && ((this.source[this.pos + 1]).toString() == "\"" || (this.source[this.pos + 1]).toString() == "'")) {
        int dollarCount = 1 + _countConsecutiveDollarsBefore(this.source, this.pos); 
        if (dollarCount % 2 == 1) {
          op = "";
        } else {
          op = this.advance();
        }
      } else {
        if (!(this.atEnd()) && this.peek() == "`") {
          int backtickPos = this.pos; 
          this.advance();
          while (!(this.atEnd()) && this.peek() != "`") {
            String bc = this.peek(); 
            if (bc == "\\" && this.pos + 1 < this.length) {
              String nextC = (this.source[this.pos + 1]).toString(); 
              if (_isEscapeCharInBacktick(nextC)) {
                this.advance();
              }
            }
            this.advance();
          }
          if (this.atEnd()) {
            this._dolbraceState = savedDolbrace;
            throw ParseError("Unterminated backtick", backtickPos, 0);
          }
          this.advance();
          op = "`";
        } else {
          if (!(this.atEnd()) && this.peek() == "\$" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "{") {
            op = "";
          } else {
            if (!(this.atEnd()) && (this.peek() == "'" || this.peek() == "\"")) {
              op = "";
            } else {
              if (!(this.atEnd()) && this.peek() == "\\") {
                op = this.advance();
                if (!(this.atEnd())) {
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
    this._updateDolbraceForOp(op, param.length > 0);
    try {
      int flags = (inDquote ? matchedpairflagsDquote : matchedpairflagsNone); 
      bool paramEndsWithDollar = param != "" && param.endsWith("\$"); 
      arg = this._collectParamArgument(flags, paramEndsWithDollar);
    } on MatchedPairError {
      this._dolbraceState = savedDolbrace;
      rethrow;
    }
    if ((op == "<" || op == ">") && arg.startsWith("(") && arg.endsWith(")")) {
      String inner = _safeSubstring(arg, 1, arg.length - 1); 
      try {
        dynamic subParser = newParser(inner, true, this._parser!._extglob);
        dynamic parsed = subParser.parseList(true);
        if (parsed != null && subParser.atEnd()) {
          String formatted = _formatCmdsubNode(parsed, 0, true, false, true); 
          arg = "(" + formatted + ")";
        }
      } on Exception {
      }
    }
    text = "\${" + param + op + arg + "}";
    this._dolbraceState = savedDolbrace;
    return (ParamExpansion(param, op, arg, "param"), text);
  }

  (Node?, String) _readFunsub(int start) {
    return this._parser!._parseFunsub(start);
  }
}

class Word implements Node {
  late String value;
  late List<Node> parts;
  late String kind;

  Word(String value, List<Node> parts, String kind) {
    this.value = value;
    this.parts = parts;
    this.kind = kind;
  }

  String toSexp() {
    String value = this.value; 
    value = this._expandAllAnsiCQuotes(value);
    value = this._stripLocaleStringDollars(value);
    value = this._normalizeArrayWhitespace(value);
    value = this._formatCommandSubstitutions(value, false);
    value = this._normalizeParamExpansionNewlines(value);
    value = this._stripArithLineContinuations(value);
    value = this._doubleCtlescSmart(value);
    value = value.replaceAll("\u007f", "\u0001\u007f");
    value = value.replaceAll("\\", "\\\\");
    if (value.endsWith("\\\\") && !(value.endsWith("\\\\\\\\"))) {
      value = value + "\\\\";
    }
    String escaped = value.replaceAll("\"", "\\\"").replaceAll("\n", "\\n").replaceAll("\t", "\\t"); 
    return "(word \"" + escaped + "\")";
  }

  void _appendWithCtlesc(List<int> result, int byteVal) {
    result.add((byteVal as int));
  }

  String _doubleCtlescSmart(String value) {
    List<String> result = <String>[]; 
    dynamic quote = newQuoteState();
    for (final _c1 in value.split('')) {
      var c = _c1;
      if (c == "'" && !(quote.double)) {
        quote.single = !(quote.single);
      } else {
        if (c == "\"" && !(quote.single)) {
          quote.double = !(quote.double);
        }
      }
      result.add(c);
      if (c == "\u0001") {
        if (quote.double) {
          int bsCount = 0; 
          for (int j = result.length - 2; j > -1; j += -1) {
            if (result[j] == "\\") {
              bsCount += 1;
            } else {
              break;
            }
          }
          if (bsCount % 2 == 0) {
            result.add("\u0001");
          }
        } else {
          result.add("\u0001");
        }
      }
    }
    return result.join("");
  }

  String _normalizeParamExpansionNewlines(String value) {
    List<String> result = <String>[]; 
    int i = 0; 
    dynamic quote = newQuoteState();
    while (i < value.length) {
      String c = (value[i]).toString(); 
      if (c == "'" && !(quote.double)) {
        quote.single = !(quote.single);
        result.add(c);
        i += 1;
      } else {
        if (c == "\"" && !(quote.single)) {
          quote.double = !(quote.double);
          result.add(c);
          i += 1;
        } else {
          if (_isExpansionStart(value, i, "\${") && !(quote.single)) {
            result.add("\$");
            result.add("{");
            i += 2;
            bool hadLeadingNewline = i < value.length && (value[i]).toString() == "\n"; 
            if (hadLeadingNewline) {
              result.add(" ");
              i += 1;
            }
            int depth = 1; 
            while (i < value.length && depth > 0) {
              String ch = (value[i]).toString(); 
              if (ch == "\\" && i + 1 < value.length && !(quote.single)) {
                if ((value[i + 1]).toString() == "\n") {
                  i += 2;
                  continue;
                }
                result.add(ch);
                result.add((value[i + 1]).toString());
                i += 2;
                continue;
              }
              if (ch == "'" && !(quote.double)) {
                quote.single = !(quote.single);
              } else {
                if (ch == "\"" && !(quote.single)) {
                  quote.double = !(quote.double);
                } else {
                  if (!(quote.inQuotes())) {
                    if (ch == "{") {
                      depth += 1;
                    } else {
                      if (ch == "}") {
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
    return result.join("");
  }

  String _shSingleQuote(String s) {
    if (!((s.isNotEmpty))) {
      return "''";
    }
    if (s == "'") {
      return "\\'";
    }
    List<String> result = <String>["'"]; 
    for (final _c2 in s.split('')) {
      var c = _c2;
      if (c == "'") {
        result.add("'\\''");
      } else {
        result.add(c);
      }
    }
    result.add("'");
    return result.join("");
  }

  List<int> _ansiCToBytes(String inner) {
    List<int> result = <int>[]; 
    int i = 0; 
    while (i < inner.length) {
      if ((inner[i]).toString() == "\\" && i + 1 < inner.length) {
        String c = (inner[i + 1]).toString(); 
        int simple = _getAnsiEscape(c); 
        if (simple >= 0) {
          result.add((simple as int));
          i += 2;
        } else {
          if (c == "'") {
            result.add((39 as int));
            i += 2;
          } else {
            int j = 0;
            int byteVal = 0;
            if (c == "x") {
              if (i + 2 < inner.length && (inner[i + 2]).toString() == "{") {
                j = i + 3;
                while (j < inner.length && _isHexDigit((inner[j]).toString())) {
                  j += 1;
                }
                String hexStr = _substring(inner, i + 3, j); 
                if (j < inner.length && (inner[j]).toString() == "}") {
                  j += 1;
                }
                if (!((hexStr.isNotEmpty))) {
                  return result;
                }
                byteVal = int.parse(hexStr, radix: 16) & 255;
                if (byteVal == 0) {
                  return result;
                }
                this._appendWithCtlesc(result, byteVal);
                i = j;
              } else {
                j = i + 2;
                while (j < inner.length && j < i + 4 && _isHexDigit((inner[j]).toString())) {
                  j += 1;
                }
                if (j > i + 2) {
                  byteVal = int.parse(_substring(inner, i + 2, j), radix: 16);
                  if (byteVal == 0) {
                    return result;
                  }
                  this._appendWithCtlesc(result, byteVal);
                  i = j;
                } else {
                  result.add(((inner[i]).toString().codeUnitAt(0) as int));
                  i += 1;
                }
              }
            } else {
              int codepoint = 0;
              if (c == "u") {
                j = i + 2;
                while (j < inner.length && j < i + 6 && _isHexDigit((inner[j]).toString())) {
                  j += 1;
                }
                if (j > i + 2) {
                  codepoint = int.parse(_substring(inner, i + 2, j), radix: 16);
                  if (codepoint == 0) {
                    return result;
                  }
                  result.addAll(utf8.encode(String.fromCharCode(codepoint)));
                  i = j;
                } else {
                  result.add(((inner[i]).toString().codeUnitAt(0) as int));
                  i += 1;
                }
              } else {
                if (c == "U") {
                  j = i + 2;
                  while (j < inner.length && j < i + 10 && _isHexDigit((inner[j]).toString())) {
                    j += 1;
                  }
                  if (j > i + 2) {
                    codepoint = int.parse(_substring(inner, i + 2, j), radix: 16);
                    if (codepoint == 0) {
                      return result;
                    }
                    result.addAll(utf8.encode(String.fromCharCode(codepoint)));
                    i = j;
                  } else {
                    result.add(((inner[i]).toString().codeUnitAt(0) as int));
                    i += 1;
                  }
                } else {
                  if (c == "c") {
                    if (i + 3 <= inner.length) {
                      String ctrlChar = (inner[i + 2]).toString(); 
                      int skipExtra = 0; 
                      if (ctrlChar == "\\" && i + 4 <= inner.length && (inner[i + 3]).toString() == "\\") {
                        skipExtra = 1;
                      }
                      int ctrlVal = ctrlChar.codeUnitAt(0) & 31; 
                      if (ctrlVal == 0) {
                        return result;
                      }
                      this._appendWithCtlesc(result, ctrlVal);
                      i += 3 + skipExtra;
                    } else {
                      result.add(((inner[i]).toString().codeUnitAt(0) as int));
                      i += 1;
                    }
                  } else {
                    if (c == "0") {
                      j = i + 2;
                      while (j < inner.length && j < i + 4 && _isOctalDigit((inner[j]).toString())) {
                        j += 1;
                      }
                      if (j > i + 2) {
                        byteVal = int.parse(_substring(inner, i + 1, j), radix: 8) & 255;
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
                        while (j < inner.length && j < i + 4 && _isOctalDigit((inner[j]).toString())) {
                          j += 1;
                        }
                        byteVal = int.parse(_substring(inner, i + 1, j), radix: 8) & 255;
                        if (byteVal == 0) {
                          return result;
                        }
                        this._appendWithCtlesc(result, byteVal);
                        i = j;
                      } else {
                        result.add((92 as int));
                        result.add((c.codeUnitAt(0) as int));
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
        result.addAll(utf8.encode((inner[i]).toString()));
        i += 1;
      }
    }
    return result;
  }

  String _expandAnsiCEscapes(String value) {
    if (!(value.startsWith("'") && value.endsWith("'"))) {
      return value;
    }
    String inner = _substring(value, 1, value.length - 1); 
    List<int> literalBytes = this._ansiCToBytes(inner); 
    String literalStr = utf8.decode(literalBytes, allowMalformed: true); 
    return this._shSingleQuote(literalStr);
  }

  String _expandAllAnsiCQuotes(String value) {
    List<String> result = <String>[]; 
    int i = 0; 
    dynamic quote = newQuoteState();
    bool inBacktick = false; 
    int braceDepth = 0; 
    while (i < value.length) {
      String ch = (value[i]).toString(); 
      if (ch == "`" && !(quote.single)) {
        inBacktick = !(inBacktick);
        result.add(ch);
        i += 1;
        continue;
      }
      if (inBacktick) {
        if (ch == "\\" && i + 1 < value.length) {
          result.add(ch);
          result.add((value[i + 1]).toString());
          i += 2;
        } else {
          result.add(ch);
          i += 1;
        }
        continue;
      }
      if (!(quote.single)) {
        if (_isExpansionStart(value, i, "\${")) {
          braceDepth += 1;
          quote.push();
          result.add("\${");
          i += 2;
          continue;
        } else {
          if (ch == "}" && braceDepth > 0 && !(quote.double)) {
            braceDepth -= 1;
            result.add(ch);
            quote.pop();
            i += 1;
            continue;
          }
        }
      }
      bool effectiveInDquote = quote.double; 
      if (ch == "'" && !(effectiveInDquote)) {
        bool isAnsiC = !(quote.single) && i > 0 && (value[i - 1]).toString() == "\$" && _countConsecutiveDollarsBefore(value, i - 1) % 2 == 0; 
        if (!(isAnsiC)) {
          quote.single = !(quote.single);
        }
        result.add(ch);
        i += 1;
      } else {
        if (ch == "\"" && !(quote.single)) {
          quote.double = !(quote.double);
          result.add(ch);
          i += 1;
        } else {
          if (ch == "\\" && i + 1 < value.length && !(quote.single)) {
            result.add(ch);
            result.add((value[i + 1]).toString());
            i += 2;
          } else {
            if (_startsWithAt(value, i, "\$'") && !(quote.single) && !(effectiveInDquote) && _countConsecutiveDollarsBefore(value, i) % 2 == 0) {
              int j = i + 2; 
              while (j < value.length) {
                if ((value[j]).toString() == "\\" && j + 1 < value.length) {
                  j += 2;
                } else {
                  if ((value[j]).toString() == "'") {
                    j += 1;
                    break;
                  } else {
                    j += 1;
                  }
                }
              }
              String ansiStr = _substring(value, i, j); 
              String expanded = this._expandAnsiCEscapes(_substring(ansiStr, 1, ansiStr.length)); 
              bool outerInDquote = quote.outerDouble(); 
              if (braceDepth > 0 && outerInDquote && expanded.startsWith("'") && expanded.endsWith("'")) {
                String inner = _substring(expanded, 1, expanded.length - 1); 
                if (inner.indexOf("\u0001") == -1) {
                  String resultStr = result.join(""); 
                  bool inPattern = false; 
                  int lastBraceIdx = resultStr.lastIndexOf("\${"); 
                  if (lastBraceIdx >= 0) {
                    String afterBrace = resultStr.substring(lastBraceIdx + 2); 
                    int varNameLen = 0; 
                    if ((afterBrace.isNotEmpty)) {
                      if ("@*#?-\$!0123456789_".contains((afterBrace[0]).toString())) {
                        varNameLen = 1;
                      } else {
                        if (((afterBrace[0]).toString().isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch((afterBrace[0]).toString())) || (afterBrace[0]).toString() == "_") {
                          while (varNameLen < afterBrace.length) {
                            String c = (afterBrace[varNameLen]).toString(); 
                            if (!((c.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(c)) || c == "_")) {
                              break;
                            }
                            varNameLen += 1;
                          }
                        }
                      }
                    }
                    if (varNameLen > 0 && varNameLen < afterBrace.length && !"#?-".contains((afterBrace[0]).toString())) {
                      String opStart = afterBrace.substring(varNameLen); 
                      if (opStart.startsWith("@") && opStart.length > 1) {
                        opStart = opStart.substring(1);
                      }
                      for (final op in <String>["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
                        if (opStart.startsWith(op)) {
                          inPattern = true;
                          break;
                        }
                      }
                      if (!(inPattern) && (opStart.isNotEmpty) && !"%#/^,~:+-=?".contains((opStart[0]).toString())) {
                        for (final op in <String>["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
                          if (opStart.contains(op)) {
                            inPattern = true;
                            break;
                          }
                        }
                      }
                    } else {
                      if (varNameLen == 0 && afterBrace.length > 1) {
                        String firstChar = (afterBrace[0]).toString(); 
                        if (!"%#/^,".contains(firstChar)) {
                          String rest = afterBrace.substring(1); 
                          for (final op in <String>["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
                            if (rest.contains(op)) {
                              inPattern = true;
                              break;
                            }
                          }
                        }
                      }
                    }
                  }
                  if (!(inPattern)) {
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
    return result.join("");
  }

  String _stripLocaleStringDollars(String value) {
    List<String> result = <String>[]; 
    int i = 0; 
    int braceDepth = 0; 
    int bracketDepth = 0; 
    dynamic quote = newQuoteState();
    dynamic braceQuote = newQuoteState();
    bool bracketInDoubleQuote = false; 
    while (i < value.length) {
      String ch = (value[i]).toString(); 
      if (ch == "\\" && i + 1 < value.length && !(quote.single) && !(braceQuote.single)) {
        result.add(ch);
        result.add((value[i + 1]).toString());
        i += 2;
      } else {
        if (_startsWithAt(value, i, "\${") && !(quote.single) && !(braceQuote.single) && (i == 0 || (value[i - 1]).toString() != "\$")) {
          braceDepth += 1;
          braceQuote.double = false;
          braceQuote.single = false;
          result.add("\$");
          result.add("{");
          i += 2;
        } else {
          if (ch == "}" && braceDepth > 0 && !(quote.single) && !(braceQuote.double) && !(braceQuote.single)) {
            braceDepth -= 1;
            result.add(ch);
            i += 1;
          } else {
            if (ch == "[" && braceDepth > 0 && !(quote.single) && !(braceQuote.double)) {
              bracketDepth += 1;
              bracketInDoubleQuote = false;
              result.add(ch);
              i += 1;
            } else {
              if (ch == "]" && bracketDepth > 0 && !(quote.single) && !(bracketInDoubleQuote)) {
                bracketDepth -= 1;
                result.add(ch);
                i += 1;
              } else {
                if (ch == "'" && !(quote.double) && braceDepth == 0) {
                  quote.single = !(quote.single);
                  result.add(ch);
                  i += 1;
                } else {
                  if (ch == "\"" && !(quote.single) && braceDepth == 0) {
                    quote.double = !(quote.double);
                    result.add(ch);
                    i += 1;
                  } else {
                    if (ch == "\"" && !(quote.single) && bracketDepth > 0) {
                      bracketInDoubleQuote = !(bracketInDoubleQuote);
                      result.add(ch);
                      i += 1;
                    } else {
                      if (ch == "\"" && !(quote.single) && !(braceQuote.single) && braceDepth > 0) {
                        braceQuote.double = !(braceQuote.double);
                        result.add(ch);
                        i += 1;
                      } else {
                        if (ch == "'" && !(quote.double) && !(braceQuote.double) && braceDepth > 0) {
                          braceQuote.single = !(braceQuote.single);
                          result.add(ch);
                          i += 1;
                        } else {
                          if (_startsWithAt(value, i, "\$\"") && !(quote.single) && !(braceQuote.single) && (braceDepth > 0 || bracketDepth > 0 || !(quote.double)) && !(braceQuote.double) && !(bracketInDoubleQuote)) {
                            int dollarCount = 1 + _countConsecutiveDollarsBefore(value, i); 
                            if (dollarCount % 2 == 1) {
                              result.add("\"");
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
    return result.join("");
  }

  String _normalizeArrayWhitespace(String value) {
    int i = 0; 
    if (!(i < value.length && (((value[i]).toString().isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch((value[i]).toString())) || (value[i]).toString() == "_"))) {
      return value;
    }
    i += 1;
    while (i < value.length && (((value[i]).toString().isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch((value[i]).toString())) || (value[i]).toString() == "_")) {
      i += 1;
    }
    while (i < value.length && (value[i]).toString() == "[") {
      int depth = 1; 
      i += 1;
      while (i < value.length && depth > 0) {
        if ((value[i]).toString() == "[") {
          depth += 1;
        } else {
          if ((value[i]).toString() == "]") {
            depth -= 1;
          }
        }
        i += 1;
      }
      if (depth != 0) {
        return value;
      }
    }
    if (i < value.length && (value[i]).toString() == "+") {
      i += 1;
    }
    if (!(i + 1 < value.length && (value[i]).toString() == "=" && (value[i + 1]).toString() == "(")) {
      return value;
    }
    String prefix = _substring(value, 0, i + 1); 
    int openParenPos = i + 1; 
    int closeParenPos = 0;
    if (value.endsWith(")")) {
      closeParenPos = value.length - 1;
    } else {
      closeParenPos = this._findMatchingParen(value, openParenPos);
      if (closeParenPos < 0) {
        return value;
      }
    }
    String inner = _substring(value, openParenPos + 1, closeParenPos); 
    String suffix = _substring(value, closeParenPos + 1, value.length); 
    String result = this._normalizeArrayInner(inner); 
    return prefix + "(" + result + ")" + suffix;
  }

  int _findMatchingParen(String value, int openPos) {
    if (openPos >= value.length || (value[openPos]).toString() != "(") {
      return -1;
    }
    int i = openPos + 1; 
    int depth = 1; 
    dynamic quote = newQuoteState();
    while (i < value.length && depth > 0) {
      String ch = (value[i]).toString(); 
      if (ch == "\\" && i + 1 < value.length && !(quote.single)) {
        i += 2;
        continue;
      }
      if (ch == "'" && !(quote.double)) {
        quote.single = !(quote.single);
        i += 1;
        continue;
      }
      if (ch == "\"" && !(quote.single)) {
        quote.double = !(quote.double);
        i += 1;
        continue;
      }
      if (quote.single || quote.double) {
        i += 1;
        continue;
      }
      if (ch == "#") {
        while (i < value.length && (value[i]).toString() != "\n") {
          i += 1;
        }
        continue;
      }
      if (ch == "(") {
        depth += 1;
      } else {
        if (ch == ")") {
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

  String _normalizeArrayInner(String inner) {
    List<String> normalized = <String>[]; 
    int i = 0; 
    bool inWhitespace = true; 
    int braceDepth = 0; 
    int bracketDepth = 0; 
    while (i < inner.length) {
      String ch = (inner[i]).toString(); 
      if (_isWhitespace(ch)) {
        if (!(inWhitespace) && (normalized.isNotEmpty) && braceDepth == 0 && bracketDepth == 0) {
          normalized.add(" ");
          inWhitespace = true;
        }
        if (braceDepth > 0 || bracketDepth > 0) {
          normalized.add(ch);
        }
        i += 1;
      } else {
        int j = 0;
        if (ch == "'") {
          inWhitespace = false;
          j = i + 1;
          while (j < inner.length && (inner[j]).toString() != "'") {
            j += 1;
          }
          normalized.add(_substring(inner, i, j + 1));
          i = j + 1;
        } else {
          if (ch == "\"") {
            inWhitespace = false;
            j = i + 1;
            List<String> dqContent = <String>["\""]; 
            int dqBraceDepth = 0; 
            while (j < inner.length) {
              if ((inner[j]).toString() == "\\" && j + 1 < inner.length) {
                if ((inner[j + 1]).toString() == "\n") {
                  j += 2;
                } else {
                  dqContent.add((inner[j]).toString());
                  dqContent.add((inner[j + 1]).toString());
                  j += 2;
                }
              } else {
                if (_isExpansionStart(inner, j, "\${")) {
                  dqContent.add("\${");
                  dqBraceDepth += 1;
                  j += 2;
                } else {
                  if ((inner[j]).toString() == "}" && dqBraceDepth > 0) {
                    dqContent.add("}");
                    dqBraceDepth -= 1;
                    j += 1;
                  } else {
                    if ((inner[j]).toString() == "\"" && dqBraceDepth == 0) {
                      dqContent.add("\"");
                      j += 1;
                      break;
                    } else {
                      dqContent.add((inner[j]).toString());
                      j += 1;
                    }
                  }
                }
              }
            }
            normalized.add(dqContent.join(""));
            i = j;
          } else {
            if (ch == "\\" && i + 1 < inner.length) {
              if ((inner[i + 1]).toString() == "\n") {
                i += 2;
              } else {
                inWhitespace = false;
                normalized.add(_substring(inner, i, i + 2));
                i += 2;
              }
            } else {
              int depth = 0;
              if (_isExpansionStart(inner, i, "\$((")) {
                inWhitespace = false;
                j = i + 3;
                depth = 1;
                while (j < inner.length && depth > 0) {
                  if (j + 1 < inner.length && (inner[j]).toString() == "(" && (inner[j + 1]).toString() == "(") {
                    depth += 1;
                    j += 2;
                  } else {
                    if (j + 1 < inner.length && (inner[j]).toString() == ")" && (inner[j + 1]).toString() == ")") {
                      depth -= 1;
                      j += 2;
                    } else {
                      j += 1;
                    }
                  }
                }
                normalized.add(_substring(inner, i, j));
                i = j;
              } else {
                if (_isExpansionStart(inner, i, "\$(")) {
                  inWhitespace = false;
                  j = i + 2;
                  depth = 1;
                  while (j < inner.length && depth > 0) {
                    if ((inner[j]).toString() == "(" && j > 0 && (inner[j - 1]).toString() == "\$") {
                      depth += 1;
                    } else {
                      if ((inner[j]).toString() == ")") {
                        depth -= 1;
                      } else {
                        if ((inner[j]).toString() == "'") {
                          j += 1;
                          while (j < inner.length && (inner[j]).toString() != "'") {
                            j += 1;
                          }
                        } else {
                          if ((inner[j]).toString() == "\"") {
                            j += 1;
                            while (j < inner.length) {
                              if ((inner[j]).toString() == "\\" && j + 1 < inner.length) {
                                j += 2;
                                continue;
                              }
                              if ((inner[j]).toString() == "\"") {
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
                  normalized.add(_substring(inner, i, j));
                  i = j;
                } else {
                  if ((ch == "<" || ch == ">") && i + 1 < inner.length && (inner[i + 1]).toString() == "(") {
                    inWhitespace = false;
                    j = i + 2;
                    depth = 1;
                    while (j < inner.length && depth > 0) {
                      if ((inner[j]).toString() == "(") {
                        depth += 1;
                      } else {
                        if ((inner[j]).toString() == ")") {
                          depth -= 1;
                        } else {
                          if ((inner[j]).toString() == "'") {
                            j += 1;
                            while (j < inner.length && (inner[j]).toString() != "'") {
                              j += 1;
                            }
                          } else {
                            if ((inner[j]).toString() == "\"") {
                              j += 1;
                              while (j < inner.length) {
                                if ((inner[j]).toString() == "\\" && j + 1 < inner.length) {
                                  j += 2;
                                  continue;
                                }
                                if ((inner[j]).toString() == "\"") {
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
                    normalized.add(_substring(inner, i, j));
                    i = j;
                  } else {
                    if (_isExpansionStart(inner, i, "\${")) {
                      inWhitespace = false;
                      normalized.add("\${");
                      braceDepth += 1;
                      i += 2;
                    } else {
                      if (ch == "{" && braceDepth > 0) {
                        normalized.add(ch);
                        braceDepth += 1;
                        i += 1;
                      } else {
                        if (ch == "}" && braceDepth > 0) {
                          normalized.add(ch);
                          braceDepth -= 1;
                          i += 1;
                        } else {
                          if (ch == "#" && braceDepth == 0 && inWhitespace) {
                            while (i < inner.length && (inner[i]).toString() != "\n") {
                              i += 1;
                            }
                          } else {
                            if (ch == "[") {
                              if (inWhitespace || bracketDepth > 0) {
                                bracketDepth += 1;
                              }
                              inWhitespace = false;
                              normalized.add(ch);
                              i += 1;
                            } else {
                              if (ch == "]" && bracketDepth > 0) {
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
    return _trimRight(normalized.join(""), " \t\n\r");
  }

  String _stripArithLineContinuations(String value) {
    List<String> result = <String>[]; 
    int i = 0; 
    while (i < value.length) {
      if (_isExpansionStart(value, i, "\$((")) {
        int start = i; 
        i += 3;
        int depth = 2; 
        List<String> arithContent = <String>[]; 
        int firstCloseIdx = -1; 
        while (i < value.length && depth > 0) {
          if ((value[i]).toString() == "(") {
            arithContent.add("(");
            depth += 1;
            i += 1;
            if (depth > 1) {
              firstCloseIdx = -1;
            }
          } else {
            if ((value[i]).toString() == ")") {
              if (depth == 2) {
                firstCloseIdx = arithContent.length;
              }
              depth -= 1;
              if (depth > 0) {
                arithContent.add(")");
              }
              i += 1;
            } else {
              if ((value[i]).toString() == "\\" && i + 1 < value.length && (value[i + 1]).toString() == "\n") {
                int numBackslashes = 0; 
                int j = arithContent.length - 1; 
                while (j >= 0 && arithContent[j] == "\n") {
                  j -= 1;
                }
                while (j >= 0 && arithContent[j] == "\\") {
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
                arithContent.add((value[i]).toString());
                i += 1;
                if (depth == 1) {
                  firstCloseIdx = -1;
                }
              }
            }
          }
        }
        if (depth == 0 || depth == 1 && firstCloseIdx != -1) {
          String content = arithContent.join(""); 
          if (firstCloseIdx != -1) {
            content = _safeSubstring(content, 0, firstCloseIdx);
            String closing = (depth == 0 ? "))" : ")"); 
            result.add("\$((" + content + closing);
          } else {
            result.add("\$((" + content + ")");
          }
        } else {
          result.add(_substring(value, start, i));
        }
      } else {
        result.add((value[i]).toString());
        i += 1;
      }
    }
    return result.join("");
  }

  List<Node> _collectCmdsubs(Node node) {
    List<Node> result = <Node>[]; 
    switch (node) {
      case CommandSubstitution nodeCommandSubstitution:
        result.add(nodeCommandSubstitution);
        break;
      case Array nodeArray:
        for (final elem in nodeArray.elements) {
          for (final p in elem.parts) {
            switch (p) {
              case CommandSubstitution pCommandSubstitution:
                result.add(pCommandSubstitution);
                break;
              default:
                result.addAll(this._collectCmdsubs(p));
                break;
            }
          }
        }
        break;
      case ArithmeticExpansion nodeArithmeticExpansion:
        if (nodeArithmeticExpansion.expression != null) {
          result.addAll(this._collectCmdsubs(nodeArithmeticExpansion.expression!));
        }
        break;
      case ArithBinaryOp nodeArithBinaryOp:
        result.addAll(this._collectCmdsubs(nodeArithBinaryOp.left));
        result.addAll(this._collectCmdsubs(nodeArithBinaryOp.right));
        break;
      case ArithComma nodeArithComma:
        result.addAll(this._collectCmdsubs(nodeArithComma.left));
        result.addAll(this._collectCmdsubs(nodeArithComma.right));
        break;
      case ArithUnaryOp nodeArithUnaryOp:
        result.addAll(this._collectCmdsubs(nodeArithUnaryOp.operand));
        break;
      case ArithPreIncr nodeArithPreIncr:
        result.addAll(this._collectCmdsubs(nodeArithPreIncr.operand));
        break;
      case ArithPostIncr nodeArithPostIncr:
        result.addAll(this._collectCmdsubs(nodeArithPostIncr.operand));
        break;
      case ArithPreDecr nodeArithPreDecr:
        result.addAll(this._collectCmdsubs(nodeArithPreDecr.operand));
        break;
      case ArithPostDecr nodeArithPostDecr:
        result.addAll(this._collectCmdsubs(nodeArithPostDecr.operand));
        break;
      case ArithTernary nodeArithTernary:
        result.addAll(this._collectCmdsubs(nodeArithTernary.condition));
        result.addAll(this._collectCmdsubs(nodeArithTernary.ifTrue));
        result.addAll(this._collectCmdsubs(nodeArithTernary.ifFalse));
        break;
      case ArithAssign nodeArithAssign:
        result.addAll(this._collectCmdsubs(nodeArithAssign.target));
        result.addAll(this._collectCmdsubs(nodeArithAssign.value));
        break;
    }
    return result;
  }

  List<Node> _collectProcsubs(Node node) {
    List<Node> result = <Node>[]; 
    switch (node) {
      case ProcessSubstitution nodeProcessSubstitution:
        result.add(nodeProcessSubstitution);
        break;
      case Array nodeArray:
        for (final elem in nodeArray.elements) {
          for (final p in elem.parts) {
            switch (p) {
              case ProcessSubstitution pProcessSubstitution:
                result.add(pProcessSubstitution);
                break;
              default:
                result.addAll(this._collectProcsubs(p));
                break;
            }
          }
        }
        break;
    }
    return result;
  }

  String _formatCommandSubstitutions(String value, bool inArith) {
    List<Node> cmdsubParts = <Node>[]; 
    List<Node> procsubParts = <Node>[]; 
    bool hasArith = false; 
    for (final p in this.parts) {
      switch (p) {
        case CommandSubstitution pCommandSubstitution:
          cmdsubParts.add(pCommandSubstitution);
          break;
        case ProcessSubstitution pProcessSubstitution:
          procsubParts.add(pProcessSubstitution);
          break;
        case ArithmeticExpansion pArithmeticExpansion:
          hasArith = true;
          break;
        default:
          cmdsubParts.addAll(this._collectCmdsubs(p));
          procsubParts.addAll(this._collectProcsubs(p));
          break;
      }
    }
    bool hasBraceCmdsub = value.indexOf("\${ ") != -1 || value.indexOf("\${\t") != -1 || value.indexOf("\${\n") != -1 || value.indexOf("\${|") != -1; 
    bool hasUntrackedCmdsub = false; 
    bool hasUntrackedProcsub = false; 
    int idx = 0; 
    dynamic scanQuote = newQuoteState();
    while (idx < value.length) {
      if ((value[idx]).toString() == "\"") {
        scanQuote.double = !(scanQuote.double);
        idx += 1;
      } else {
        if ((value[idx]).toString() == "'" && !(scanQuote.double)) {
          idx += 1;
          while (idx < value.length && (value[idx]).toString() != "'") {
            idx += 1;
          }
          if (idx < value.length) {
            idx += 1;
          }
        } else {
          if (_startsWithAt(value, idx, "\$(") && !(_startsWithAt(value, idx, "\$((")) && !(_isBackslashEscaped(value, idx)) && !(_isDollarDollarParen(value, idx))) {
            hasUntrackedCmdsub = true;
            break;
          } else {
            if ((_startsWithAt(value, idx, "<(") || _startsWithAt(value, idx, ">(")) && !(scanQuote.double)) {
              if (idx == 0 || !(((value[idx - 1]).toString().isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch((value[idx - 1]).toString()))) && !"\"'".contains((value[idx - 1]).toString())) {
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
    bool hasParamWithProcsubPattern = value.contains("\${") && (value.contains("<(") || value.contains(">(")); 
    if (!((cmdsubParts.isNotEmpty)) && !((procsubParts.isNotEmpty)) && !(hasBraceCmdsub) && !(hasUntrackedCmdsub) && !(hasUntrackedProcsub) && !(hasParamWithProcsubPattern)) {
      return value;
    }
    List<String> result = <String>[]; 
    int i = 0; 
    int cmdsubIdx = 0; 
    int procsubIdx = 0; 
    dynamic mainQuote = newQuoteState();
    int extglobDepth = 0; 
    int deprecatedArithDepth = 0; 
    int arithDepth = 0; 
    int arithParenDepth = 0; 
    while (i < value.length) {
      if (i > 0 && _isExtglobPrefix((value[i - 1]).toString()) && (value[i]).toString() == "(" && !(_isBackslashEscaped(value, i - 1))) {
        extglobDepth += 1;
        result.add((value[i]).toString());
        i += 1;
        continue;
      }
      if ((value[i]).toString() == ")" && extglobDepth > 0) {
        extglobDepth -= 1;
        result.add((value[i]).toString());
        i += 1;
        continue;
      }
      if (_startsWithAt(value, i, "\$[") && !(_isBackslashEscaped(value, i))) {
        deprecatedArithDepth += 1;
        result.add((value[i]).toString());
        i += 1;
        continue;
      }
      if ((value[i]).toString() == "]" && deprecatedArithDepth > 0) {
        deprecatedArithDepth -= 1;
        result.add((value[i]).toString());
        i += 1;
        continue;
      }
      if (_isExpansionStart(value, i, "\$((") && !(_isBackslashEscaped(value, i)) && hasArith) {
        arithDepth += 1;
        arithParenDepth += 2;
        result.add("\$((");
        i += 3;
        continue;
      }
      if (arithDepth > 0 && arithParenDepth == 2 && _startsWithAt(value, i, "))")) {
        arithDepth -= 1;
        arithParenDepth -= 2;
        result.add("))");
        i += 2;
        continue;
      }
      if (arithDepth > 0) {
        if ((value[i]).toString() == "(") {
          arithParenDepth += 1;
          result.add((value[i]).toString());
          i += 1;
          continue;
        } else {
          if ((value[i]).toString() == ")") {
            arithParenDepth -= 1;
            result.add((value[i]).toString());
            i += 1;
            continue;
          }
        }
      }
      int j = 0;
      if (_isExpansionStart(value, i, "\$((") && !(hasArith)) {
        j = _findCmdsubEnd(value, i + 2);
        result.add(_substring(value, i, j));
        if (cmdsubIdx < cmdsubParts.length) {
          cmdsubIdx += 1;
        }
        i = j;
        continue;
      }
      String inner = "";
      dynamic node;
      String formatted = "";
      dynamic parser;
      dynamic parsed;
      if (_startsWithAt(value, i, "\$(") && !(_startsWithAt(value, i, "\$((")) && !(_isBackslashEscaped(value, i)) && !(_isDollarDollarParen(value, i))) {
        j = _findCmdsubEnd(value, i + 2);
        if (extglobDepth > 0) {
          result.add(_substring(value, i, j));
          if (cmdsubIdx < cmdsubParts.length) {
            cmdsubIdx += 1;
          }
          i = j;
          continue;
        }
        inner = _substring(value, i + 2, j - 1);
        if (cmdsubIdx < cmdsubParts.length) {
          node = cmdsubParts[cmdsubIdx];
          formatted = _formatCmdsubNode((node as CommandSubstitution).command, 0, false, false, false);
          cmdsubIdx += 1;
        } else {
          try {
            parser = newParser(inner, false, false);
            parsed = parser.parseList(true);
            formatted = (parsed != null ? _formatCmdsubNode(parsed, 0, false, false, false) : "");
          } on Exception {
            formatted = inner;
          }
        }
        if (formatted.startsWith("(")) {
          result.add("\$( " + formatted + ")");
        } else {
          result.add("\$(" + formatted + ")");
        }
        i = j;
      } else {
        if ((value[i]).toString() == "`" && cmdsubIdx < cmdsubParts.length) {
          j = i + 1;
          while (j < value.length) {
            if ((value[j]).toString() == "\\" && j + 1 < value.length) {
              j += 2;
              continue;
            }
            if ((value[j]).toString() == "`") {
              j += 1;
              break;
            }
            j += 1;
          }
          result.add(_substring(value, i, j));
          cmdsubIdx += 1;
          i = j;
        } else {
          String prefix = "";
          if (_isExpansionStart(value, i, "\${") && i + 2 < value.length && _isFunsubChar((value[i + 2]).toString()) && !(_isBackslashEscaped(value, i))) {
            j = _findFunsubEnd(value, i + 2);
            Node? cmdsubNode = (cmdsubIdx < cmdsubParts.length ? cmdsubParts[cmdsubIdx] : null);
            if ((cmdsubNode is CommandSubstitution) && (cmdsubNode as CommandSubstitution).brace) {
              node = cmdsubNode;
              formatted = _formatCmdsubNode((node as CommandSubstitution).command, 0, false, false, false);
              bool hasPipe = (value[i + 2]).toString() == "|"; 
              prefix = (hasPipe ? "\${|" : "\${ ");
              String origInner = _substring(value, i + 2, j - 1); 
              bool endsWithNewline = origInner.endsWith("\n"); 
              String suffix = "";
              if (!((formatted.isNotEmpty)) || (formatted.isNotEmpty && RegExp(r'^\s+$').hasMatch(formatted))) {
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
              result.add(_substring(value, i, j));
            }
            i = j;
          } else {
            if ((_startsWithAt(value, i, ">(") || _startsWithAt(value, i, "<(")) && !(mainQuote.double) && deprecatedArithDepth == 0 && arithDepth == 0) {
              bool isProcsub = i == 0 || !(((value[i - 1]).toString().isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch((value[i - 1]).toString()))) && !"\"'".contains((value[i - 1]).toString()); 
              if (extglobDepth > 0) {
                j = _findCmdsubEnd(value, i + 2);
                result.add(_substring(value, i, j));
                if (procsubIdx < procsubParts.length) {
                  procsubIdx += 1;
                }
                i = j;
                continue;
              }
              String direction = "";
              bool compact = false;
              String stripped = "";
              if (procsubIdx < procsubParts.length) {
                direction = (value[i]).toString();
                j = _findCmdsubEnd(value, i + 2);
                node = procsubParts[procsubIdx];
                compact = _startsWithSubshell((node as ProcessSubstitution).command);
                formatted = _formatCmdsubNode((node as ProcessSubstitution).command, 0, true, compact, true);
                String rawContent = _substring(value, i + 2, j - 1); 
                if ((node as ProcessSubstitution).command.kind == "subshell") {
                  int leadingWsEnd = 0; 
                  while (leadingWsEnd < rawContent.length && " \t\n".contains((rawContent[leadingWsEnd]).toString())) {
                    leadingWsEnd += 1;
                  }
                  String leadingWs = _safeSubstring(rawContent, 0, leadingWsEnd); 
                  stripped = rawContent.substring(leadingWsEnd);
                  if (stripped.startsWith("(")) {
                    if ((leadingWs.isNotEmpty)) {
                      String normalizedWs = leadingWs.replaceAll("\n", " ").replaceAll("\t", " "); 
                      String spaced = _formatCmdsubNode((node as ProcessSubstitution).command, 0, false, false, false); 
                      result.add(direction + "(" + normalizedWs + spaced + ")");
                    } else {
                      rawContent = rawContent.replaceAll("\\\n", "");
                      result.add(direction + "(" + rawContent + ")");
                    }
                    procsubIdx += 1;
                    i = j;
                    continue;
                  }
                }
                rawContent = _substring(value, i + 2, j - 1);
                String rawStripped = rawContent.replaceAll("\\\n", ""); 
                if (_startsWithSubshell((node as ProcessSubstitution).command) && formatted != rawStripped) {
                  result.add(direction + "(" + rawStripped + ")");
                } else {
                  String finalOutput = direction + "(" + formatted + ")"; 
                  result.add(finalOutput);
                }
                procsubIdx += 1;
                i = j;
              } else {
                if (isProcsub && (this.parts.length != 0)) {
                  direction = (value[i]).toString();
                  j = _findCmdsubEnd(value, i + 2);
                  if (j > value.length || j > 0 && j <= value.length && (value[j - 1]).toString() != ")") {
                    result.add((value[i]).toString());
                    i += 1;
                    continue;
                  }
                  inner = _substring(value, i + 2, j - 1);
                  try {
                    parser = newParser(inner, false, false);
                    parsed = parser.parseList(true);
                    if (parsed != null && parser.pos == inner.length && !inner.contains("\n")) {
                      compact = _startsWithSubshell(parsed);
                      formatted = _formatCmdsubNode(parsed, 0, true, compact, true);
                    } else {
                      formatted = inner;
                    }
                  } on Exception {
                    formatted = inner;
                  }
                  result.add(direction + "(" + formatted + ")");
                  i = j;
                } else {
                  if (isProcsub) {
                    direction = (value[i]).toString();
                    j = _findCmdsubEnd(value, i + 2);
                    if (j > value.length || j > 0 && j <= value.length && (value[j - 1]).toString() != ")") {
                      result.add((value[i]).toString());
                      i += 1;
                      continue;
                    }
                    inner = _substring(value, i + 2, j - 1);
                    if (inArith) {
                      result.add(direction + "(" + inner + ")");
                    } else {
                      if ((_trimBoth(inner, " \t\n\r").isNotEmpty)) {
                        stripped = _trimLeft(inner, " \t");
                        result.add(direction + "(" + stripped + ")");
                      } else {
                        result.add(direction + "(" + inner + ")");
                      }
                    }
                    i = j;
                  } else {
                    result.add((value[i]).toString());
                    i += 1;
                  }
                }
              }
            } else {
              int depth = 0;
              if ((_isExpansionStart(value, i, "\${ ") || _isExpansionStart(value, i, "\${\t") || _isExpansionStart(value, i, "\${\n") || _isExpansionStart(value, i, "\${|")) && !(_isBackslashEscaped(value, i))) {
                prefix = _substring(value, i, i + 3).replaceAll("\t", " ").replaceAll("\n", " ");
                j = i + 3;
                depth = 1;
                while (j < value.length && depth > 0) {
                  if ((value[j]).toString() == "{") {
                    depth += 1;
                  } else {
                    if ((value[j]).toString() == "}") {
                      depth -= 1;
                    }
                  }
                  j += 1;
                }
                inner = _substring(value, i + 2, j - 1);
                if (_trimBoth(inner, " \t\n\r") == "") {
                  result.add("\${ }");
                } else {
                  try {
                    parser = newParser(_trimLeft(inner, " \t\n|"), false, false);
                    parsed = parser.parseList(true);
                    if (parsed != null) {
                      formatted = _formatCmdsubNode(parsed, 0, false, false, false);
                      formatted = _trimRight(formatted, ";");
                      String terminator = "";
                      if (_trimRight(inner, " \t").endsWith("\n")) {
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
                      result.add("\${ }");
                    }
                  } on Exception {
                    result.add(_substring(value, i, j));
                  }
                }
                i = j;
              } else {
                if (_isExpansionStart(value, i, "\${") && !(_isBackslashEscaped(value, i))) {
                  j = i + 2;
                  depth = 1;
                  dynamic braceQuote = newQuoteState();
                  while (j < value.length && depth > 0) {
                    String c = (value[j]).toString(); 
                    if (c == "\\" && j + 1 < value.length && !(braceQuote.single)) {
                      j += 2;
                      continue;
                    }
                    if (c == "'" && !(braceQuote.double)) {
                      braceQuote.single = !(braceQuote.single);
                    } else {
                      if (c == "\"" && !(braceQuote.single)) {
                        braceQuote.double = !(braceQuote.double);
                      } else {
                        if (!(braceQuote.inQuotes())) {
                          if (_isExpansionStart(value, j, "\$(") && !(_startsWithAt(value, j, "\$(("))) {
                            j = _findCmdsubEnd(value, j + 2);
                            continue;
                          }
                          if (c == "{") {
                            depth += 1;
                          } else {
                            if (c == "}") {
                              depth -= 1;
                            }
                          }
                        }
                      }
                    }
                    j += 1;
                  }
                  if (depth > 0) {
                    inner = _substring(value, i + 2, j);
                  } else {
                    inner = _substring(value, i + 2, j - 1);
                  }
                  String formattedInner = this._formatCommandSubstitutions(inner, false); 
                  formattedInner = this._normalizeExtglobWhitespace(formattedInner);
                  if (depth == 0) {
                    result.add("\${" + formattedInner + "}");
                  } else {
                    result.add("\${" + formattedInner);
                  }
                  i = j;
                } else {
                  if ((value[i]).toString() == "\"") {
                    mainQuote.double = !(mainQuote.double);
                    result.add((value[i]).toString());
                    i += 1;
                  } else {
                    if ((value[i]).toString() == "'" && !(mainQuote.double)) {
                      j = i + 1;
                      while (j < value.length && (value[j]).toString() != "'") {
                        j += 1;
                      }
                      if (j < value.length) {
                        j += 1;
                      }
                      result.add(_substring(value, i, j));
                      i = j;
                    } else {
                      result.add((value[i]).toString());
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

  String _normalizeExtglobWhitespace(String value) {
    List<String> result = <String>[]; 
    int i = 0; 
    dynamic extglobQuote = newQuoteState();
    int deprecatedArithDepth = 0; 
    while (i < value.length) {
      if ((value[i]).toString() == "\"") {
        extglobQuote.double = !(extglobQuote.double);
        result.add((value[i]).toString());
        i += 1;
        continue;
      }
      if (_startsWithAt(value, i, "\$[") && !(_isBackslashEscaped(value, i))) {
        deprecatedArithDepth += 1;
        result.add((value[i]).toString());
        i += 1;
        continue;
      }
      if ((value[i]).toString() == "]" && deprecatedArithDepth > 0) {
        deprecatedArithDepth -= 1;
        result.add((value[i]).toString());
        i += 1;
        continue;
      }
      if (i + 1 < value.length && (value[i + 1]).toString() == "(") {
        String prefixChar = (value[i]).toString(); 
        if ("><".contains(prefixChar) && !(extglobQuote.double) && deprecatedArithDepth == 0) {
          result.add(prefixChar);
          result.add("(");
          i += 2;
          int depth = 1; 
          List<String> patternParts = <String>[]; 
          List<String> currentPart = <String>[]; 
          bool hasPipe = false; 
          while (i < value.length && depth > 0) {
            if ((value[i]).toString() == "\\" && i + 1 < value.length) {
              currentPart.add(_safeSubstring(value, i, i + 2));
              i += 2;
              continue;
            } else {
              if ((value[i]).toString() == "(") {
                depth += 1;
                currentPart.add((value[i]).toString());
                i += 1;
              } else {
                String partContent = "";
                if ((value[i]).toString() == ")") {
                  depth -= 1;
                  if (depth == 0) {
                    partContent = currentPart.join("");
                    if (partContent.contains("<<")) {
                      patternParts.add(partContent);
                    } else {
                      if (hasPipe) {
                        patternParts.add(_trimBoth(partContent, " \t\n\r"));
                      } else {
                        patternParts.add(partContent);
                      }
                    }
                    break;
                  }
                  currentPart.add((value[i]).toString());
                  i += 1;
                } else {
                  if ((value[i]).toString() == "|" && depth == 1) {
                    if (i + 1 < value.length && (value[i + 1]).toString() == "|") {
                      currentPart.add("||");
                      i += 2;
                    } else {
                      hasPipe = true;
                      partContent = currentPart.join("");
                      if (partContent.contains("<<")) {
                        patternParts.add(partContent);
                      } else {
                        patternParts.add(_trimBoth(partContent, " \t\n\r"));
                      }
                      currentPart = <String>[];
                      i += 1;
                    }
                  } else {
                    currentPart.add((value[i]).toString());
                    i += 1;
                  }
                }
              }
            }
          }
          result.add(patternParts.join(" | "));
          if (depth == 0) {
            result.add(")");
            i += 1;
          }
          continue;
        }
      }
      result.add((value[i]).toString());
      i += 1;
    }
    return result.join("");
  }

  String getCondFormattedValue() {
    String value = this._expandAllAnsiCQuotes(this.value); 
    value = this._stripLocaleStringDollars(value);
    value = this._formatCommandSubstitutions(value, false);
    value = this._normalizeExtglobWhitespace(value);
    value = value.replaceAll("\u0001", "\u0001\u0001");
    return _trimRight(value, "\n");
  }

  String getKind() {
    return this.kind;
  }
}

class Command implements Node {
  late List<Word> words;
  late List<Node> redirects;
  late String kind;

  Command(List<Word> words, List<Node> redirects, String kind) {
    this.words = words;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    List<String> parts = <String>[]; 
    for (final w in this.words) {
      parts.add(w.toSexp());
    }
    for (final r in this.redirects) {
      parts.add(r.toSexp());
    }
    String inner = parts.join(" "); 
    if (!((inner.isNotEmpty))) {
      return "(command)";
    }
    return "(command " + inner + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class Pipeline implements Node {
  late List<Node> commands;
  late String kind;

  Pipeline(List<Node> commands, String kind) {
    this.commands = commands;
    this.kind = kind;
  }

  String toSexp() {
    if (this.commands.length == 1) {
      return this.commands[0].toSexp();
    }
    List<(Node, bool)> cmds = <(Node, bool)>[]; 
    int i = 0; 
    dynamic cmd;
    while (i < this.commands.length) {
      cmd = this.commands[i];
      switch (cmd) {
        case PipeBoth cmdPipeBoth:
          i += 1;
          continue;
      }
      bool needsRedirect = i + 1 < this.commands.length && this.commands[i + 1].kind == "pipe-both"; 
      cmds.add((cmd, needsRedirect));
      i += 1;
    }
    dynamic pair;
    bool needs = false;
    if (cmds.length == 1) {
      pair = cmds[0];
      cmd = pair.$1;
      needs = pair.$2;
      return this._cmdSexp(cmd, needs);
    }
    (Node, bool) lastPair = cmds[cmds.length - 1]; 
    Node lastCmd = lastPair.$1; 
    bool lastNeeds = lastPair.$2; 
    String result = this._cmdSexp(lastCmd, lastNeeds); 
    int j = cmds.length - 2; 
    while (j >= 0) {
      pair = cmds[j];
      cmd = pair.$1;
      needs = pair.$2;
      if (needs && cmd.kind != "command") {
        result = "(pipe " + cmd.toSexp() + " (redirect \">&\" 1) " + result + ")";
      } else {
        result = "(pipe " + this._cmdSexp(cmd, needs) + " " + result + ")";
      }
      j -= 1;
    }
    return result;
  }

  String _cmdSexp(Node cmd, bool needsRedirect) {
    if (!(needsRedirect)) {
      return cmd.toSexp();
    }
    switch (cmd) {
      case Command cmdCommand:
        List<String> parts = <String>[]; 
        for (final w in cmdCommand.words) {
          parts.add(w.toSexp());
        }
        for (final r in cmdCommand.redirects) {
          parts.add(r.toSexp());
        }
        parts.add("(redirect \">&\" 1)");
        return "(command " + parts.join(" ") + ")";
    }
    return cmd.toSexp();
  }

  String getKind() {
    return this.kind;
  }
}

class List_ implements Node {
  late List<Node> parts;
  late String kind;

  List_(List<Node> parts, String kind) {
    this.parts = parts;
    this.kind = kind;
  }

  String toSexp() {
    List<Node> parts = List<Node>.from(this.parts); 
    Map<String, String> opNames = <String, String>{"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}; 
    while (parts.length > 1 && parts[parts.length - 1].kind == "operator" && ((parts[parts.length - 1] as Operator).op == ";" || (parts[parts.length - 1] as Operator).op == "\n")) {
      parts = _sublist(parts, 0, parts.length - 1);
    }
    if (parts.length == 1) {
      return parts[0].toSexp();
    }
    if (parts[parts.length - 1].kind == "operator" && (parts[parts.length - 1] as Operator).op == "&") {
      for (int i = parts.length - 3; i > 0; i += -2) {
        if (parts[i].kind == "operator" && ((parts[i] as Operator).op == ";" || (parts[i] as Operator).op == "\n")) {
          List<Node> left = _sublist(parts, 0, i); 
          List<Node> right = _sublist(parts, i + 1, parts.length - 1); 
          String leftSexp = "";
          if (left.length > 1) {
            leftSexp = List_(left, "list").toSexp();
          } else {
            leftSexp = left[0].toSexp();
          }
          String rightSexp = "";
          if (right.length > 1) {
            rightSexp = List_(right, "list").toSexp();
          } else {
            rightSexp = right[0].toSexp();
          }
          return "(semi " + leftSexp + " (background " + rightSexp + "))";
        }
      }
      List<Node> innerParts = _sublist(parts, 0, parts.length - 1); 
      if (innerParts.length == 1) {
        return "(background " + innerParts[0].toSexp() + ")";
      }
      List_ innerList = List_(innerParts, "list"); 
      return "(background " + innerList.toSexp() + ")";
    }
    return this._toSexpWithPrecedence(parts, opNames);
  }

  String _toSexpWithPrecedence(List<Node> parts, Map<String, String> opNames) {
    List<int> semiPositions = <int>[]; 
    for (int i = 0; i < parts.length; i += 1) {
      if (parts[i].kind == "operator" && ((parts[i] as Operator).op == ";" || (parts[i] as Operator).op == "\n")) {
        semiPositions.add(i);
      }
    }
    if ((semiPositions.isNotEmpty)) {
      List<List<Node>> segments = <List<Node>>[]; 
      int start = 0; 
      List<Node> seg = <Node>[];
      for (final pos in semiPositions) {
        seg = _sublist(parts, start, pos);
        if ((seg.isNotEmpty) && seg[0].kind != "operator") {
          segments.add(seg);
        }
        start = pos + 1;
      }
      seg = _sublist(parts, start, parts.length);
      if ((seg.isNotEmpty) && seg[0].kind != "operator") {
        segments.add(seg);
      }
      if (!((segments.isNotEmpty))) {
        return "()";
      }
      String result = this._toSexpAmpAndHigher(segments[0], opNames); 
      for (int i = 1; i < segments.length; i += 1) {
        result = "(semi " + result + " " + this._toSexpAmpAndHigher(segments[i], opNames) + ")";
      }
      return result;
    }
    return this._toSexpAmpAndHigher(parts, opNames);
  }

  String _toSexpAmpAndHigher(List<Node> parts, Map<String, String> opNames) {
    if (parts.length == 1) {
      return parts[0].toSexp();
    }
    List<int> ampPositions = <int>[]; 
    for (int i = 1; i < parts.length - 1; i += 2) {
      if (parts[i].kind == "operator" && (parts[i] as Operator).op == "&") {
        ampPositions.add(i);
      }
    }
    if ((ampPositions.isNotEmpty)) {
      List<List<Node>> segments = <List<Node>>[]; 
      int start = 0; 
      for (final pos in ampPositions) {
        segments.add(_sublist(parts, start, pos));
        start = pos + 1;
      }
      segments.add(_sublist(parts, start, parts.length));
      String result = this._toSexpAndOr(segments[0], opNames); 
      for (int i = 1; i < segments.length; i += 1) {
        result = "(background " + result + " " + this._toSexpAndOr(segments[i], opNames) + ")";
      }
      return result;
    }
    return this._toSexpAndOr(parts, opNames);
  }

  String _toSexpAndOr(List<Node> parts, Map<String, String> opNames) {
    if (parts.length == 1) {
      return parts[0].toSexp();
    }
    String result = parts[0].toSexp(); 
    for (int i = 1; i < parts.length - 1; i += 2) {
      Node op = parts[i]; 
      Node cmd = parts[i + 1]; 
      String opName = (opNames[(op as Operator).op] ?? (op as Operator).op); 
      result = "(" + opName + " " + result + " " + cmd.toSexp() + ")";
    }
    return result;
  }

  String getKind() {
    return this.kind;
  }
}

class Operator implements Node {
  late String op;
  late String kind;

  Operator(String op, String kind) {
    this.op = op;
    this.kind = kind;
  }

  String toSexp() {
    Map<String, String> names = <String, String>{"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}; 
    return "(" + (names[this.op] ?? this.op) + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class PipeBoth implements Node {
  late String kind;

  PipeBoth(String kind) {
    this.kind = kind;
  }

  String toSexp() {
    return "(pipe-both)";
  }

  String getKind() {
    return this.kind;
  }
}

class Empty implements Node {
  late String kind;

  Empty(String kind) {
    this.kind = kind;
  }

  String toSexp() {
    return "";
  }

  String getKind() {
    return this.kind;
  }
}

class Comment implements Node {
  late String text;
  late String kind;

  Comment(String text, String kind) {
    this.text = text;
    this.kind = kind;
  }

  String toSexp() {
    return "";
  }

  String getKind() {
    return this.kind;
  }
}

class Redirect implements Node {
  late String op;
  late Word target;
  late int fd;
  late String kind;

  Redirect(String op, Word? target, int fd, String kind) {
    this.op = op;
    if (target != null) this.target = target;
    this.fd = fd;
    this.kind = kind;
  }

  String toSexp() {
    String op = _trimLeft(this.op, "0123456789"); 
    if (op.startsWith("{")) {
      int j = 1; 
      if (j < op.length && (((op[j]).toString().isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch((op[j]).toString())) || (op[j]).toString() == "_")) {
        j += 1;
        while (j < op.length && (((op[j]).toString().isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch((op[j]).toString())) || (op[j]).toString() == "_")) {
          j += 1;
        }
        if (j < op.length && (op[j]).toString() == "[") {
          j += 1;
          while (j < op.length && (op[j]).toString() != "]") {
            j += 1;
          }
          if (j < op.length && (op[j]).toString() == "]") {
            j += 1;
          }
        }
        if (j < op.length && (op[j]).toString() == "}") {
          op = _substring(op, j + 1, op.length);
        }
      }
    }
    String targetVal = this.target.value; 
    targetVal = this.target._expandAllAnsiCQuotes(targetVal);
    targetVal = this.target._stripLocaleStringDollars(targetVal);
    targetVal = this.target._formatCommandSubstitutions(targetVal, false);
    targetVal = this.target._stripArithLineContinuations(targetVal);
    if (targetVal.endsWith("\\") && !(targetVal.endsWith("\\\\"))) {
      targetVal = targetVal + "\\";
    }
    if (targetVal.startsWith("&")) {
      if (op == ">") {
        op = ">&";
      } else {
        if (op == "<") {
          op = "<&";
        }
      }
      String raw = _substring(targetVal, 1, targetVal.length); 
      if ((raw.isNotEmpty && RegExp(r'^\d+$').hasMatch(raw)) && int.parse(raw, radix: 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + int.parse(raw, radix: 10).toString() + ")";
      }
      if (raw.endsWith("-") && (_safeSubstring(raw, 0, raw.length - 1).isNotEmpty && RegExp(r'^\d+$').hasMatch(_safeSubstring(raw, 0, raw.length - 1))) && int.parse(_safeSubstring(raw, 0, raw.length - 1), radix: 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + int.parse(_safeSubstring(raw, 0, raw.length - 1), radix: 10).toString() + ")";
      }
      if (targetVal == "&-") {
        return "(redirect \">&-\" 0)";
      }
      String fdTarget = (raw.endsWith("-") ? _safeSubstring(raw, 0, raw.length - 1) : raw); 
      return "(redirect \"" + op + "\" \"" + fdTarget + "\")";
    }
    if (op == ">&" || op == "<&") {
      if ((targetVal.isNotEmpty && RegExp(r'^\d+$').hasMatch(targetVal)) && int.parse(targetVal, radix: 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + int.parse(targetVal, radix: 10).toString() + ")";
      }
      if (targetVal == "-") {
        return "(redirect \">&-\" 0)";
      }
      if (targetVal.endsWith("-") && (_safeSubstring(targetVal, 0, targetVal.length - 1).isNotEmpty && RegExp(r'^\d+$').hasMatch(_safeSubstring(targetVal, 0, targetVal.length - 1))) && int.parse(_safeSubstring(targetVal, 0, targetVal.length - 1), radix: 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + int.parse(_safeSubstring(targetVal, 0, targetVal.length - 1), radix: 10).toString() + ")";
      }
      String outVal = (targetVal.endsWith("-") ? _safeSubstring(targetVal, 0, targetVal.length - 1) : targetVal); 
      return "(redirect \"" + op + "\" \"" + outVal + "\")";
    }
    return "(redirect \"" + op + "\" \"" + targetVal + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class HereDoc implements Node {
  late String delimiter;
  late String content;
  late bool stripTabs;
  late bool quoted;
  late int fd;
  late bool complete;
  late int _startPos;
  late String kind;

  HereDoc(String delimiter, String content, bool stripTabs, bool quoted, int fd, bool complete, int _startPos, String kind) {
    this.delimiter = delimiter;
    this.content = content;
    this.stripTabs = stripTabs;
    this.quoted = quoted;
    this.fd = fd;
    this.complete = complete;
    this._startPos = _startPos;
    this.kind = kind;
  }

  String toSexp() {
    String op = (this.stripTabs ? "<<-" : "<<"); 
    String content = this.content; 
    if (content.endsWith("\\") && !(content.endsWith("\\\\"))) {
      content = content + "\\";
    }
    return "(redirect \"${op}\" \"${content}\")";
  }

  String getKind() {
    return this.kind;
  }
}

class Subshell implements Node {
  dynamic body;
  List<Node>? redirects;
  late String kind;

  Subshell(dynamic body, List<Node>? redirects, String kind) {
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String base = "(subshell " + this.body.toSexp() + ")"; 
    return _appendRedirects(base, this.redirects!);
  }

  String getKind() {
    return this.kind;
  }
}

class BraceGroup implements Node {
  dynamic body;
  List<Node>? redirects;
  late String kind;

  BraceGroup(dynamic body, List<Node>? redirects, String kind) {
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String base = "(brace-group " + this.body.toSexp() + ")"; 
    return _appendRedirects(base, this.redirects!);
  }

  String getKind() {
    return this.kind;
  }
}

class If implements Node {
  dynamic condition;
  dynamic thenBody;
  Node? elseBody;
  late List<Node> redirects;
  late String kind;

  If(dynamic condition, dynamic thenBody, Node? elseBody, List<Node> redirects, String kind) {
    if (condition != null) this.condition = condition;
    if (thenBody != null) this.thenBody = thenBody;
    this.elseBody = elseBody;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String result = "(if " + this.condition.toSexp() + " " + this.thenBody.toSexp(); 
    if (this.elseBody != null) {
      result = result + " " + this.elseBody!.toSexp();
    }
    result = result + ")";
    for (final r in this.redirects) {
      result = result + " " + r.toSexp();
    }
    return result;
  }

  String getKind() {
    return this.kind;
  }
}

class While implements Node {
  dynamic condition;
  dynamic body;
  late List<Node> redirects;
  late String kind;

  While(dynamic condition, dynamic body, List<Node> redirects, String kind) {
    if (condition != null) this.condition = condition;
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String base = "(while " + this.condition.toSexp() + " " + this.body.toSexp() + ")"; 
    return _appendRedirects(base, this.redirects);
  }

  String getKind() {
    return this.kind;
  }
}

class Until implements Node {
  dynamic condition;
  dynamic body;
  late List<Node> redirects;
  late String kind;

  Until(dynamic condition, dynamic body, List<Node> redirects, String kind) {
    if (condition != null) this.condition = condition;
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String base = "(until " + this.condition.toSexp() + " " + this.body.toSexp() + ")"; 
    return _appendRedirects(base, this.redirects);
  }

  String getKind() {
    return this.kind;
  }
}

class For implements Node {
  late String var_;
  List<Word>? words;
  dynamic body;
  late List<Node> redirects;
  late String kind;

  For(String var_, List<Word>? words, dynamic body, List<Node> redirects, String kind) {
    this.var_ = var_;
    this.words = words;
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String suffix = ""; 
    if ((this.redirects.isNotEmpty)) {
      List<String> redirectParts = <String>[]; 
      for (final r in this.redirects) {
        redirectParts.add(r.toSexp());
      }
      suffix = " " + redirectParts.join(" ");
    }
    Word tempWord = Word(this.var_, <Node>[], "word"); 
    String varFormatted = tempWord._formatCommandSubstitutions(this.var_, false); 
    String varEscaped = varFormatted.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
    if (this.words == null) {
      return "(for (word \"" + varEscaped + "\") (in (word \"\\\"\$@\\\"\")) " + this.body.toSexp() + ")" + suffix;
    } else {
      if (this.words!.length == 0) {
        return "(for (word \"" + varEscaped + "\") (in) " + this.body.toSexp() + ")" + suffix;
      } else {
        List<String> wordParts = <String>[]; 
        for (final w in (this.words ?? <Word>[])) {
          wordParts.add(w.toSexp());
        }
        String wordStrs = wordParts.join(" "); 
        return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + this.body.toSexp() + ")" + suffix;
      }
    }
  }

  String getKind() {
    return this.kind;
  }
}

class ForArith implements Node {
  late String init;
  late String cond;
  late String incr;
  dynamic body;
  late List<Node> redirects;
  late String kind;

  ForArith(String init, String cond, String incr, dynamic body, List<Node> redirects, String kind) {
    this.init = init;
    this.cond = cond;
    this.incr = incr;
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String suffix = ""; 
    if ((this.redirects.isNotEmpty)) {
      List<String> redirectParts = <String>[]; 
      for (final r in this.redirects) {
        redirectParts.add(r.toSexp());
      }
      suffix = " " + redirectParts.join(" ");
    }
    String initVal = ((this.init.isNotEmpty) ? this.init : "1"); 
    String condVal = ((this.cond.isNotEmpty) ? this.cond : "1"); 
    String incrVal = ((this.incr.isNotEmpty) ? this.incr : "1"); 
    String initStr = _formatArithVal(initVal); 
    String condStr = _formatArithVal(condVal); 
    String incrStr = _formatArithVal(incrVal); 
    String bodyStr = this.body.toSexp(); 
    return "(arith-for (init (word \"${initStr}\")) (test (word \"${condStr}\")) (step (word \"${incrStr}\")) ${bodyStr})${suffix}";
  }

  String getKind() {
    return this.kind;
  }
}

class Select implements Node {
  late String var_;
  List<Word>? words;
  dynamic body;
  late List<Node> redirects;
  late String kind;

  Select(String var_, List<Word>? words, dynamic body, List<Node> redirects, String kind) {
    this.var_ = var_;
    this.words = words;
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    String suffix = ""; 
    if ((this.redirects.isNotEmpty)) {
      List<String> redirectParts = <String>[]; 
      for (final r in this.redirects) {
        redirectParts.add(r.toSexp());
      }
      suffix = " " + redirectParts.join(" ");
    }
    String varEscaped = this.var_.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
    String inClause = "";
    if (this.words != null) {
      List<String> wordParts = <String>[]; 
      for (final w in (this.words ?? <Word>[])) {
        wordParts.add(w.toSexp());
      }
      String wordStrs = wordParts.join(" "); 
      if ((this.words?.isNotEmpty ?? false)) {
        inClause = "(in " + wordStrs + ")";
      } else {
        inClause = "(in)";
      }
    } else {
      inClause = "(in (word \"\\\"\$@\\\"\"))";
    }
    return "(select (word \"" + varEscaped + "\") " + inClause + " " + this.body.toSexp() + ")" + suffix;
  }

  String getKind() {
    return this.kind;
  }
}

class Case implements Node {
  late Word word;
  late List<CasePattern> patterns;
  late List<Node> redirects;
  late String kind;

  Case(Word? word, List<CasePattern> patterns, List<Node> redirects, String kind) {
    if (word != null) this.word = word;
    this.patterns = patterns;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    List<String> parts = <String>[]; 
    parts.add("(case " + this.word.toSexp());
    for (final p in this.patterns) {
      parts.add(p.toSexp());
    }
    String base = parts.join(" ") + ")"; 
    return _appendRedirects(base, this.redirects);
  }

  String getKind() {
    return this.kind;
  }
}

class CasePattern implements Node {
  late String pattern;
  Node? body;
  late String terminator;
  late String kind;

  CasePattern(String pattern, Node? body, String terminator, String kind) {
    this.pattern = pattern;
    this.body = body;
    this.terminator = terminator;
    this.kind = kind;
  }

  String toSexp() {
    List<String> alternatives = <String>[]; 
    List<String> current = <String>[]; 
    int i = 0; 
    int depth = 0; 
    while (i < this.pattern.length) {
      String ch = (this.pattern[i]).toString(); 
      if (ch == "\\" && i + 1 < this.pattern.length) {
        current.add(_substring(this.pattern, i, i + 2));
        i += 2;
      } else {
        if ((ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!") && i + 1 < this.pattern.length && (this.pattern[i + 1]).toString() == "(") {
          current.add(ch);
          current.add("(");
          depth += 1;
          i += 2;
        } else {
          if (_isExpansionStart(this.pattern, i, "\$(")) {
            current.add(ch);
            current.add("(");
            depth += 1;
            i += 2;
          } else {
            if (ch == "(" && depth > 0) {
              current.add(ch);
              depth += 1;
              i += 1;
            } else {
              if (ch == ")" && depth > 0) {
                current.add(ch);
                depth -= 1;
                i += 1;
              } else {
                int result0 = 0;
                List<String> result1 = <String>[];
                if (ch == "[") {
                  final _tuple20 = _consumeBracketClass(this.pattern, i, depth);
                  result0 = _tuple20.$1;
                  result1 = _tuple20.$2;
                  bool result2 = _tuple20.$3;
                  i = result0;
                  current.addAll(result1);
                } else {
                  if (ch == "'" && depth == 0) {
                    final _tuple21 = _consumeSingleQuote(this.pattern, i);
                    result0 = _tuple21.$1;
                    result1 = _tuple21.$2;
                    i = result0;
                    current.addAll(result1);
                  } else {
                    if (ch == "\"" && depth == 0) {
                      final _tuple22 = _consumeDoubleQuote(this.pattern, i);
                      result0 = _tuple22.$1;
                      result1 = _tuple22.$2;
                      i = result0;
                      current.addAll(result1);
                    } else {
                      if (ch == "|" && depth == 0) {
                        alternatives.add(current.join(""));
                        current = <String>[];
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
    alternatives.add(current.join(""));
    List<String> wordList = <String>[]; 
    for (final alt in alternatives) {
      wordList.add(Word(alt, <Node>[], "word").toSexp());
    }
    String patternStr = wordList.join(" "); 
    List<String> parts = <String>["(pattern (" + patternStr + ")"]; 
    if (this.body != null) {
      parts.add(" " + this.body!.toSexp());
    } else {
      parts.add(" ()");
    }
    parts.add(")");
    return parts.join("");
  }

  String getKind() {
    return this.kind;
  }
}

class Function_ implements Node {
  late String name;
  dynamic body;
  late String kind;

  Function_(String name, dynamic body, String kind) {
    this.name = name;
    if (body != null) this.body = body;
    this.kind = kind;
  }

  String toSexp() {
    return "(function \"" + this.name + "\" " + this.body.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ParamExpansion implements Node {
  late String param;
  late String op;
  late String arg;
  late String kind;

  ParamExpansion(String param, String op, String arg, String kind) {
    this.param = param;
    this.op = op;
    this.arg = arg;
    this.kind = kind;
  }

  String toSexp() {
    String escapedParam = this.param.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
    if (this.op != "") {
      String escapedOp = this.op.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
      String argVal = "";
      if (this.arg != "") {
        argVal = this.arg;
      } else {
        argVal = "";
      }
      String escapedArg = argVal.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
      return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
    }
    return "(param \"" + escapedParam + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class ParamLength implements Node {
  late String param;
  late String kind;

  ParamLength(String param, String kind) {
    this.param = param;
    this.kind = kind;
  }

  String toSexp() {
    String escaped = this.param.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
    return "(param-len \"" + escaped + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class ParamIndirect implements Node {
  late String param;
  late String op;
  late String arg;
  late String kind;

  ParamIndirect(String param, String op, String arg, String kind) {
    this.param = param;
    this.op = op;
    this.arg = arg;
    this.kind = kind;
  }

  String toSexp() {
    String escaped = this.param.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
    if (this.op != "") {
      String escapedOp = this.op.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
      String argVal = "";
      if (this.arg != "") {
        argVal = this.arg;
      } else {
        argVal = "";
      }
      String escapedArg = argVal.replaceAll("\\", "\\\\").replaceAll("\"", "\\\""); 
      return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
    }
    return "(param-indirect \"" + escaped + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class CommandSubstitution implements Node {
  dynamic command;
  late bool brace;
  late String kind;

  CommandSubstitution(dynamic command, bool brace, String kind) {
    if (command != null) this.command = command;
    this.brace = brace;
    this.kind = kind;
  }

  String toSexp() {
    if (this.brace) {
      return "(funsub " + this.command.toSexp() + ")";
    }
    return "(cmdsub " + this.command.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithmeticExpansion implements Node {
  Node? expression;
  late String kind;

  ArithmeticExpansion(Node? expression, String kind) {
    this.expression = expression;
    this.kind = kind;
  }

  String toSexp() {
    if (this.expression == null) {
      return "(arith)";
    }
    return "(arith " + this.expression!.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithmeticCommand implements Node {
  Node? expression;
  late List<Node> redirects;
  late String rawContent;
  late String kind;

  ArithmeticCommand(Node? expression, List<Node> redirects, String rawContent, String kind) {
    this.expression = expression;
    this.redirects = redirects;
    this.rawContent = rawContent;
    this.kind = kind;
  }

  String toSexp() {
    String formatted = Word(this.rawContent, <Node>[], "word")._formatCommandSubstitutions(this.rawContent, true); 
    String escaped = formatted.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n").replaceAll("\t", "\\t"); 
    String result = "(arith (word \"" + escaped + "\"))"; 
    if ((this.redirects.isNotEmpty)) {
      List<String> redirectParts = <String>[]; 
      for (final r in this.redirects) {
        redirectParts.add(r.toSexp());
      }
      String redirectSexps = redirectParts.join(" "); 
      return result + " " + redirectSexps;
    }
    return result;
  }

  String getKind() {
    return this.kind;
  }
}

class ArithNumber implements Node {
  late String value;
  late String kind;

  ArithNumber(String value, String kind) {
    this.value = value;
    this.kind = kind;
  }

  String toSexp() {
    return "(number \"" + this.value + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithEmpty implements Node {
  late String kind;

  ArithEmpty(String kind) {
    this.kind = kind;
  }

  String toSexp() {
    return "(empty)";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithVar implements Node {
  late String name;
  late String kind;

  ArithVar(String name, String kind) {
    this.name = name;
    this.kind = kind;
  }

  String toSexp() {
    return "(var \"" + this.name + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithBinaryOp implements Node {
  late String op;
  dynamic left;
  dynamic right;
  late String kind;

  ArithBinaryOp(String op, dynamic left, dynamic right, String kind) {
    this.op = op;
    if (left != null) this.left = left;
    if (right != null) this.right = right;
    this.kind = kind;
  }

  String toSexp() {
    return "(binary-op \"" + this.op + "\" " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithUnaryOp implements Node {
  late String op;
  dynamic operand;
  late String kind;

  ArithUnaryOp(String op, dynamic operand, String kind) {
    this.op = op;
    if (operand != null) this.operand = operand;
    this.kind = kind;
  }

  String toSexp() {
    return "(unary-op \"" + this.op + "\" " + this.operand.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithPreIncr implements Node {
  dynamic operand;
  late String kind;

  ArithPreIncr(dynamic operand, String kind) {
    if (operand != null) this.operand = operand;
    this.kind = kind;
  }

  String toSexp() {
    return "(pre-incr " + this.operand.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithPostIncr implements Node {
  dynamic operand;
  late String kind;

  ArithPostIncr(dynamic operand, String kind) {
    if (operand != null) this.operand = operand;
    this.kind = kind;
  }

  String toSexp() {
    return "(post-incr " + this.operand.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithPreDecr implements Node {
  dynamic operand;
  late String kind;

  ArithPreDecr(dynamic operand, String kind) {
    if (operand != null) this.operand = operand;
    this.kind = kind;
  }

  String toSexp() {
    return "(pre-decr " + this.operand.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithPostDecr implements Node {
  dynamic operand;
  late String kind;

  ArithPostDecr(dynamic operand, String kind) {
    if (operand != null) this.operand = operand;
    this.kind = kind;
  }

  String toSexp() {
    return "(post-decr " + this.operand.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithAssign implements Node {
  late String op;
  dynamic target;
  dynamic value;
  late String kind;

  ArithAssign(String op, dynamic target, dynamic value, String kind) {
    this.op = op;
    if (target != null) this.target = target;
    if (value != null) this.value = value;
    this.kind = kind;
  }

  String toSexp() {
    return "(assign \"" + this.op + "\" " + this.target.toSexp() + " " + this.value.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithTernary implements Node {
  dynamic condition;
  dynamic ifTrue;
  dynamic ifFalse;
  late String kind;

  ArithTernary(dynamic condition, dynamic ifTrue, dynamic ifFalse, String kind) {
    if (condition != null) this.condition = condition;
    if (ifTrue != null) this.ifTrue = ifTrue;
    if (ifFalse != null) this.ifFalse = ifFalse;
    this.kind = kind;
  }

  String toSexp() {
    return "(ternary " + this.condition.toSexp() + " " + this.ifTrue.toSexp() + " " + this.ifFalse.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithComma implements Node {
  dynamic left;
  dynamic right;
  late String kind;

  ArithComma(dynamic left, dynamic right, String kind) {
    if (left != null) this.left = left;
    if (right != null) this.right = right;
    this.kind = kind;
  }

  String toSexp() {
    return "(comma " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithSubscript implements Node {
  late String array;
  dynamic index;
  late String kind;

  ArithSubscript(String array, dynamic index, String kind) {
    this.array = array;
    if (index != null) this.index = index;
    this.kind = kind;
  }

  String toSexp() {
    return "(subscript \"" + this.array + "\" " + this.index.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithEscape implements Node {
  late String char;
  late String kind;

  ArithEscape(String char, String kind) {
    this.char = char;
    this.kind = kind;
  }

  String toSexp() {
    return "(escape \"" + this.char + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithDeprecated implements Node {
  late String expression;
  late String kind;

  ArithDeprecated(String expression, String kind) {
    this.expression = expression;
    this.kind = kind;
  }

  String toSexp() {
    String escaped = this.expression.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n"); 
    return "(arith-deprecated \"" + escaped + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class ArithConcat implements Node {
  late List<Node> parts;
  late String kind;

  ArithConcat(List<Node> parts, String kind) {
    this.parts = parts;
    this.kind = kind;
  }

  String toSexp() {
    List<String> sexps = <String>[]; 
    for (final p in this.parts) {
      sexps.add(p.toSexp());
    }
    return "(arith-concat " + sexps.join(" ") + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class AnsiCQuote implements Node {
  late String content;
  late String kind;

  AnsiCQuote(String content, String kind) {
    this.content = content;
    this.kind = kind;
  }

  String toSexp() {
    String escaped = this.content.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n"); 
    return "(ansi-c \"" + escaped + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class LocaleString implements Node {
  late String content;
  late String kind;

  LocaleString(String content, String kind) {
    this.content = content;
    this.kind = kind;
  }

  String toSexp() {
    String escaped = this.content.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n"); 
    return "(locale \"" + escaped + "\")";
  }

  String getKind() {
    return this.kind;
  }
}

class ProcessSubstitution implements Node {
  late String direction;
  dynamic command;
  late String kind;

  ProcessSubstitution(String direction, dynamic command, String kind) {
    this.direction = direction;
    if (command != null) this.command = command;
    this.kind = kind;
  }

  String toSexp() {
    return "(procsub \"" + this.direction + "\" " + this.command.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class Negation implements Node {
  dynamic pipeline;
  late String kind;

  Negation(dynamic pipeline, String kind) {
    if (pipeline != null) this.pipeline = pipeline;
    this.kind = kind;
  }

  String toSexp() {
    if (this.pipeline == null) {
      return "(negation (command))";
    }
    return "(negation " + this.pipeline.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class Time implements Node {
  dynamic pipeline;
  late bool posix;
  late String kind;

  Time(dynamic pipeline, bool posix, String kind) {
    if (pipeline != null) this.pipeline = pipeline;
    this.posix = posix;
    this.kind = kind;
  }

  String toSexp() {
    if (this.pipeline == null) {
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

  String getKind() {
    return this.kind;
  }
}

class ConditionalExpr implements Node {
  dynamic body;
  late List<Node> redirects;
  late String kind;

  ConditionalExpr(dynamic body, List<Node> redirects, String kind) {
    if (body != null) this.body = body;
    this.redirects = redirects;
    this.kind = kind;
  }

  String toSexp() {
    dynamic body = this.body; 
    String result = "";
    switch (body) {
      case String bodyString:
        String escaped = bodyString.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n"); 
        result = "(cond \"" + escaped + "\")";
        break;
      default:
        result = "(cond " + body.toSexp() + ")";
        break;
    }
    if ((this.redirects.isNotEmpty)) {
      List<String> redirectParts = <String>[]; 
      for (final r in this.redirects) {
        redirectParts.add(r.toSexp());
      }
      String redirectSexps = redirectParts.join(" "); 
      return result + " " + redirectSexps;
    }
    return result;
  }

  String getKind() {
    return this.kind;
  }
}

class UnaryTest implements Node {
  late String op;
  late Word operand;
  late String kind;

  UnaryTest(String op, Word? operand, String kind) {
    this.op = op;
    if (operand != null) this.operand = operand;
    this.kind = kind;
  }

  String toSexp() {
    String operandVal = this.operand.getCondFormattedValue(); 
    return "(cond-unary \"" + this.op + "\" (cond-term \"" + operandVal + "\"))";
  }

  String getKind() {
    return this.kind;
  }
}

class BinaryTest implements Node {
  late String op;
  late Word left;
  late Word right;
  late String kind;

  BinaryTest(String op, Word? left, Word? right, String kind) {
    this.op = op;
    if (left != null) this.left = left;
    if (right != null) this.right = right;
    this.kind = kind;
  }

  String toSexp() {
    String leftVal = this.left.getCondFormattedValue(); 
    String rightVal = this.right.getCondFormattedValue(); 
    return "(cond-binary \"" + this.op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))";
  }

  String getKind() {
    return this.kind;
  }
}

class CondAnd implements Node {
  dynamic left;
  dynamic right;
  late String kind;

  CondAnd(dynamic left, dynamic right, String kind) {
    if (left != null) this.left = left;
    if (right != null) this.right = right;
    this.kind = kind;
  }

  String toSexp() {
    return "(cond-and " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class CondOr implements Node {
  dynamic left;
  dynamic right;
  late String kind;

  CondOr(dynamic left, dynamic right, String kind) {
    if (left != null) this.left = left;
    if (right != null) this.right = right;
    this.kind = kind;
  }

  String toSexp() {
    return "(cond-or " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class CondNot implements Node {
  dynamic operand;
  late String kind;

  CondNot(dynamic operand, String kind) {
    if (operand != null) this.operand = operand;
    this.kind = kind;
  }

  String toSexp() {
    return this.operand.toSexp();
  }

  String getKind() {
    return this.kind;
  }
}

class CondParen implements Node {
  dynamic inner;
  late String kind;

  CondParen(dynamic inner, String kind) {
    if (inner != null) this.inner = inner;
    this.kind = kind;
  }

  String toSexp() {
    return "(cond-expr " + this.inner.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class Array implements Node {
  late List<Word> elements;
  late String kind;

  Array(List<Word> elements, String kind) {
    this.elements = elements;
    this.kind = kind;
  }

  String toSexp() {
    if (!((this.elements.isNotEmpty))) {
      return "(array)";
    }
    List<String> parts = <String>[]; 
    for (final e in this.elements) {
      parts.add(e.toSexp());
    }
    String inner = parts.join(" "); 
    return "(array " + inner + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class Coproc implements Node {
  dynamic command;
  late String name;
  late String kind;

  Coproc(dynamic command, String name, String kind) {
    if (command != null) this.command = command;
    this.name = name;
    this.kind = kind;
  }

  String toSexp() {
    String name = "";
    if ((this.name.isNotEmpty)) {
      name = this.name;
    } else {
      name = "COPROC";
    }
    return "(coproc \"" + name + "\" " + this.command.toSexp() + ")";
  }

  String getKind() {
    return this.kind;
  }
}

class Parser {
  late String source;
  late int pos;
  late int length;
  late List<HereDoc> _pendingHeredocs;
  late int _cmdsubHeredocEnd;
  late bool _sawNewlineInSingleQuote;
  late bool _inProcessSub;
  late bool _extglob;
  late ContextStack _ctx;
  late Lexer _lexer;
  late List<Token?> _tokenHistory;
  late int _parserState;
  late int _dolbraceState;
  late String _eofToken;
  late int _wordContext;
  late bool _atCommandStart;
  late bool _inArrayLiteral;
  late bool _inAssignBuiltin;
  late String _arithSrc;
  late int _arithPos;
  late int _arithLen;

  Parser(String source, int pos, int length, List<HereDoc> _pendingHeredocs, int _cmdsubHeredocEnd, bool _sawNewlineInSingleQuote, bool _inProcessSub, bool _extglob, ContextStack? _ctx, Lexer? _lexer, List<Token?> _tokenHistory, int _parserState, int _dolbraceState, String _eofToken, int _wordContext, bool _atCommandStart, bool _inArrayLiteral, bool _inAssignBuiltin, String _arithSrc, int _arithPos, int _arithLen) {
    this.source = source;
    this.pos = pos;
    this.length = length;
    this._pendingHeredocs = _pendingHeredocs;
    this._cmdsubHeredocEnd = _cmdsubHeredocEnd;
    this._sawNewlineInSingleQuote = _sawNewlineInSingleQuote;
    this._inProcessSub = _inProcessSub;
    this._extglob = _extglob;
    if (_ctx != null) this._ctx = _ctx;
    if (_lexer != null) this._lexer = _lexer;
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

  void _setState(int flag) {
    this._parserState = this._parserState | flag;
  }

  void _clearState(int flag) {
    this._parserState = this._parserState & ~flag;
  }

  bool _inState(int flag) {
    return this._parserState & flag != 0;
  }

  SavedParserState _saveParserState() {
    return SavedParserState(this._parserState, this._dolbraceState, this._pendingHeredocs, this._ctx.copyStack(), this._eofToken);
  }

  void _restoreParserState(SavedParserState saved) {
    this._parserState = saved.parserState;
    this._dolbraceState = saved.dolbraceState;
    this._eofToken = saved.eofToken;
    this._ctx.restoreFrom(saved.ctxStack);
  }

  void _recordToken(Token tok) {
    this._tokenHistory = <Token?>[tok, this._tokenHistory[0], this._tokenHistory[1], this._tokenHistory[2]];
  }

  void _updateDolbraceForOp(String op, bool hasParam) {
    if (this._dolbraceState == dolbracestateNone) {
      return;
    }
    if (op == "" || op.length == 0) {
      return;
    }
    String firstChar = (op[0]).toString(); 
    if (this._dolbraceState == dolbracestateParam && hasParam) {
      if ("%#^,".contains(firstChar)) {
        this._dolbraceState = dolbracestateQuote;
        return;
      }
      if (firstChar == "/") {
        this._dolbraceState = dolbracestateQuote2;
        return;
      }
    }
    if (this._dolbraceState == dolbracestateParam) {
      if ("#%^,~:-=?+/".contains(firstChar)) {
        this._dolbraceState = dolbracestateOp;
      }
    }
  }

  void _syncLexer() {
    if (this._lexer._tokenCache != null) {
      if (this._lexer._tokenCache!.pos != this.pos || this._lexer._cachedWordContext != this._wordContext || this._lexer._cachedAtCommandStart != this._atCommandStart || this._lexer._cachedInArrayLiteral != this._inArrayLiteral || this._lexer._cachedInAssignBuiltin != this._inAssignBuiltin) {
        this._lexer._tokenCache = null as dynamic;
      }
    }
    if (this._lexer.pos != this.pos) {
      this._lexer.pos = this.pos;
    }
    this._lexer._eofToken = this._eofToken;
    this._lexer._parserState = this._parserState;
    this._lexer._lastReadToken = this._tokenHistory[0];
    this._lexer._wordContext = this._wordContext;
    this._lexer._atCommandStart = this._atCommandStart;
    this._lexer._inArrayLiteral = this._inArrayLiteral;
    this._lexer._inAssignBuiltin = this._inAssignBuiltin;
  }

  void _syncParser() {
    this.pos = this._lexer.pos;
  }

  Token _lexPeekToken() {
    if (this._lexer._tokenCache != null && this._lexer._tokenCache!.pos == this.pos && this._lexer._cachedWordContext == this._wordContext && this._lexer._cachedAtCommandStart == this._atCommandStart && this._lexer._cachedInArrayLiteral == this._inArrayLiteral && this._lexer._cachedInAssignBuiltin == this._inAssignBuiltin) {
      return this._lexer._tokenCache!;
    }
    int savedPos = this.pos; 
    this._syncLexer();
    dynamic result = this._lexer.peekToken();
    this._lexer._cachedWordContext = this._wordContext;
    this._lexer._cachedAtCommandStart = this._atCommandStart;
    this._lexer._cachedInArrayLiteral = this._inArrayLiteral;
    this._lexer._cachedInAssignBuiltin = this._inAssignBuiltin;
    this._lexer._postReadPos = this._lexer.pos;
    this.pos = savedPos;
    return result;
  }

  Token _lexNextToken() {
    dynamic tok;
    if (this._lexer._tokenCache != null && this._lexer._tokenCache!.pos == this.pos && this._lexer._cachedWordContext == this._wordContext && this._lexer._cachedAtCommandStart == this._atCommandStart && this._lexer._cachedInArrayLiteral == this._inArrayLiteral && this._lexer._cachedInAssignBuiltin == this._inAssignBuiltin) {
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

  void _lexSkipBlanks() {
    this._syncLexer();
    this._lexer.skipBlanks();
    this._syncParser();
  }

  bool _lexSkipComment() {
    this._syncLexer();
    bool result = this._lexer._skipComment(); 
    this._syncParser();
    return result;
  }

  bool _lexIsCommandTerminator() {
    dynamic tok = this._lexPeekToken();
    int t = tok.type; 
    return t == tokentypeEof || t == tokentypeNewline || t == tokentypePipe || t == tokentypeSemi || t == tokentypeLparen || t == tokentypeRparen || t == tokentypeAmp;
  }

  (int, String) _lexPeekOperator() {
    dynamic tok = this._lexPeekToken();
    int t = tok.type; 
    if (t >= tokentypeSemi && t <= tokentypeGreater || t >= tokentypeAndAnd && t <= tokentypePipeAmp) {
      return (t, tok.value);
    }
    return (0, "");
  }

  String _lexPeekReservedWord() {
    dynamic tok = this._lexPeekToken();
    if (tok.type != tokentypeWord) {
      return "";
    }
    String word = tok.value; 
    if (word.endsWith("\\\n")) {
      word = _safeSubstring(word, 0, word.length - 2);
    }
    if (reservedWords.contains(word) || word == "{" || word == "}" || word == "[[" || word == "]]" || word == "!" || word == "time") {
      return word;
    }
    return "";
  }

  bool _lexIsAtReservedWord(String word) {
    String reserved = this._lexPeekReservedWord(); 
    return reserved == word;
  }

  bool _lexConsumeWord(String expected) {
    dynamic tok = this._lexPeekToken();
    if (tok.type != tokentypeWord) {
      return false;
    }
    String word = tok.value; 
    if (word.endsWith("\\\n")) {
      word = _safeSubstring(word, 0, word.length - 2);
    }
    if (word == expected) {
      this._lexNextToken();
      return true;
    }
    return false;
  }

  String _lexPeekCaseTerminator() {
    dynamic tok = this._lexPeekToken();
    int t = tok.type; 
    if (t == tokentypeSemiSemi) {
      return ";;";
    }
    if (t == tokentypeSemiAmp) {
      return ";&";
    }
    if (t == tokentypeSemiSemiAmp) {
      return ";;&";
    }
    return "";
  }

  bool atEnd() {
    return this.pos >= this.length;
  }

  String peek() {
    if (this.atEnd()) {
      return "";
    }
    return (this.source[this.pos]).toString();
  }

  String advance() {
    if (this.atEnd()) {
      return "";
    }
    String ch = (this.source[this.pos]).toString(); 
    this.pos += 1;
    return ch;
  }

  String peekAt(int offset) {
    int pos = this.pos + offset; 
    if (pos < 0 || pos >= this.length) {
      return "";
    }
    return (this.source[pos]).toString();
  }

  String lookahead(int n) {
    return _substring(this.source, this.pos, this.pos + n);
  }

  bool _isBangFollowedByProcsub() {
    if (this.pos + 2 >= this.length) {
      return false;
    }
    String nextChar = (this.source[this.pos + 1]).toString(); 
    if (nextChar != ">" && nextChar != "<") {
      return false;
    }
    return (this.source[this.pos + 2]).toString() == "(";
  }

  void skipWhitespace() {
    while (!(this.atEnd())) {
      this._lexSkipBlanks();
      if (this.atEnd()) {
        break;
      }
      String ch = this.peek(); 
      if (ch == "#") {
        this._lexSkipComment();
      } else {
        if (ch == "\\" && this.peekAt(1) == "\n") {
          this.advance();
          this.advance();
        } else {
          break;
        }
      }
    }
  }

  void skipWhitespaceAndNewlines() {
    while (!(this.atEnd())) {
      String ch = this.peek(); 
      if (_isWhitespace(ch)) {
        this.advance();
        if (ch == "\n") {
          this._gatherHeredocBodies();
          if (this._cmdsubHeredocEnd != -1 && this._cmdsubHeredocEnd > this.pos) {
            this.pos = this._cmdsubHeredocEnd;
            this._cmdsubHeredocEnd = -1;
          }
        }
      } else {
        if (ch == "#") {
          while (!(this.atEnd()) && this.peek() != "\n") {
            this.advance();
          }
        } else {
          if (ch == "\\" && this.peekAt(1) == "\n") {
            this.advance();
            this.advance();
          } else {
            break;
          }
        }
      }
    }
  }

  bool _atListTerminatingBracket() {
    if (this.atEnd()) {
      return false;
    }
    String ch = this.peek(); 
    if (this._eofToken != "" && ch == this._eofToken) {
      return true;
    }
    if (ch == ")") {
      return true;
    }
    if (ch == "}") {
      int nextPos = this.pos + 1; 
      if (nextPos >= this.length) {
        return true;
      }
      return _isWordEndContext((this.source[nextPos]).toString());
    }
    return false;
  }

  bool _atEofToken() {
    if (this._eofToken == "") {
      return false;
    }
    dynamic tok = this._lexPeekToken();
    if (this._eofToken == ")") {
      return tok.type == tokentypeRparen;
    }
    if (this._eofToken == "}") {
      return tok.type == tokentypeWord && tok.value == "}";
    }
    return false;
  }

  List<Node> _collectRedirects() {
    List<Node> redirects = <Node>[]; 
    while (true) {
      this.skipWhitespace();
      dynamic redirect = this.parseRedirect();
      if (redirect == null) {
        break;
      }
      redirects.add(redirect);
    }
    return ((redirects.isNotEmpty) ? redirects : <Node>[]);
  }

  Node _parseLoopBody(String context) {
    if (this.peek() == "{") {
      dynamic brace = this.parseBraceGroup();
      if (brace == null) {
        throw ParseError("Expected brace group body in ${context}", this._lexPeekToken().pos, 0);
      }
      return brace.body;
    }
    if (this._lexConsumeWord("do")) {
      dynamic body = this.parseListUntil(<String>{"done"});
      if (body == null) {
        throw ParseError("Expected commands after 'do'", this._lexPeekToken().pos, 0);
      }
      this.skipWhitespaceAndNewlines();
      if (!(this._lexConsumeWord("done"))) {
        throw ParseError("Expected 'done' to close ${context}", this._lexPeekToken().pos, 0);
      }
      return body;
    }
    throw ParseError("Expected 'do' or '{' in ${context}", this._lexPeekToken().pos, 0);
  }

  String peekWord() {
    int savedPos = this.pos; 
    this.skipWhitespace();
    if (this.atEnd() || _isMetachar(this.peek())) {
      this.pos = savedPos;
      return "";
    }
    List<String> chars = <String>[]; 
    while (!(this.atEnd()) && !(_isMetachar(this.peek()))) {
      String ch = this.peek(); 
      if (_isQuote(ch)) {
        break;
      }
      if (ch == "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "\n") {
        break;
      }
      if (ch == "\\" && this.pos + 1 < this.length) {
        chars.add(this.advance());
        chars.add(this.advance());
        continue;
      }
      chars.add(this.advance());
    }
    String word = "";
    if ((chars.isNotEmpty)) {
      word = chars.join("");
    } else {
      word = "";
    }
    this.pos = savedPos;
    return word;
  }

  bool consumeWord(String expected) {
    int savedPos = this.pos; 
    this.skipWhitespace();
    String word = this.peekWord(); 
    String keywordWord = word; 
    bool hasLeadingBrace = false; 
    if (word != "" && this._inProcessSub && word.length > 1 && (word[0]).toString() == "}") {
      keywordWord = word.substring(1);
      hasLeadingBrace = true;
    }
    if (keywordWord != expected) {
      this.pos = savedPos;
      return false;
    }
    this.skipWhitespace();
    if (hasLeadingBrace) {
      this.advance();
    }
    for (final _ in expected.codeUnits) {
      this.advance();
    }
    while (this.peek() == "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "\n") {
      this.advance();
      this.advance();
    }
    return true;
  }

  bool _isWordTerminator(int ctx, String ch, int bracketDepth, int parenDepth) {
    this._syncLexer();
    return this._lexer._isWordTerminator(ctx, ch, bracketDepth, parenDepth);
  }

  void _scanDoubleQuote(List<String> chars, List<Node> parts, int start, bool handleLineContinuation) {
    chars.add("\"");
    while (!(this.atEnd()) && this.peek() != "\"") {
      String c = this.peek(); 
      if (c == "\\" && this.pos + 1 < this.length) {
        String nextC = (this.source[this.pos + 1]).toString(); 
        if (handleLineContinuation && nextC == "\n") {
          this.advance();
          this.advance();
        } else {
          chars.add(this.advance());
          chars.add(this.advance());
        }
      } else {
        if (c == "\$") {
          if (!(this._parseDollarExpansion(chars, parts, true))) {
            chars.add(this.advance());
          }
        } else {
          chars.add(this.advance());
        }
      }
    }
    if (this.atEnd()) {
      throw ParseError("Unterminated double quote", start, 0);
    }
    chars.add(this.advance());
  }

  bool _parseDollarExpansion(List<String> chars, List<Node> parts, bool inDquote) {
    dynamic result0;
    String result1 = "";
    if (this.pos + 2 < this.length && (this.source[this.pos + 1]).toString() == "(" && (this.source[this.pos + 2]).toString() == "(") {
      final _tuple23 = this._parseArithmeticExpansion();
      result0 = _tuple23.$1;
      result1 = _tuple23.$2;
      if (result0 != null) {
        parts.add(result0);
        chars.add(result1);
        return true;
      }
      final _tuple24 = this._parseCommandSubstitution();
      result0 = _tuple24.$1;
      result1 = _tuple24.$2;
      if (result0 != null) {
        parts.add(result0);
        chars.add(result1);
        return true;
      }
      return false;
    }
    if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "[") {
      final _tuple25 = this._parseDeprecatedArithmetic();
      result0 = _tuple25.$1;
      result1 = _tuple25.$2;
      if (result0 != null) {
        parts.add(result0);
        chars.add(result1);
        return true;
      }
      return false;
    }
    if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
      final _tuple26 = this._parseCommandSubstitution();
      result0 = _tuple26.$1;
      result1 = _tuple26.$2;
      if (result0 != null) {
        parts.add(result0);
        chars.add(result1);
        return true;
      }
      return false;
    }
    final _tuple27 = this._parseParamExpansion(inDquote);
    result0 = _tuple27.$1;
    result1 = _tuple27.$2;
    if (result0 != null) {
      parts.add(result0);
      chars.add(result1);
      return true;
    }
    return false;
  }

  Word _parseWordInternal(int ctx, bool atCommandStart, bool inArrayLiteral) {
    this._wordContext = ctx;
    return this.parseWord(atCommandStart, inArrayLiteral, false);
  }

  dynamic parseWord(bool atCommandStart, bool inArrayLiteral, bool inAssignBuiltin) {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null as dynamic;
    }
    this._atCommandStart = atCommandStart;
    this._inArrayLiteral = inArrayLiteral;
    this._inAssignBuiltin = inAssignBuiltin;
    dynamic tok = this._lexPeekToken();
    if (tok.type != tokentypeWord) {
      this._atCommandStart = false;
      this._inArrayLiteral = false;
      this._inAssignBuiltin = false;
      return null as dynamic;
    }
    this._lexNextToken();
    this._atCommandStart = false;
    this._inArrayLiteral = false;
    this._inAssignBuiltin = false;
    return tok.word!;
  }

  (Node?, String) _parseCommandSubstitution() {
    if (this.atEnd() || this.peek() != "\$") {
      return (null, "");
    }
    int start = this.pos; 
    this.advance();
    if (this.atEnd() || this.peek() != "(") {
      this.pos = start;
      return (null, "");
    }
    this.advance();
    dynamic saved = this._saveParserState();
    this._setState(parserstateflagsPstCmdsubst | parserstateflagsPstEoftoken);
    this._eofToken = ")";
    dynamic cmd = this.parseList(true);
    if (cmd == null) {
      cmd = Empty("empty");
    }
    this.skipWhitespaceAndNewlines();
    if (this.atEnd() || this.peek() != ")") {
      this._restoreParserState(saved);
      this.pos = start;
      return (null, "");
    }
    this.advance();
    int textEnd = this.pos; 
    String text = _substring(this.source, start, textEnd); 
    this._restoreParserState(saved);
    return (CommandSubstitution(cmd, false, "cmdsub"), text);
  }

  (Node?, String) _parseFunsub(int start) {
    this._syncParser();
    if (!(this.atEnd()) && this.peek() == "|") {
      this.advance();
    }
    dynamic saved = this._saveParserState();
    this._setState(parserstateflagsPstCmdsubst | parserstateflagsPstEoftoken);
    this._eofToken = "}";
    dynamic cmd = this.parseList(true);
    if (cmd == null) {
      cmd = Empty("empty");
    }
    this.skipWhitespaceAndNewlines();
    if (this.atEnd() || this.peek() != "}") {
      this._restoreParserState(saved);
      throw MatchedPairError("unexpected EOF looking for `}'", start, 0);
    }
    this.advance();
    String text = _substring(this.source, start, this.pos); 
    this._restoreParserState(saved);
    this._syncLexer();
    return (CommandSubstitution(cmd, true, "cmdsub"), text);
  }

  bool _isAssignmentWord(Word word) {
    return _assignment(word.value, 0) != -1;
  }

  (Node?, String) _parseBacktickSubstitution() {
    if (this.atEnd() || this.peek() != "`") {
      return (null, "");
    }
    int start = this.pos; 
    this.advance();
    List<String> contentChars = <String>[]; 
    List<String> textChars = <String>["`"]; 
    List<(String, bool)> pendingHeredocs = <(String, bool)>[]; 
    bool inHeredocBody = false; 
    String currentHeredocDelim = ""; 
    bool currentHeredocStrip = false; 
    String ch = "";
    while (!(this.atEnd()) && (inHeredocBody || this.peek() != "`")) {
      if (inHeredocBody) {
        int lineStart = this.pos; 
        int lineEnd = lineStart; 
        while (lineEnd < this.length && (this.source[lineEnd]).toString() != "\n") {
          lineEnd += 1;
        }
        String line = _substring(this.source, lineStart, lineEnd); 
        String checkLine = (currentHeredocStrip ? _trimLeft(line, "\t") : line); 
        if (checkLine == currentHeredocDelim) {
          for (final _c3 in line.split('')) {
            ch = _c3;
            contentChars.add(ch);
            textChars.add(ch);
          }
          this.pos = lineEnd;
          if (this.pos < this.length && (this.source[this.pos]).toString() == "\n") {
            contentChars.add("\n");
            textChars.add("\n");
            this.advance();
          }
          inHeredocBody = false;
          if (pendingHeredocs.length > 0) {
            final _entry28 = pendingHeredocs[0];
            pendingHeredocs.removeAt(0);
            currentHeredocDelim = _entry28.$1;
            currentHeredocStrip = _entry28.$2;
            inHeredocBody = true;
          }
        } else {
          if (checkLine.startsWith(currentHeredocDelim) && checkLine.length > currentHeredocDelim.length) {
            int tabsStripped = line.length - checkLine.length; 
            int endPos = tabsStripped + currentHeredocDelim.length; 
            for (int i = 0; i < endPos; i += 1) {
              contentChars.add((line[i]).toString());
              textChars.add((line[i]).toString());
            }
            this.pos = lineStart + endPos;
            inHeredocBody = false;
            if (pendingHeredocs.length > 0) {
              final _entry29 = pendingHeredocs[0];
              pendingHeredocs.removeAt(0);
              currentHeredocDelim = _entry29.$1;
              currentHeredocStrip = _entry29.$2;
              inHeredocBody = true;
            }
          } else {
            for (final _c4 in line.split('')) {
              ch = _c4;
              contentChars.add(ch);
              textChars.add(ch);
            }
            this.pos = lineEnd;
            if (this.pos < this.length && (this.source[this.pos]).toString() == "\n") {
              contentChars.add("\n");
              textChars.add("\n");
              this.advance();
            }
          }
        }
        continue;
      }
      String c = this.peek(); 
      if (c == "\\" && this.pos + 1 < this.length) {
        String nextC = (this.source[this.pos + 1]).toString(); 
        if (nextC == "\n") {
          this.advance();
          this.advance();
        } else {
          if (_isEscapeCharInBacktick(nextC)) {
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
      if (c == "<" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "<") {
        String quote = "";
        if (this.pos + 2 < this.length && (this.source[this.pos + 2]).toString() == "<") {
          contentChars.add(this.advance());
          textChars.add("<");
          contentChars.add(this.advance());
          textChars.add("<");
          contentChars.add(this.advance());
          textChars.add("<");
          while (!(this.atEnd()) && _isWhitespaceNoNewline(this.peek())) {
            ch = this.advance();
            contentChars.add(ch);
            textChars.add(ch);
          }
          while (!(this.atEnd()) && !(_isWhitespace(this.peek())) && !"()".contains(this.peek())) {
            if (this.peek() == "\\" && this.pos + 1 < this.length) {
              ch = this.advance();
              contentChars.add(ch);
              textChars.add(ch);
              ch = this.advance();
              contentChars.add(ch);
              textChars.add(ch);
            } else {
              if ("\"'".contains(this.peek())) {
                quote = this.peek();
                ch = this.advance();
                contentChars.add(ch);
                textChars.add(ch);
                while (!(this.atEnd()) && this.peek() != quote) {
                  if (quote == "\"" && this.peek() == "\\") {
                    ch = this.advance();
                    contentChars.add(ch);
                    textChars.add(ch);
                  }
                  ch = this.advance();
                  contentChars.add(ch);
                  textChars.add(ch);
                }
                if (!(this.atEnd())) {
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
        bool stripTabs = false; 
        if (!(this.atEnd()) && this.peek() == "-") {
          stripTabs = true;
          contentChars.add(this.advance());
          textChars.add("-");
        }
        while (!(this.atEnd()) && _isWhitespaceNoNewline(this.peek())) {
          ch = this.advance();
          contentChars.add(ch);
          textChars.add(ch);
        }
        List<String> delimiterChars = <String>[]; 
        if (!(this.atEnd())) {
          ch = this.peek();
          String dch = "";
          String closing = "";
          if (_isQuote(ch)) {
            quote = this.advance();
            contentChars.add(quote);
            textChars.add(quote);
            while (!(this.atEnd()) && this.peek() != quote) {
              dch = this.advance();
              contentChars.add(dch);
              textChars.add(dch);
              delimiterChars.add(dch);
            }
            if (!(this.atEnd())) {
              closing = this.advance();
              contentChars.add(closing);
              textChars.add(closing);
            }
          } else {
            String esc = "";
            if (ch == "\\") {
              esc = this.advance();
              contentChars.add(esc);
              textChars.add(esc);
              if (!(this.atEnd())) {
                dch = this.advance();
                contentChars.add(dch);
                textChars.add(dch);
                delimiterChars.add(dch);
              }
              while (!(this.atEnd()) && !(_isMetachar(this.peek()))) {
                dch = this.advance();
                contentChars.add(dch);
                textChars.add(dch);
                delimiterChars.add(dch);
              }
            } else {
              while (!(this.atEnd()) && !(_isMetachar(this.peek())) && this.peek() != "`") {
                ch = this.peek();
                if (_isQuote(ch)) {
                  quote = this.advance();
                  contentChars.add(quote);
                  textChars.add(quote);
                  while (!(this.atEnd()) && this.peek() != quote) {
                    dch = this.advance();
                    contentChars.add(dch);
                    textChars.add(dch);
                    delimiterChars.add(dch);
                  }
                  if (!(this.atEnd())) {
                    closing = this.advance();
                    contentChars.add(closing);
                    textChars.add(closing);
                  }
                } else {
                  if (ch == "\\") {
                    esc = this.advance();
                    contentChars.add(esc);
                    textChars.add(esc);
                    if (!(this.atEnd())) {
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
        String delimiter = delimiterChars.join(""); 
        if ((delimiter.isNotEmpty)) {
          pendingHeredocs.add((delimiter, stripTabs));
        }
        continue;
      }
      if (c == "\n") {
        ch = this.advance();
        contentChars.add(ch);
        textChars.add(ch);
        if (pendingHeredocs.length > 0) {
          final _entry30 = pendingHeredocs[0];
          pendingHeredocs.removeAt(0);
          currentHeredocDelim = _entry30.$1;
          currentHeredocStrip = _entry30.$2;
          inHeredocBody = true;
        }
        continue;
      }
      ch = this.advance();
      contentChars.add(ch);
      textChars.add(ch);
    }
    if (this.atEnd()) {
      throw ParseError("Unterminated backtick", start, 0);
    }
    this.advance();
    textChars.add("`");
    String text = textChars.join(""); 
    String content = contentChars.join(""); 
    if (pendingHeredocs.length > 0) {
      final _tuple31 = _findHeredocContentEnd(this.source, this.pos, pendingHeredocs);
      int heredocStart = _tuple31.$1;
      int heredocEnd = _tuple31.$2;
      if (heredocEnd > heredocStart) {
        content = content + _substring(this.source, heredocStart, heredocEnd);
        if (this._cmdsubHeredocEnd == -1) {
          this._cmdsubHeredocEnd = heredocEnd;
        } else {
          this._cmdsubHeredocEnd = (this._cmdsubHeredocEnd > heredocEnd ? this._cmdsubHeredocEnd : heredocEnd);
        }
      }
    }
    dynamic subParser = newParser(content, false, this._extglob);
    dynamic cmd = subParser.parseList(true);
    if (cmd == null) {
      cmd = Empty("empty");
    }
    return (CommandSubstitution(cmd, false, "cmdsub"), text);
  }

  (Node?, String) _parseProcessSubstitution() {
    if (this.atEnd() || !(_isRedirectChar(this.peek()))) {
      return (null, "");
    }
    int start = this.pos; 
    String direction = this.advance(); 
    if (this.atEnd() || this.peek() != "(") {
      this.pos = start;
      return (null, "");
    }
    this.advance();
    dynamic saved = this._saveParserState();
    bool oldInProcessSub = this._inProcessSub; 
    this._inProcessSub = true;
    this._setState(parserstateflagsPstEoftoken);
    this._eofToken = ")";
    try {
      dynamic cmd = this.parseList(true);
      if (cmd == null) {
        cmd = Empty("empty");
      }
      this.skipWhitespaceAndNewlines();
      if (this.atEnd() || this.peek() != ")") {
        throw ParseError("Invalid process substitution", start, 0);
      }
      this.advance();
      int textEnd = this.pos; 
      String text = _substring(this.source, start, textEnd); 
      text = _stripLineContinuationsCommentAware(text);
      this._restoreParserState(saved);
      this._inProcessSub = oldInProcessSub;
      return (ProcessSubstitution(direction, cmd, "procsub"), text);
    } on ParseError {
      this._restoreParserState(saved);
      this._inProcessSub = oldInProcessSub;
      String contentStartChar = (start + 2 < this.length ? (this.source[start + 2]).toString() : ""); 
      if (" \t\n".contains(contentStartChar)) {
        rethrow;
      }
      this.pos = start + 2;
      this._lexer.pos = this.pos;
      this._lexer._parseMatchedPair("(", ")", 0, false);
      this.pos = this._lexer.pos;
      String text = _substring(this.source, start, this.pos); 
      text = _stripLineContinuationsCommentAware(text);
      return (null, text);
    }
  }

  (Node?, String) _parseArrayLiteral() {
    if (this.atEnd() || this.peek() != "(") {
      return (null, "");
    }
    int start = this.pos; 
    this.advance();
    this._setState(parserstateflagsPstCompassign);
    List<Word> elements = <Word>[]; 
    while (true) {
      this.skipWhitespaceAndNewlines();
      if (this.atEnd()) {
        this._clearState(parserstateflagsPstCompassign);
        throw ParseError("Unterminated array literal", start, 0);
      }
      if (this.peek() == ")") {
        break;
      }
      dynamic word = this.parseWord(false, true, false);
      if (word == null) {
        if (this.peek() == ")") {
          break;
        }
        this._clearState(parserstateflagsPstCompassign);
        throw ParseError("Expected word in array literal", this.pos, 0);
      }
      elements.add(word);
    }
    if (this.atEnd() || this.peek() != ")") {
      this._clearState(parserstateflagsPstCompassign);
      throw ParseError("Expected ) to close array literal", this.pos, 0);
    }
    this.advance();
    String text = _substring(this.source, start, this.pos); 
    this._clearState(parserstateflagsPstCompassign);
    return (Array(elements, "array"), text);
  }

  (Node?, String) _parseArithmeticExpansion() {
    if (this.atEnd() || this.peek() != "\$") {
      return (null, "");
    }
    int start = this.pos; 
    if (this.pos + 2 >= this.length || (this.source[this.pos + 1]).toString() != "(" || (this.source[this.pos + 2]).toString() != "(") {
      return (null, "");
    }
    this.advance();
    this.advance();
    this.advance();
    int contentStart = this.pos; 
    int depth = 2; 
    int firstClosePos = -1; 
    while (!(this.atEnd()) && depth > 0) {
      String c = this.peek(); 
      if (c == "'") {
        this.advance();
        while (!(this.atEnd()) && this.peek() != "'") {
          this.advance();
        }
        if (!(this.atEnd())) {
          this.advance();
        }
      } else {
        if (c == "\"") {
          this.advance();
          while (!(this.atEnd())) {
            if (this.peek() == "\\" && this.pos + 1 < this.length) {
              this.advance();
              this.advance();
            } else {
              if (this.peek() == "\"") {
                this.advance();
                break;
              } else {
                this.advance();
              }
            }
          }
        } else {
          if (c == "\\" && this.pos + 1 < this.length) {
            this.advance();
            this.advance();
          } else {
            if (c == "(") {
              depth += 1;
              this.advance();
            } else {
              if (c == ")") {
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
        throw MatchedPairError("unexpected EOF looking for `))'", start, 0);
      }
      this.pos = start;
      return (null, "");
    }
    String content = "";
    if (firstClosePos != -1) {
      content = _substring(this.source, contentStart, firstClosePos);
    } else {
      content = _substring(this.source, contentStart, this.pos);
    }
    this.advance();
    String text = _substring(this.source, start, this.pos); 
    dynamic expr;
    try {
      expr = this._parseArithExpr(content);
    } on ParseError {
      this.pos = start;
      return (null, "");
    }
    return (ArithmeticExpansion(expr, "arith"), text);
  }

  dynamic _parseArithExpr(String content) {
    String savedArithSrc = this._arithSrc; 
    int savedArithPos = this._arithPos; 
    int savedArithLen = this._arithLen; 
    int savedParserState = this._parserState; 
    this._setState(parserstateflagsPstArith);
    this._arithSrc = content;
    this._arithPos = 0;
    this._arithLen = content.length;
    this._arithSkipWs();
    dynamic result;
    if (this._arithAtEnd()) {
      result = null as dynamic;
    } else {
      result = this._arithParseComma();
    }
    this._parserState = savedParserState;
    if (savedArithSrc != "") {
      this._arithSrc = savedArithSrc;
      this._arithPos = savedArithPos;
      this._arithLen = savedArithLen;
    }
    return result;
  }

  bool _arithAtEnd() {
    return this._arithPos >= this._arithLen;
  }

  String _arithPeek(int offset) {
    int pos = this._arithPos + offset; 
    if (pos >= this._arithLen) {
      return "";
    }
    return (this._arithSrc[pos]).toString();
  }

  String _arithAdvance() {
    if (this._arithAtEnd()) {
      return "";
    }
    String c = (this._arithSrc[this._arithPos]).toString(); 
    this._arithPos += 1;
    return c;
  }

  void _arithSkipWs() {
    while (!(this._arithAtEnd())) {
      String c = (this._arithSrc[this._arithPos]).toString(); 
      if (_isWhitespace(c)) {
        this._arithPos += 1;
      } else {
        if (c == "\\" && this._arithPos + 1 < this._arithLen && (this._arithSrc[this._arithPos + 1]).toString() == "\n") {
          this._arithPos += 2;
        } else {
          break;
        }
      }
    }
  }

  bool _arithMatch(String s) {
    return _startsWithAt(this._arithSrc, this._arithPos, s);
  }

  bool _arithConsume(String s) {
    if (this._arithMatch(s)) {
      this._arithPos += s.length;
      return true;
    }
    return false;
  }

  Node _arithParseComma() {
    dynamic left = this._arithParseAssign();
    while (true) {
      this._arithSkipWs();
      if (this._arithConsume(",")) {
        this._arithSkipWs();
        dynamic right = this._arithParseAssign();
        left = ArithComma(left, right, "comma");
      } else {
        break;
      }
    }
    return left;
  }

  Node _arithParseAssign() {
    dynamic left = this._arithParseTernary();
    this._arithSkipWs();
    List<String> assignOps = <String>["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="]; 
    for (final op in assignOps) {
      if (this._arithMatch(op)) {
        if (op == "=" && this._arithPeek(1) == "=") {
          break;
        }
        this._arithConsume(op);
        this._arithSkipWs();
        dynamic right = this._arithParseAssign();
        return ArithAssign(op, left, right, "assign");
      }
    }
    return left;
  }

  Node _arithParseTernary() {
    dynamic cond = this._arithParseLogicalOr();
    this._arithSkipWs();
    if (this._arithConsume("?")) {
      this._arithSkipWs();
      dynamic ifTrue;
      if (this._arithMatch(":")) {
        ifTrue = null as dynamic;
      } else {
        ifTrue = this._arithParseAssign();
      }
      this._arithSkipWs();
      dynamic ifFalse;
      if (this._arithConsume(":")) {
        this._arithSkipWs();
        if (this._arithAtEnd() || this._arithPeek(0) == ")") {
          ifFalse = null as dynamic;
        } else {
          ifFalse = this._arithParseTernary();
        }
      } else {
        ifFalse = null as dynamic;
      }
      return ArithTernary(cond, ifTrue, ifFalse, "ternary");
    }
    return cond;
  }

  Node _arithParseLeftAssoc(List<String> ops, Node Function() parsefn) {
    dynamic left = parsefn();
    while (true) {
      this._arithSkipWs();
      bool matched = false; 
      for (final op in ops) {
        if (this._arithMatch(op)) {
          this._arithConsume(op);
          this._arithSkipWs();
          left = ArithBinaryOp(op, left, parsefn(), "binary-op");
          matched = true;
          break;
        }
      }
      if (!(matched)) {
        break;
      }
    }
    return left;
  }

  Node _arithParseLogicalOr() {
    return this._arithParseLeftAssoc(<String>["||"], this._arithParseLogicalAnd);
  }

  Node _arithParseLogicalAnd() {
    return this._arithParseLeftAssoc(<String>["&&"], this._arithParseBitwiseOr);
  }

  Node _arithParseBitwiseOr() {
    dynamic left = this._arithParseBitwiseXor();
    while (true) {
      this._arithSkipWs();
      if (this._arithPeek(0) == "|" && this._arithPeek(1) != "|" && this._arithPeek(1) != "=") {
        this._arithAdvance();
        this._arithSkipWs();
        dynamic right = this._arithParseBitwiseXor();
        left = ArithBinaryOp("|", left, right, "binary-op");
      } else {
        break;
      }
    }
    return left;
  }

  Node _arithParseBitwiseXor() {
    dynamic left = this._arithParseBitwiseAnd();
    while (true) {
      this._arithSkipWs();
      if (this._arithPeek(0) == "^" && this._arithPeek(1) != "=") {
        this._arithAdvance();
        this._arithSkipWs();
        dynamic right = this._arithParseBitwiseAnd();
        left = ArithBinaryOp("^", left, right, "binary-op");
      } else {
        break;
      }
    }
    return left;
  }

  Node _arithParseBitwiseAnd() {
    dynamic left = this._arithParseEquality();
    while (true) {
      this._arithSkipWs();
      if (this._arithPeek(0) == "&" && this._arithPeek(1) != "&" && this._arithPeek(1) != "=") {
        this._arithAdvance();
        this._arithSkipWs();
        dynamic right = this._arithParseEquality();
        left = ArithBinaryOp("&", left, right, "binary-op");
      } else {
        break;
      }
    }
    return left;
  }

  Node _arithParseEquality() {
    return this._arithParseLeftAssoc(<String>["==", "!="], this._arithParseComparison);
  }

  Node _arithParseComparison() {
    dynamic left = this._arithParseShift();
    while (true) {
      this._arithSkipWs();
      dynamic right;
      if (this._arithMatch("<=")) {
        this._arithConsume("<=");
        this._arithSkipWs();
        right = this._arithParseShift();
        left = ArithBinaryOp("<=", left, right, "binary-op");
      } else {
        if (this._arithMatch(">=")) {
          this._arithConsume(">=");
          this._arithSkipWs();
          right = this._arithParseShift();
          left = ArithBinaryOp(">=", left, right, "binary-op");
        } else {
          if (this._arithPeek(0) == "<" && this._arithPeek(1) != "<" && this._arithPeek(1) != "=") {
            this._arithAdvance();
            this._arithSkipWs();
            right = this._arithParseShift();
            left = ArithBinaryOp("<", left, right, "binary-op");
          } else {
            if (this._arithPeek(0) == ">" && this._arithPeek(1) != ">" && this._arithPeek(1) != "=") {
              this._arithAdvance();
              this._arithSkipWs();
              right = this._arithParseShift();
              left = ArithBinaryOp(">", left, right, "binary-op");
            } else {
              break;
            }
          }
        }
      }
    }
    return left;
  }

  Node _arithParseShift() {
    dynamic left = this._arithParseAdditive();
    while (true) {
      this._arithSkipWs();
      if (this._arithMatch("<<=")) {
        break;
      }
      if (this._arithMatch(">>=")) {
        break;
      }
      dynamic right;
      if (this._arithMatch("<<")) {
        this._arithConsume("<<");
        this._arithSkipWs();
        right = this._arithParseAdditive();
        left = ArithBinaryOp("<<", left, right, "binary-op");
      } else {
        if (this._arithMatch(">>")) {
          this._arithConsume(">>");
          this._arithSkipWs();
          right = this._arithParseAdditive();
          left = ArithBinaryOp(">>", left, right, "binary-op");
        } else {
          break;
        }
      }
    }
    return left;
  }

  Node _arithParseAdditive() {
    dynamic left = this._arithParseMultiplicative();
    while (true) {
      this._arithSkipWs();
      String c = this._arithPeek(0); 
      String c2 = this._arithPeek(1); 
      dynamic right;
      if (c == "+" && c2 != "+" && c2 != "=") {
        this._arithAdvance();
        this._arithSkipWs();
        right = this._arithParseMultiplicative();
        left = ArithBinaryOp("+", left, right, "binary-op");
      } else {
        if (c == "-" && c2 != "-" && c2 != "=") {
          this._arithAdvance();
          this._arithSkipWs();
          right = this._arithParseMultiplicative();
          left = ArithBinaryOp("-", left, right, "binary-op");
        } else {
          break;
        }
      }
    }
    return left;
  }

  Node _arithParseMultiplicative() {
    dynamic left = this._arithParseExponentiation();
    while (true) {
      this._arithSkipWs();
      String c = this._arithPeek(0); 
      String c2 = this._arithPeek(1); 
      dynamic right;
      if (c == "*" && c2 != "*" && c2 != "=") {
        this._arithAdvance();
        this._arithSkipWs();
        right = this._arithParseExponentiation();
        left = ArithBinaryOp("*", left, right, "binary-op");
      } else {
        if (c == "/" && c2 != "=") {
          this._arithAdvance();
          this._arithSkipWs();
          right = this._arithParseExponentiation();
          left = ArithBinaryOp("/", left, right, "binary-op");
        } else {
          if (c == "%" && c2 != "=") {
            this._arithAdvance();
            this._arithSkipWs();
            right = this._arithParseExponentiation();
            left = ArithBinaryOp("%", left, right, "binary-op");
          } else {
            break;
          }
        }
      }
    }
    return left;
  }

  Node _arithParseExponentiation() {
    dynamic left = this._arithParseUnary();
    this._arithSkipWs();
    if (this._arithMatch("**")) {
      this._arithConsume("**");
      this._arithSkipWs();
      dynamic right = this._arithParseExponentiation();
      return ArithBinaryOp("**", left, right, "binary-op");
    }
    return left;
  }

  Node _arithParseUnary() {
    this._arithSkipWs();
    dynamic operand;
    if (this._arithMatch("++")) {
      this._arithConsume("++");
      this._arithSkipWs();
      operand = this._arithParseUnary();
      return ArithPreIncr(operand, "pre-incr");
    }
    if (this._arithMatch("--")) {
      this._arithConsume("--");
      this._arithSkipWs();
      operand = this._arithParseUnary();
      return ArithPreDecr(operand, "pre-decr");
    }
    String c = this._arithPeek(0); 
    if (c == "!") {
      this._arithAdvance();
      this._arithSkipWs();
      operand = this._arithParseUnary();
      return ArithUnaryOp("!", operand, "unary-op");
    }
    if (c == "~") {
      this._arithAdvance();
      this._arithSkipWs();
      operand = this._arithParseUnary();
      return ArithUnaryOp("~", operand, "unary-op");
    }
    if (c == "+" && this._arithPeek(1) != "+") {
      this._arithAdvance();
      this._arithSkipWs();
      operand = this._arithParseUnary();
      return ArithUnaryOp("+", operand, "unary-op");
    }
    if (c == "-" && this._arithPeek(1) != "-") {
      this._arithAdvance();
      this._arithSkipWs();
      operand = this._arithParseUnary();
      return ArithUnaryOp("-", operand, "unary-op");
    }
    return this._arithParsePostfix();
  }

  Node _arithParsePostfix() {
    dynamic left = this._arithParsePrimary();
    while (true) {
      this._arithSkipWs();
      if (this._arithMatch("++")) {
        this._arithConsume("++");
        left = ArithPostIncr(left, "post-incr");
      } else {
        if (this._arithMatch("--")) {
          this._arithConsume("--");
          left = ArithPostDecr(left, "post-decr");
        } else {
          if (this._arithPeek(0) == "[") {
            bool _breakLoop32 = false;
            switch (left) {
              case ArithVar leftArithVar:
                this._arithAdvance();
                this._arithSkipWs();
                dynamic index = this._arithParseComma();
                this._arithSkipWs();
                if (!(this._arithConsume("]"))) {
                  throw ParseError("Expected ']' in array subscript", this._arithPos, 0);
                }
                left = ArithSubscript(leftArithVar.name, index, "subscript");
                break;
              default:
                _breakLoop32 = true;
                break;
            }
            if (_breakLoop32) break;
          } else {
            break;
          }
        }
      }
    }
    return left;
  }

  Node _arithParsePrimary() {
    this._arithSkipWs();
    String c = this._arithPeek(0); 
    if (c == "(") {
      this._arithAdvance();
      this._arithSkipWs();
      dynamic expr = this._arithParseComma();
      this._arithSkipWs();
      if (!(this._arithConsume(")"))) {
        throw ParseError("Expected ')' in arithmetic expression", this._arithPos, 0);
      }
      return expr;
    }
    if (c == "#" && this._arithPeek(1) == "\$") {
      this._arithAdvance();
      return this._arithParseExpansion();
    }
    if (c == "\$") {
      return this._arithParseExpansion();
    }
    if (c == "'") {
      return this._arithParseSingleQuote();
    }
    if (c == "\"") {
      return this._arithParseDoubleQuote();
    }
    if (c == "`") {
      return this._arithParseBacktick();
    }
    if (c == "\\") {
      this._arithAdvance();
      if (this._arithAtEnd()) {
        throw ParseError("Unexpected end after backslash in arithmetic", this._arithPos, 0);
      }
      String escapedChar = this._arithAdvance(); 
      return ArithEscape(escapedChar, "escape");
    }
    if (this._arithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".contains(c)) {
      return ArithEmpty("empty");
    }
    return this._arithParseNumberOrVar();
  }

  Node _arithParseExpansion() {
    if (!(this._arithConsume("\$"))) {
      throw ParseError("Expected '\$'", this._arithPos, 0);
    }
    String c = this._arithPeek(0); 
    if (c == "(") {
      return this._arithParseCmdsub();
    }
    if (c == "{") {
      return this._arithParseBracedParam();
    }
    List<String> nameChars = <String>[]; 
    while (!(this._arithAtEnd())) {
      String ch = this._arithPeek(0); 
      if ((ch.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(ch)) || ch == "_") {
        nameChars.add(this._arithAdvance());
      } else {
        if ((_isSpecialParamOrDigit(ch) || ch == "#") && !((nameChars.isNotEmpty))) {
          nameChars.add(this._arithAdvance());
          break;
        } else {
          break;
        }
      }
    }
    if (!((nameChars.isNotEmpty))) {
      throw ParseError("Expected variable name after \$", this._arithPos, 0);
    }
    return ParamExpansion(nameChars.join(""), "", "", "param");
  }

  Node _arithParseCmdsub() {
    this._arithAdvance();
    int depth = 0;
    int contentStart = 0;
    String ch = "";
    String content = "";
    if (this._arithPeek(0) == "(") {
      this._arithAdvance();
      depth = 1;
      contentStart = this._arithPos;
      while (!(this._arithAtEnd()) && depth > 0) {
        ch = this._arithPeek(0);
        if (ch == "(") {
          depth += 1;
          this._arithAdvance();
        } else {
          if (ch == ")") {
            if (depth == 1 && this._arithPeek(1) == ")") {
              break;
            }
            depth -= 1;
            this._arithAdvance();
          } else {
            this._arithAdvance();
          }
        }
      }
      content = _substring(this._arithSrc, contentStart, this._arithPos);
      this._arithAdvance();
      this._arithAdvance();
      dynamic innerExpr = this._parseArithExpr(content);
      return ArithmeticExpansion(innerExpr, "arith");
    }
    depth = 1;
    contentStart = this._arithPos;
    while (!(this._arithAtEnd()) && depth > 0) {
      ch = this._arithPeek(0);
      if (ch == "(") {
        depth += 1;
        this._arithAdvance();
      } else {
        if (ch == ")") {
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
    content = _substring(this._arithSrc, contentStart, this._arithPos);
    this._arithAdvance();
    dynamic subParser = newParser(content, false, this._extglob);
    dynamic cmd = subParser.parseList(true);
    return CommandSubstitution(cmd, false, "cmdsub");
  }

  Node _arithParseBracedParam() {
    this._arithAdvance();
    List<String> nameChars = <String>[];
    if (this._arithPeek(0) == "!") {
      this._arithAdvance();
      nameChars = <String>[];
      while (!(this._arithAtEnd()) && this._arithPeek(0) != "}") {
        nameChars.add(this._arithAdvance());
      }
      this._arithConsume("}");
      return ParamIndirect(nameChars.join(""), "", "", "param-indirect");
    }
    if (this._arithPeek(0) == "#") {
      this._arithAdvance();
      nameChars = <String>[];
      while (!(this._arithAtEnd()) && this._arithPeek(0) != "}") {
        nameChars.add(this._arithAdvance());
      }
      this._arithConsume("}");
      return ParamLength(nameChars.join(""), "param-len");
    }
    nameChars = <String>[];
    String ch = "";
    while (!(this._arithAtEnd())) {
      ch = this._arithPeek(0);
      if (ch == "}") {
        this._arithAdvance();
        return ParamExpansion(nameChars.join(""), "", "", "param");
      }
      if (_isParamExpansionOp(ch)) {
        break;
      }
      nameChars.add(this._arithAdvance());
    }
    String name = nameChars.join(""); 
    List<String> opChars = <String>[]; 
    int depth = 1; 
    while (!(this._arithAtEnd()) && depth > 0) {
      ch = this._arithPeek(0);
      if (ch == "{") {
        depth += 1;
        opChars.add(this._arithAdvance());
      } else {
        if (ch == "}") {
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
    String opStr = opChars.join(""); 
    if (opStr.startsWith(":-")) {
      return ParamExpansion(name, ":-", _substring(opStr, 2, opStr.length), "param");
    }
    if (opStr.startsWith(":=")) {
      return ParamExpansion(name, ":=", _substring(opStr, 2, opStr.length), "param");
    }
    if (opStr.startsWith(":+")) {
      return ParamExpansion(name, ":+", _substring(opStr, 2, opStr.length), "param");
    }
    if (opStr.startsWith(":?")) {
      return ParamExpansion(name, ":?", _substring(opStr, 2, opStr.length), "param");
    }
    if (opStr.startsWith(":")) {
      return ParamExpansion(name, ":", _substring(opStr, 1, opStr.length), "param");
    }
    if (opStr.startsWith("##")) {
      return ParamExpansion(name, "##", _substring(opStr, 2, opStr.length), "param");
    }
    if (opStr.startsWith("#")) {
      return ParamExpansion(name, "#", _substring(opStr, 1, opStr.length), "param");
    }
    if (opStr.startsWith("%%")) {
      return ParamExpansion(name, "%%", _substring(opStr, 2, opStr.length), "param");
    }
    if (opStr.startsWith("%")) {
      return ParamExpansion(name, "%", _substring(opStr, 1, opStr.length), "param");
    }
    if (opStr.startsWith("//")) {
      return ParamExpansion(name, "//", _substring(opStr, 2, opStr.length), "param");
    }
    if (opStr.startsWith("/")) {
      return ParamExpansion(name, "/", _substring(opStr, 1, opStr.length), "param");
    }
    return ParamExpansion(name, "", opStr, "param");
  }

  Node _arithParseSingleQuote() {
    this._arithAdvance();
    int contentStart = this._arithPos; 
    while (!(this._arithAtEnd()) && this._arithPeek(0) != "'") {
      this._arithAdvance();
    }
    String content = _substring(this._arithSrc, contentStart, this._arithPos); 
    if (!(this._arithConsume("'"))) {
      throw ParseError("Unterminated single quote in arithmetic", this._arithPos, 0);
    }
    return ArithNumber(content, "number");
  }

  Node _arithParseDoubleQuote() {
    this._arithAdvance();
    int contentStart = this._arithPos; 
    while (!(this._arithAtEnd()) && this._arithPeek(0) != "\"") {
      String c = this._arithPeek(0); 
      if (c == "\\" && !(this._arithAtEnd())) {
        this._arithAdvance();
        this._arithAdvance();
      } else {
        this._arithAdvance();
      }
    }
    String content = _substring(this._arithSrc, contentStart, this._arithPos); 
    if (!(this._arithConsume("\""))) {
      throw ParseError("Unterminated double quote in arithmetic", this._arithPos, 0);
    }
    return ArithNumber(content, "number");
  }

  Node _arithParseBacktick() {
    this._arithAdvance();
    int contentStart = this._arithPos; 
    while (!(this._arithAtEnd()) && this._arithPeek(0) != "`") {
      String c = this._arithPeek(0); 
      if (c == "\\" && !(this._arithAtEnd())) {
        this._arithAdvance();
        this._arithAdvance();
      } else {
        this._arithAdvance();
      }
    }
    String content = _substring(this._arithSrc, contentStart, this._arithPos); 
    if (!(this._arithConsume("`"))) {
      throw ParseError("Unterminated backtick in arithmetic", this._arithPos, 0);
    }
    dynamic subParser = newParser(content, false, this._extglob);
    dynamic cmd = subParser.parseList(true);
    return CommandSubstitution(cmd, false, "cmdsub");
  }

  Node _arithParseNumberOrVar() {
    this._arithSkipWs();
    List<String> chars = <String>[]; 
    String c = this._arithPeek(0); 
    String ch = "";
    if ((c.isNotEmpty && RegExp(r'^\d+$').hasMatch(c))) {
      while (!(this._arithAtEnd())) {
        ch = this._arithPeek(0);
        if ((ch.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(ch)) || ch == "#" || ch == "_") {
          chars.add(this._arithAdvance());
        } else {
          break;
        }
      }
      String prefix = chars.join(""); 
      if (!(this._arithAtEnd()) && this._arithPeek(0) == "\$") {
        dynamic expansion = this._arithParseExpansion();
        return ArithConcat(<Node>[ArithNumber(prefix, "number"), expansion], "arith-concat");
      }
      return ArithNumber(prefix, "number");
    }
    if ((c.isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch(c)) || c == "_") {
      while (!(this._arithAtEnd())) {
        ch = this._arithPeek(0);
        if ((ch.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(ch)) || ch == "_") {
          chars.add(this._arithAdvance());
        } else {
          break;
        }
      }
      return ArithVar(chars.join(""), "var");
    }
    throw ParseError("Unexpected character '" + c + "' in arithmetic expression", this._arithPos, 0);
  }

  (Node?, String) _parseDeprecatedArithmetic() {
    if (this.atEnd() || this.peek() != "\$") {
      return (null, "");
    }
    int start = this.pos; 
    if (this.pos + 1 >= this.length || (this.source[this.pos + 1]).toString() != "[") {
      return (null, "");
    }
    this.advance();
    this.advance();
    this._lexer.pos = this.pos;
    String content = this._lexer._parseMatchedPair("[", "]", matchedpairflagsArith, false); 
    this.pos = this._lexer.pos;
    String text = _substring(this.source, start, this.pos); 
    return (ArithDeprecated(content, "arith-deprecated"), text);
  }

  (Node?, String) _parseParamExpansion(bool inDquote) {
    this._syncLexer();
    final _tuple33 = this._lexer._readParamExpansion(inDquote);
    Node? result0 = _tuple33.$1;
    String result1 = _tuple33.$2;
    this._syncParser();
    return (result0, result1);
  }

  dynamic parseRedirect() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null as dynamic;
    }
    int start = this.pos; 
    int fd = -1; 
    String varfd = ""; 
    String ch = "";
    if (this.peek() == "{") {
      int saved = this.pos; 
      this.advance();
      List<String> varnameChars = <String>[]; 
      bool inBracket = false; 
      while (!(this.atEnd()) && !(_isRedirectChar(this.peek()))) {
        ch = this.peek();
        if (ch == "}" && !(inBracket)) {
          break;
        } else {
          if (ch == "[") {
            inBracket = true;
            varnameChars.add(this.advance());
          } else {
            if (ch == "]") {
              inBracket = false;
              varnameChars.add(this.advance());
            } else {
              if ((ch.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(ch)) || ch == "_") {
                varnameChars.add(this.advance());
              } else {
                if (inBracket && !(_isMetachar(ch))) {
                  varnameChars.add(this.advance());
                } else {
                  break;
                }
              }
            }
          }
        }
      }
      String varname = varnameChars.join(""); 
      bool isValidVarfd = false; 
      if ((varname.isNotEmpty)) {
        if (((varname[0]).toString().isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch((varname[0]).toString())) || (varname[0]).toString() == "_") {
          if (varname.contains("[") || varname.contains("]")) {
            int left = varname.indexOf("["); 
            int right = varname.lastIndexOf("]"); 
            if (left != -1 && right == varname.length - 1 && right > left + 1) {
              String base = _safeSubstring(varname, 0, left); 
              if ((base.isNotEmpty) && (((base[0]).toString().isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch((base[0]).toString())) || (base[0]).toString() == "_")) {
                isValidVarfd = true;
                for (final _c5 in base.substring(1).split('')) {
                  var c = _c5;
                  if (!((c.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(c)) || c == "_")) {
                    isValidVarfd = false;
                    break;
                  }
                }
              }
            }
          } else {
            isValidVarfd = true;
            for (final _c6 in varname.substring(1).split('')) {
              var c = _c6;
              if (!((c.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(c)) || c == "_")) {
                isValidVarfd = false;
                break;
              }
            }
          }
        }
      }
      if (!(this.atEnd()) && this.peek() == "}" && isValidVarfd) {
        this.advance();
        varfd = varname;
      } else {
        this.pos = saved;
      }
    }
    List<String> fdChars = <String>[];
    if (varfd == "" && (this.peek().isNotEmpty) && (this.peek().isNotEmpty && RegExp(r'^\d+$').hasMatch(this.peek()))) {
      fdChars = <String>[];
      while (!(this.atEnd()) && (this.peek().isNotEmpty && RegExp(r'^\d+$').hasMatch(this.peek()))) {
        fdChars.add(this.advance());
      }
      fd = int.parse(fdChars.join(""), radix: 10);
    }
    ch = this.peek();
    String op = "";
    dynamic target;
    if (ch == "&" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == ">") {
      if (fd != -1 || varfd != "") {
        this.pos = start;
        return null as dynamic;
      }
      this.advance();
      this.advance();
      if (!(this.atEnd()) && this.peek() == ">") {
        this.advance();
        op = "&>>";
      } else {
        op = "&>";
      }
      this.skipWhitespace();
      target = this.parseWord(false, false, false);
      if (target == null) {
        throw ParseError("Expected target for redirect " + op, this.pos, 0);
      }
      return Redirect(op, target, 0, "redirect");
    }
    if (ch == "" || !(_isRedirectChar(ch))) {
      this.pos = start;
      return null as dynamic;
    }
    if (fd == -1 && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
      this.pos = start;
      return null as dynamic;
    }
    op = this.advance();
    bool stripTabs = false; 
    if (!(this.atEnd())) {
      String nextCh = this.peek(); 
      if (op == ">" && nextCh == ">") {
        this.advance();
        op = ">>";
      } else {
        if (op == "<" && nextCh == "<") {
          this.advance();
          if (!(this.atEnd()) && this.peek() == "<") {
            this.advance();
            op = "<<<";
          } else {
            if (!(this.atEnd()) && this.peek() == "-") {
              this.advance();
              op = "<<";
              stripTabs = true;
            } else {
              op = "<<";
            }
          }
        } else {
          if (op == "<" && nextCh == ">") {
            this.advance();
            op = "<>";
          } else {
            if (op == ">" && nextCh == "|") {
              this.advance();
              op = ">|";
            } else {
              if (fd == -1 && varfd == "" && op == ">" && nextCh == "&") {
                if (this.pos + 1 >= this.length || !(_isDigitOrDash((this.source[this.pos + 1]).toString()))) {
                  this.advance();
                  op = ">&";
                }
              } else {
                if (fd == -1 && varfd == "" && op == "<" && nextCh == "&") {
                  if (this.pos + 1 >= this.length || !(_isDigitOrDash((this.source[this.pos + 1]).toString()))) {
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
    if (op == "<<") {
      return this._parseHeredoc(fd, stripTabs);
    }
    if (varfd != "") {
      op = "{" + varfd + "}" + op;
    } else {
      if (fd != -1) {
        op = fd.toString() + op;
      }
    }
    if (!(this.atEnd()) && this.peek() == "&") {
      this.advance();
      this.skipWhitespace();
      if (!(this.atEnd()) && this.peek() == "-") {
        if (this.pos + 1 < this.length && !(_isMetachar((this.source[this.pos + 1]).toString()))) {
          this.advance();
          target = Word("&-", <Node>[], "word");
        } else {
          target = null as dynamic;
        }
      } else {
        target = null as dynamic;
      }
      if (target == null) {
        dynamic innerWord;
        if (!(this.atEnd()) && ((this.peek().isNotEmpty && RegExp(r'^\d+$').hasMatch(this.peek())) || this.peek() == "-")) {
          int wordStart = this.pos; 
          fdChars = <String>[];
          while (!(this.atEnd()) && (this.peek().isNotEmpty && RegExp(r'^\d+$').hasMatch(this.peek()))) {
            fdChars.add(this.advance());
          }
          String fdTarget = "";
          if ((fdChars.isNotEmpty)) {
            fdTarget = fdChars.join("");
          } else {
            fdTarget = "";
          }
          if (!(this.atEnd()) && this.peek() == "-") {
            fdTarget += this.advance();
          }
          if (fdTarget != "-" && !(this.atEnd()) && !(_isMetachar(this.peek()))) {
            this.pos = wordStart;
            innerWord = this.parseWord(false, false, false);
            if (innerWord != null) {
              target = Word("&" + innerWord.value, <Node>[], "word");
              target!.parts = innerWord.parts;
            } else {
              throw ParseError("Expected target for redirect " + op, this.pos, 0);
            }
          } else {
            target = Word("&" + fdTarget, <Node>[], "word");
          }
        } else {
          innerWord = this.parseWord(false, false, false);
          if (innerWord != null) {
            target = Word("&" + innerWord.value, <Node>[], "word");
            target!.parts = innerWord.parts;
          } else {
            throw ParseError("Expected target for redirect " + op, this.pos, 0);
          }
        }
      }
    } else {
      this.skipWhitespace();
      if ((op == ">&" || op == "<&") && !(this.atEnd()) && this.peek() == "-") {
        if (this.pos + 1 < this.length && !(_isMetachar((this.source[this.pos + 1]).toString()))) {
          this.advance();
          target = Word("&-", <Node>[], "word");
        } else {
          target = this.parseWord(false, false, false);
        }
      } else {
        target = this.parseWord(false, false, false);
      }
    }
    if (target == null) {
      throw ParseError("Expected target for redirect " + op, this.pos, 0);
    }
    return Redirect(op, target, 0, "redirect");
  }

  (String, bool) _parseHeredocDelimiter() {
    this.skipWhitespace();
    bool quoted = false; 
    List<String> delimiterChars = <String>[]; 
    while (true) {
      String c = "";
      int depth = 0;
      while (!(this.atEnd()) && !(_isMetachar(this.peek()))) {
        String ch = this.peek(); 
        if (ch == "\"") {
          quoted = true;
          this.advance();
          while (!(this.atEnd()) && this.peek() != "\"") {
            delimiterChars.add(this.advance());
          }
          if (!(this.atEnd())) {
            this.advance();
          }
        } else {
          if (ch == "'") {
            quoted = true;
            this.advance();
            while (!(this.atEnd()) && this.peek() != "'") {
              c = this.advance();
              if (c == "\n") {
                this._sawNewlineInSingleQuote = true;
              }
              delimiterChars.add(c);
            }
            if (!(this.atEnd())) {
              this.advance();
            }
          } else {
            if (ch == "\\") {
              this.advance();
              if (!(this.atEnd())) {
                String nextCh = this.peek(); 
                if (nextCh == "\n") {
                  this.advance();
                } else {
                  quoted = true;
                  delimiterChars.add(this.advance());
                }
              }
            } else {
              if (ch == "\$" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "'") {
                quoted = true;
                this.advance();
                this.advance();
                while (!(this.atEnd()) && this.peek() != "'") {
                  c = this.peek();
                  if (c == "\\" && this.pos + 1 < this.length) {
                    this.advance();
                    String esc = this.peek(); 
                    int escVal = _getAnsiEscape(esc); 
                    if (escVal >= 0) {
                      delimiterChars.add(String.fromCharCode(escVal));
                      this.advance();
                    } else {
                      if (esc == "'") {
                        delimiterChars.add(this.advance());
                      } else {
                        delimiterChars.add(this.advance());
                      }
                    }
                  } else {
                    delimiterChars.add(this.advance());
                  }
                }
                if (!(this.atEnd())) {
                  this.advance();
                }
              } else {
                if (_isExpansionStart(this.source, this.pos, "\$(")) {
                  delimiterChars.add(this.advance());
                  delimiterChars.add(this.advance());
                  depth = 1;
                  while (!(this.atEnd()) && depth > 0) {
                    c = this.peek();
                    if (c == "(") {
                      depth += 1;
                    } else {
                      if (c == ")") {
                        depth -= 1;
                      }
                    }
                    delimiterChars.add(this.advance());
                  }
                } else {
                  int dollarCount = 0;
                  int j = 0;
                  if (ch == "\$" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "{") {
                    dollarCount = 0;
                    j = this.pos - 1;
                    while (j >= 0 && (this.source[j]).toString() == "\$") {
                      dollarCount += 1;
                      j -= 1;
                    }
                    if (j >= 0 && (this.source[j]).toString() == "\\") {
                      dollarCount -= 1;
                    }
                    if (dollarCount % 2 == 1) {
                      delimiterChars.add(this.advance());
                    } else {
                      delimiterChars.add(this.advance());
                      delimiterChars.add(this.advance());
                      depth = 0;
                      while (!(this.atEnd())) {
                        c = this.peek();
                        if (c == "{") {
                          depth += 1;
                        } else {
                          if (c == "}") {
                            delimiterChars.add(this.advance());
                            if (depth == 0) {
                              break;
                            }
                            depth -= 1;
                            if (depth == 0 && !(this.atEnd()) && _isMetachar(this.peek())) {
                              break;
                            }
                            continue;
                          }
                        }
                        delimiterChars.add(this.advance());
                      }
                    }
                  } else {
                    if (ch == "\$" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "[") {
                      dollarCount = 0;
                      j = this.pos - 1;
                      while (j >= 0 && (this.source[j]).toString() == "\$") {
                        dollarCount += 1;
                        j -= 1;
                      }
                      if (j >= 0 && (this.source[j]).toString() == "\\") {
                        dollarCount -= 1;
                      }
                      if (dollarCount % 2 == 1) {
                        delimiterChars.add(this.advance());
                      } else {
                        delimiterChars.add(this.advance());
                        delimiterChars.add(this.advance());
                        depth = 1;
                        while (!(this.atEnd()) && depth > 0) {
                          c = this.peek();
                          if (c == "[") {
                            depth += 1;
                          } else {
                            if (c == "]") {
                              depth -= 1;
                            }
                          }
                          delimiterChars.add(this.advance());
                        }
                      }
                    } else {
                      if (ch == "`") {
                        delimiterChars.add(this.advance());
                        while (!(this.atEnd()) && this.peek() != "`") {
                          c = this.peek();
                          if (c == "'") {
                            delimiterChars.add(this.advance());
                            while (!(this.atEnd()) && this.peek() != "'" && this.peek() != "`") {
                              delimiterChars.add(this.advance());
                            }
                            if (!(this.atEnd()) && this.peek() == "'") {
                              delimiterChars.add(this.advance());
                            }
                          } else {
                            if (c == "\"") {
                              delimiterChars.add(this.advance());
                              while (!(this.atEnd()) && this.peek() != "\"" && this.peek() != "`") {
                                if (this.peek() == "\\" && this.pos + 1 < this.length) {
                                  delimiterChars.add(this.advance());
                                }
                                delimiterChars.add(this.advance());
                              }
                              if (!(this.atEnd()) && this.peek() == "\"") {
                                delimiterChars.add(this.advance());
                              }
                            } else {
                              if (c == "\\" && this.pos + 1 < this.length) {
                                delimiterChars.add(this.advance());
                                delimiterChars.add(this.advance());
                              } else {
                                delimiterChars.add(this.advance());
                              }
                            }
                          }
                        }
                        if (!(this.atEnd())) {
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
      if (!(this.atEnd()) && "<>".contains(this.peek()) && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
        delimiterChars.add(this.advance());
        delimiterChars.add(this.advance());
        depth = 1;
        while (!(this.atEnd()) && depth > 0) {
          c = this.peek();
          if (c == "(") {
            depth += 1;
          } else {
            if (c == ")") {
              depth -= 1;
            }
          }
          delimiterChars.add(this.advance());
        }
        continue;
      }
      break;
    }
    return (delimiterChars.join(""), quoted);
  }

  (String, int) _readHeredocLine(bool quoted) {
    int lineStart = this.pos; 
    int lineEnd = this.pos; 
    while (lineEnd < this.length && (this.source[lineEnd]).toString() != "\n") {
      lineEnd += 1;
    }
    String line = _substring(this.source, lineStart, lineEnd); 
    if (!(quoted)) {
      while (lineEnd < this.length) {
        int trailingBs = _countTrailingBackslashes(line); 
        if (trailingBs % 2 == 0) {
          break;
        }
        line = _substring(line, 0, line.length - 1);
        lineEnd += 1;
        int nextLineStart = lineEnd; 
        while (lineEnd < this.length && (this.source[lineEnd]).toString() != "\n") {
          lineEnd += 1;
        }
        line = line + _substring(this.source, nextLineStart, lineEnd);
      }
    }
    return (line, lineEnd);
  }

  (bool, String) _lineMatchesDelimiter(String line, String delimiter, bool stripTabs) {
    String checkLine = (stripTabs ? _trimLeft(line, "\t") : line); 
    String normalizedCheck = _normalizeHeredocDelimiter(checkLine); 
    String normalizedDelim = _normalizeHeredocDelimiter(delimiter); 
    return (normalizedCheck == normalizedDelim, checkLine);
  }

  void _gatherHeredocBodies() {
    for (final heredoc in this._pendingHeredocs) {
      List<String> contentLines = <String>[]; 
      int lineStart = this.pos; 
      while (this.pos < this.length) {
        lineStart = this.pos;
        final _tuple34 = this._readHeredocLine(heredoc.quoted);
        String line = _tuple34.$1;
        int lineEnd = _tuple34.$2;
        final _tuple35 = this._lineMatchesDelimiter(line, heredoc.delimiter, heredoc.stripTabs);
        bool matches = _tuple35.$1;
        String checkLine = _tuple35.$2;
        if (matches) {
          this.pos = (lineEnd < this.length ? lineEnd + 1 : lineEnd);
          break;
        }
        String normalizedCheck = _normalizeHeredocDelimiter(checkLine); 
        String normalizedDelim = _normalizeHeredocDelimiter(heredoc.delimiter); 
        int tabsStripped = 0;
        if (this._eofToken == ")" && normalizedCheck.startsWith(normalizedDelim)) {
          tabsStripped = line.length - checkLine.length;
          this.pos = lineStart + tabsStripped + heredoc.delimiter.length;
          break;
        }
        if (lineEnd >= this.length && normalizedCheck.startsWith(normalizedDelim) && this._inProcessSub) {
          tabsStripped = line.length - checkLine.length;
          this.pos = lineStart + tabsStripped + heredoc.delimiter.length;
          break;
        }
        if (heredoc.stripTabs) {
          line = _trimLeft(line, "\t");
        }
        if (lineEnd < this.length) {
          contentLines.add(line + "\n");
          this.pos = lineEnd + 1;
        } else {
          bool addNewline = true; 
          if (!(heredoc.quoted) && _countTrailingBackslashes(line) % 2 == 1) {
            addNewline = false;
          }
          contentLines.add(line + (addNewline ? "\n" : ""));
          this.pos = this.length;
        }
      }
      heredoc.content = contentLines.join("");
    }
    this._pendingHeredocs = <HereDoc>[];
  }

  HereDoc _parseHeredoc(int fd, bool stripTabs) {
    int startPos = this.pos; 
    this._setState(parserstateflagsPstHeredoc);
    final _tuple36 = this._parseHeredocDelimiter();
    String delimiter = _tuple36.$1;
    bool quoted = _tuple36.$2;
    for (final existing in this._pendingHeredocs) {
      if (existing._startPos == startPos && existing.delimiter == delimiter) {
        this._clearState(parserstateflagsPstHeredoc);
        return existing;
      }
    }
    HereDoc heredoc = HereDoc(delimiter, "", stripTabs, quoted, fd, false, 0, "heredoc"); 
    heredoc._startPos = startPos;
    this._pendingHeredocs.add(heredoc);
    this._clearState(parserstateflagsPstHeredoc);
    return heredoc;
  }

  dynamic parseCommand() {
    List<Word> words = <Word>[]; 
    List<Node> redirects = <Node>[]; 
    while (true) {
      this.skipWhitespace();
      if (this._lexIsCommandTerminator()) {
        break;
      }
      if (words.length == 0) {
        String reserved = this._lexPeekReservedWord(); 
        if (reserved == "}" || reserved == "]]") {
          break;
        }
      }
      dynamic redirect = this.parseRedirect();
      if (redirect != null) {
        redirects.add(redirect);
        continue;
      }
      bool allAssignments = true; 
      for (final w in words) {
        if (!(this._isAssignmentWord(w))) {
          allAssignments = false;
          break;
        }
      }
      bool inAssignBuiltin = words.length > 0 && assignmentBuiltins.contains(words[0].value); 
      dynamic word = this.parseWord(!((words.isNotEmpty)) || allAssignments && redirects.length == 0, false, inAssignBuiltin);
      if (word == null) {
        break;
      }
      words.add(word);
    }
    if (!((words.isNotEmpty)) && !((redirects.isNotEmpty))) {
      return null as dynamic;
    }
    return Command(words, redirects, "command");
  }

  dynamic parseSubshell() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() != "(") {
      return null as dynamic;
    }
    this.advance();
    this._setState(parserstateflagsPstSubshell);
    dynamic body = this.parseList(true);
    if (body == null) {
      this._clearState(parserstateflagsPstSubshell);
      throw ParseError("Expected command in subshell", this.pos, 0);
    }
    this.skipWhitespace();
    if (this.atEnd() || this.peek() != ")") {
      this._clearState(parserstateflagsPstSubshell);
      throw ParseError("Expected ) to close subshell", this.pos, 0);
    }
    this.advance();
    this._clearState(parserstateflagsPstSubshell);
    return Subshell(body, this._collectRedirects(), "subshell");
  }

  dynamic parseArithmeticCommand() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() != "(" || this.pos + 1 >= this.length || (this.source[this.pos + 1]).toString() != "(") {
      return null as dynamic;
    }
    int savedPos = this.pos; 
    this.advance();
    this.advance();
    int contentStart = this.pos; 
    int depth = 1; 
    while (!(this.atEnd()) && depth > 0) {
      String c = this.peek(); 
      if (c == "'") {
        this.advance();
        while (!(this.atEnd()) && this.peek() != "'") {
          this.advance();
        }
        if (!(this.atEnd())) {
          this.advance();
        }
      } else {
        if (c == "\"") {
          this.advance();
          while (!(this.atEnd())) {
            if (this.peek() == "\\" && this.pos + 1 < this.length) {
              this.advance();
              this.advance();
            } else {
              if (this.peek() == "\"") {
                this.advance();
                break;
              } else {
                this.advance();
              }
            }
          }
        } else {
          if (c == "\\" && this.pos + 1 < this.length) {
            this.advance();
            this.advance();
          } else {
            if (c == "(") {
              depth += 1;
              this.advance();
            } else {
              if (c == ")") {
                if (depth == 1 && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == ")") {
                  break;
                }
                depth -= 1;
                if (depth == 0) {
                  this.pos = savedPos;
                  return null as dynamic;
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
      throw MatchedPairError("unexpected EOF looking for `))'", savedPos, 0);
    }
    if (depth != 1) {
      this.pos = savedPos;
      return null as dynamic;
    }
    String content = _substring(this.source, contentStart, this.pos); 
    content = content.replaceAll("\\\n", "");
    this.advance();
    this.advance();
    dynamic expr = this._parseArithExpr(content);
    return ArithmeticCommand(expr, this._collectRedirects(), content, "arith-cmd");
  }

  dynamic parseConditionalExpr() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() != "[" || this.pos + 1 >= this.length || (this.source[this.pos + 1]).toString() != "[") {
      return null as dynamic;
    }
    int nextPos = this.pos + 2; 
    if (nextPos < this.length && !(_isWhitespace((this.source[nextPos]).toString()) || (this.source[nextPos]).toString() == "\\" && nextPos + 1 < this.length && (this.source[nextPos + 1]).toString() == "\n")) {
      return null as dynamic;
    }
    this.advance();
    this.advance();
    this._setState(parserstateflagsPstCondexpr);
    this._wordContext = wordCtxCond;
    dynamic body = this._parseCondOr();
    while (!(this.atEnd()) && _isWhitespaceNoNewline(this.peek())) {
      this.advance();
    }
    if (this.atEnd() || this.peek() != "]" || this.pos + 1 >= this.length || (this.source[this.pos + 1]).toString() != "]") {
      this._clearState(parserstateflagsPstCondexpr);
      this._wordContext = wordCtxNormal;
      throw ParseError("Expected ]] to close conditional expression", this.pos, 0);
    }
    this.advance();
    this.advance();
    this._clearState(parserstateflagsPstCondexpr);
    this._wordContext = wordCtxNormal;
    return ConditionalExpr(body, this._collectRedirects(), "cond-expr");
  }

  void _condSkipWhitespace() {
    while (!(this.atEnd())) {
      if (_isWhitespaceNoNewline(this.peek())) {
        this.advance();
      } else {
        if (this.peek() == "\\" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "\n") {
          this.advance();
          this.advance();
        } else {
          if (this.peek() == "\n") {
            this.advance();
          } else {
            break;
          }
        }
      }
    }
  }

  bool _condAtEnd() {
    return this.atEnd() || this.peek() == "]" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "]";
  }

  Node _parseCondOr() {
    this._condSkipWhitespace();
    dynamic left = this._parseCondAnd();
    this._condSkipWhitespace();
    if (!(this._condAtEnd()) && this.peek() == "|" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "|") {
      this.advance();
      this.advance();
      dynamic right = this._parseCondOr();
      return CondOr(left, right, "cond-or");
    }
    return left;
  }

  Node _parseCondAnd() {
    this._condSkipWhitespace();
    dynamic left = this._parseCondTerm();
    this._condSkipWhitespace();
    if (!(this._condAtEnd()) && this.peek() == "&" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "&") {
      this.advance();
      this.advance();
      dynamic right = this._parseCondAnd();
      return CondAnd(left, right, "cond-and");
    }
    return left;
  }

  Node _parseCondTerm() {
    this._condSkipWhitespace();
    if (this._condAtEnd()) {
      throw ParseError("Unexpected end of conditional expression", this.pos, 0);
    }
    if (this.peek() == "!") {
      if (this.pos + 1 < this.length && !(_isWhitespaceNoNewline((this.source[this.pos + 1]).toString()))) {
      } else {
        this.advance();
        dynamic operand = this._parseCondTerm();
        return CondNot(operand, "cond-not");
      }
    }
    if (this.peek() == "(") {
      this.advance();
      dynamic inner = this._parseCondOr();
      this._condSkipWhitespace();
      if (this.atEnd() || this.peek() != ")") {
        throw ParseError("Expected ) in conditional expression", this.pos, 0);
      }
      this.advance();
      return CondParen(inner, "cond-paren");
    }
    dynamic word1 = this._parseCondWord();
    if (word1 == null) {
      throw ParseError("Expected word in conditional expression", this.pos, 0);
    }
    this._condSkipWhitespace();
    if (condUnaryOps.contains(word1.value)) {
      dynamic unaryOperand = this._parseCondWord();
      if (unaryOperand == null) {
        throw ParseError("Expected operand after " + word1.value, this.pos, 0);
      }
      return UnaryTest(word1.value, unaryOperand, "unary-test");
    }
    if (!(this._condAtEnd()) && this.peek() != "&" && this.peek() != "|" && this.peek() != ")") {
      dynamic word2;
      if (_isRedirectChar(this.peek()) && !(this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(")) {
        String op = this.advance(); 
        this._condSkipWhitespace();
        word2 = this._parseCondWord();
        if (word2 == null) {
          throw ParseError("Expected operand after " + op, this.pos, 0);
        }
        return BinaryTest(op, word1, word2, "binary-test");
      }
      int savedPos = this.pos; 
      dynamic opWord = this._parseCondWord();
      if (opWord != null && condBinaryOps.contains(opWord.value)) {
        this._condSkipWhitespace();
        if (opWord.value == "=~") {
          word2 = this._parseCondRegexWord();
        } else {
          word2 = this._parseCondWord();
        }
        if (word2 == null) {
          throw ParseError("Expected operand after " + opWord.value, this.pos, 0);
        }
        return BinaryTest(opWord.value, word1, word2, "binary-test");
      } else {
        this.pos = savedPos;
      }
    }
    return UnaryTest("-n", word1, "unary-test");
  }

  dynamic _parseCondWord() {
    this._condSkipWhitespace();
    if (this._condAtEnd()) {
      return null as dynamic;
    }
    String c = this.peek(); 
    if (_isParen(c)) {
      return null as dynamic;
    }
    if (c == "&" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "&") {
      return null as dynamic;
    }
    if (c == "|" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "|") {
      return null as dynamic;
    }
    return this._parseWordInternal(wordCtxCond, false, false);
  }

  dynamic _parseCondRegexWord() {
    this._condSkipWhitespace();
    if (this._condAtEnd()) {
      return null as dynamic;
    }
    this._setState(parserstateflagsPstRegexp);
    dynamic result = this._parseWordInternal(wordCtxRegex, false, false);
    this._clearState(parserstateflagsPstRegexp);
    this._wordContext = wordCtxCond;
    return result;
  }

  dynamic parseBraceGroup() {
    this.skipWhitespace();
    if (!(this._lexConsumeWord("{"))) {
      return null as dynamic;
    }
    this.skipWhitespaceAndNewlines();
    dynamic body = this.parseList(true);
    if (body == null) {
      throw ParseError("Expected command in brace group", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespace();
    if (!(this._lexConsumeWord("}"))) {
      throw ParseError("Expected } to close brace group", this._lexPeekToken().pos, 0);
    }
    return BraceGroup(body, this._collectRedirects(), "brace-group");
  }

  dynamic parseIf() {
    this.skipWhitespace();
    if (!(this._lexConsumeWord("if"))) {
      return null as dynamic;
    }
    dynamic condition = this.parseListUntil(<String>{"then"});
    if (condition == null) {
      throw ParseError("Expected condition after 'if'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("then"))) {
      throw ParseError("Expected 'then' after if condition", this._lexPeekToken().pos, 0);
    }
    dynamic thenBody = this.parseListUntil(<String>{"elif", "else", "fi"});
    if (thenBody == null) {
      throw ParseError("Expected commands after 'then'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    Node? elseBody = null;
    if (this._lexIsAtReservedWord("elif")) {
      this._lexConsumeWord("elif");
      dynamic elifCondition = this.parseListUntil(<String>{"then"});
      if (elifCondition == null) {
        throw ParseError("Expected condition after 'elif'", this._lexPeekToken().pos, 0);
      }
      this.skipWhitespaceAndNewlines();
      if (!(this._lexConsumeWord("then"))) {
        throw ParseError("Expected 'then' after elif condition", this._lexPeekToken().pos, 0);
      }
      dynamic elifThenBody = this.parseListUntil(<String>{"elif", "else", "fi"});
      if (elifThenBody == null) {
        throw ParseError("Expected commands after 'then'", this._lexPeekToken().pos, 0);
      }
      this.skipWhitespaceAndNewlines();
      Node? innerElse = null;
      if (this._lexIsAtReservedWord("elif")) {
        innerElse = this._parseElifChain();
      } else {
        if (this._lexIsAtReservedWord("else")) {
          this._lexConsumeWord("else");
          innerElse = this.parseListUntil(<String>{"fi"});
          if (innerElse == null) {
            throw ParseError("Expected commands after 'else'", this._lexPeekToken().pos, 0);
          }
        }
      }
      elseBody = If(elifCondition, elifThenBody, innerElse, <Node>[], "if");
    } else {
      if (this._lexIsAtReservedWord("else")) {
        this._lexConsumeWord("else");
        elseBody = this.parseListUntil(<String>{"fi"});
        if (elseBody == null) {
          throw ParseError("Expected commands after 'else'", this._lexPeekToken().pos, 0);
        }
      }
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("fi"))) {
      throw ParseError("Expected 'fi' to close if statement", this._lexPeekToken().pos, 0);
    }
    return If(condition, thenBody, elseBody, this._collectRedirects(), "if");
  }

  If _parseElifChain() {
    this._lexConsumeWord("elif");
    dynamic condition = this.parseListUntil(<String>{"then"});
    if (condition == null) {
      throw ParseError("Expected condition after 'elif'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("then"))) {
      throw ParseError("Expected 'then' after elif condition", this._lexPeekToken().pos, 0);
    }
    dynamic thenBody = this.parseListUntil(<String>{"elif", "else", "fi"});
    if (thenBody == null) {
      throw ParseError("Expected commands after 'then'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    Node? elseBody = null;
    if (this._lexIsAtReservedWord("elif")) {
      elseBody = this._parseElifChain();
    } else {
      if (this._lexIsAtReservedWord("else")) {
        this._lexConsumeWord("else");
        elseBody = this.parseListUntil(<String>{"fi"});
        if (elseBody == null) {
          throw ParseError("Expected commands after 'else'", this._lexPeekToken().pos, 0);
        }
      }
    }
    return If(condition, thenBody, elseBody, <Node>[], "if");
  }

  dynamic parseWhile() {
    this.skipWhitespace();
    if (!(this._lexConsumeWord("while"))) {
      return null as dynamic;
    }
    dynamic condition = this.parseListUntil(<String>{"do"});
    if (condition == null) {
      throw ParseError("Expected condition after 'while'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("do"))) {
      throw ParseError("Expected 'do' after while condition", this._lexPeekToken().pos, 0);
    }
    dynamic body = this.parseListUntil(<String>{"done"});
    if (body == null) {
      throw ParseError("Expected commands after 'do'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("done"))) {
      throw ParseError("Expected 'done' to close while loop", this._lexPeekToken().pos, 0);
    }
    return While(condition, body, this._collectRedirects(), "while");
  }

  dynamic parseUntil() {
    this.skipWhitespace();
    if (!(this._lexConsumeWord("until"))) {
      return null as dynamic;
    }
    dynamic condition = this.parseListUntil(<String>{"do"});
    if (condition == null) {
      throw ParseError("Expected condition after 'until'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("do"))) {
      throw ParseError("Expected 'do' after until condition", this._lexPeekToken().pos, 0);
    }
    dynamic body = this.parseListUntil(<String>{"done"});
    if (body == null) {
      throw ParseError("Expected commands after 'do'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("done"))) {
      throw ParseError("Expected 'done' to close until loop", this._lexPeekToken().pos, 0);
    }
    return Until(condition, body, this._collectRedirects(), "until");
  }

  dynamic parseFor() {
    this.skipWhitespace();
    if (!(this._lexConsumeWord("for"))) {
      return null as dynamic;
    }
    this.skipWhitespace();
    if (this.peek() == "(" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
      return this._parseForArith();
    }
    String varName = "";
    if (this.peek() == "\$") {
      dynamic varWord = this.parseWord(false, false, false);
      if (varWord == null) {
        throw ParseError("Expected variable name after 'for'", this._lexPeekToken().pos, 0);
      }
      varName = varWord.value;
    } else {
      varName = this.peekWord();
      if (varName == "") {
        throw ParseError("Expected variable name after 'for'", this._lexPeekToken().pos, 0);
      }
      this.consumeWord(varName);
    }
    this.skipWhitespace();
    if (this.peek() == ";") {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    List<Word>? words = null;
    if (this._lexIsAtReservedWord("in")) {
      this._lexConsumeWord("in");
      this.skipWhitespace();
      bool sawDelimiter = _isSemicolonOrNewline(this.peek()); 
      if (this.peek() == ";") {
        this.advance();
      }
      this.skipWhitespaceAndNewlines();
      words = <Word>[];
      while (true) {
        this.skipWhitespace();
        if (this.atEnd()) {
          break;
        }
        if (_isSemicolonOrNewline(this.peek())) {
          sawDelimiter = true;
          if (this.peek() == ";") {
            this.advance();
          }
          break;
        }
        if (this._lexIsAtReservedWord("do")) {
          if (sawDelimiter) {
            break;
          }
          throw ParseError("Expected ';' or newline before 'do'", this._lexPeekToken().pos, 0);
        }
        dynamic word = this.parseWord(false, false, false);
        if (word == null) {
          break;
        }
        words.add(word);
      }
    }
    this.skipWhitespaceAndNewlines();
    if (this.peek() == "{") {
      dynamic braceGroup = this.parseBraceGroup();
      if (braceGroup == null) {
        throw ParseError("Expected brace group in for loop", this._lexPeekToken().pos, 0);
      }
      return For(varName, words, braceGroup.body, this._collectRedirects(), "for");
    }
    if (!(this._lexConsumeWord("do"))) {
      throw ParseError("Expected 'do' in for loop", this._lexPeekToken().pos, 0);
    }
    dynamic body = this.parseListUntil(<String>{"done"});
    if (body == null) {
      throw ParseError("Expected commands after 'do'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("done"))) {
      throw ParseError("Expected 'done' to close for loop", this._lexPeekToken().pos, 0);
    }
    return For(varName, words, body, this._collectRedirects(), "for");
  }

  ForArith _parseForArith() {
    this.advance();
    this.advance();
    List<String> parts = <String>[]; 
    List<String> current = <String>[]; 
    int parenDepth = 0; 
    while (!(this.atEnd())) {
      String ch = this.peek(); 
      if (ch == "(") {
        parenDepth += 1;
        current.add(this.advance());
      } else {
        if (ch == ")") {
          if (parenDepth > 0) {
            parenDepth -= 1;
            current.add(this.advance());
          } else {
            if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == ")") {
              parts.add(_trimLeft(current.join(""), " \t"));
              this.advance();
              this.advance();
              break;
            } else {
              current.add(this.advance());
            }
          }
        } else {
          if (ch == ";" && parenDepth == 0) {
            parts.add(_trimLeft(current.join(""), " \t"));
            current = <String>[];
            this.advance();
          } else {
            current.add(this.advance());
          }
        }
      }
    }
    if (parts.length != 3) {
      throw ParseError("Expected three expressions in for ((;;))", this.pos, 0);
    }
    String init = parts[0]; 
    String cond = parts[1]; 
    String incr = parts[2]; 
    this.skipWhitespace();
    if (!(this.atEnd()) && this.peek() == ";") {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    dynamic body = this._parseLoopBody("for loop");
    return ForArith(init, cond, incr, body, this._collectRedirects(), "for-arith");
  }

  dynamic parseSelect() {
    this.skipWhitespace();
    if (!(this._lexConsumeWord("select"))) {
      return null as dynamic;
    }
    this.skipWhitespace();
    String varName = this.peekWord(); 
    if (varName == "") {
      throw ParseError("Expected variable name after 'select'", this._lexPeekToken().pos, 0);
    }
    this.consumeWord(varName);
    this.skipWhitespace();
    if (this.peek() == ";") {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    List<Word>? words = null;
    if (this._lexIsAtReservedWord("in")) {
      this._lexConsumeWord("in");
      this.skipWhitespaceAndNewlines();
      words = <Word>[];
      while (true) {
        this.skipWhitespace();
        if (this.atEnd()) {
          break;
        }
        if (_isSemicolonNewlineBrace(this.peek())) {
          if (this.peek() == ";") {
            this.advance();
          }
          break;
        }
        if (this._lexIsAtReservedWord("do")) {
          break;
        }
        dynamic word = this.parseWord(false, false, false);
        if (word == null) {
          break;
        }
        words.add(word);
      }
    }
    this.skipWhitespaceAndNewlines();
    dynamic body = this._parseLoopBody("select");
    return Select(varName, words, body, this._collectRedirects(), "select");
  }

  String _consumeCaseTerminator() {
    String term = this._lexPeekCaseTerminator(); 
    if (term != "") {
      this._lexNextToken();
      return term;
    }
    return ";;";
  }

  dynamic parseCase() {
    if (!(this.consumeWord("case"))) {
      return null as dynamic;
    }
    this._setState(parserstateflagsPstCasestmt);
    this.skipWhitespace();
    dynamic word = this.parseWord(false, false, false);
    if (word == null) {
      throw ParseError("Expected word after 'case'", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("in"))) {
      throw ParseError("Expected 'in' after case word", this._lexPeekToken().pos, 0);
    }
    this.skipWhitespaceAndNewlines();
    List<CasePattern> patterns = <CasePattern>[]; 
    this._setState(parserstateflagsPstCasepat);
    while (true) {
      this.skipWhitespaceAndNewlines();
      if (this._lexIsAtReservedWord("esac")) {
        int saved = this.pos; 
        this.skipWhitespace();
        while (!(this.atEnd()) && !(_isMetachar(this.peek())) && !(_isQuote(this.peek()))) {
          this.advance();
        }
        this.skipWhitespace();
        bool isPattern = false; 
        if (!(this.atEnd()) && this.peek() == ")") {
          if (this._eofToken == ")") {
            isPattern = false;
          } else {
            this.advance();
            this.skipWhitespace();
            if (!(this.atEnd())) {
              String nextCh = this.peek(); 
              if (nextCh == ";") {
                isPattern = true;
              } else {
                if (!(_isNewlineOrRightParen(nextCh))) {
                  isPattern = true;
                }
              }
            }
          }
        }
        this.pos = saved;
        if (!(isPattern)) {
          break;
        }
      }
      this.skipWhitespaceAndNewlines();
      if (!(this.atEnd()) && this.peek() == "(") {
        this.advance();
        this.skipWhitespaceAndNewlines();
      }
      List<String> patternChars = <String>[]; 
      int extglobDepth = 0; 
      while (!(this.atEnd())) {
        String ch = this.peek(); 
        if (ch == ")") {
          if (extglobDepth > 0) {
            patternChars.add(this.advance());
            extglobDepth -= 1;
          } else {
            this.advance();
            break;
          }
        } else {
          if (ch == "\\") {
            if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "\n") {
              this.advance();
              this.advance();
            } else {
              patternChars.add(this.advance());
              if (!(this.atEnd())) {
                patternChars.add(this.advance());
              }
            }
          } else {
            if (_isExpansionStart(this.source, this.pos, "\$(")) {
              patternChars.add(this.advance());
              patternChars.add(this.advance());
              if (!(this.atEnd()) && this.peek() == "(") {
                patternChars.add(this.advance());
                int parenDepth = 2; 
                while (!(this.atEnd()) && parenDepth > 0) {
                  String c = this.peek(); 
                  if (c == "(") {
                    parenDepth += 1;
                  } else {
                    if (c == ")") {
                      parenDepth -= 1;
                    }
                  }
                  patternChars.add(this.advance());
                }
              } else {
                extglobDepth += 1;
              }
            } else {
              if (ch == "(" && extglobDepth > 0) {
                patternChars.add(this.advance());
                extglobDepth += 1;
              } else {
                if (this._extglob && _isExtglobPrefix(ch) && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
                  patternChars.add(this.advance());
                  patternChars.add(this.advance());
                  extglobDepth += 1;
                } else {
                  if (ch == "[") {
                    bool isCharClass = false; 
                    int scanPos = this.pos + 1; 
                    int scanDepth = 0; 
                    bool hasFirstBracketLiteral = false; 
                    if (scanPos < this.length && _isCaretOrBang((this.source[scanPos]).toString())) {
                      scanPos += 1;
                    }
                    if (scanPos < this.length && (this.source[scanPos]).toString() == "]") {
                      if (this.source.indexOf("]", scanPos + 1) != -1) {
                        scanPos += 1;
                        hasFirstBracketLiteral = true;
                      }
                    }
                    while (scanPos < this.length) {
                      String sc = (this.source[scanPos]).toString(); 
                      if (sc == "]" && scanDepth == 0) {
                        isCharClass = true;
                        break;
                      } else {
                        if (sc == "[") {
                          scanDepth += 1;
                        } else {
                          if (sc == ")" && scanDepth == 0) {
                            break;
                          } else {
                            if (sc == "|" && scanDepth == 0) {
                              break;
                            }
                          }
                        }
                      }
                      scanPos += 1;
                    }
                    if (isCharClass) {
                      patternChars.add(this.advance());
                      if (!(this.atEnd()) && _isCaretOrBang(this.peek())) {
                        patternChars.add(this.advance());
                      }
                      if (hasFirstBracketLiteral && !(this.atEnd()) && this.peek() == "]") {
                        patternChars.add(this.advance());
                      }
                      while (!(this.atEnd()) && this.peek() != "]") {
                        patternChars.add(this.advance());
                      }
                      if (!(this.atEnd())) {
                        patternChars.add(this.advance());
                      }
                    } else {
                      patternChars.add(this.advance());
                    }
                  } else {
                    if (ch == "'") {
                      patternChars.add(this.advance());
                      while (!(this.atEnd()) && this.peek() != "'") {
                        patternChars.add(this.advance());
                      }
                      if (!(this.atEnd())) {
                        patternChars.add(this.advance());
                      }
                    } else {
                      if (ch == "\"") {
                        patternChars.add(this.advance());
                        while (!(this.atEnd()) && this.peek() != "\"") {
                          if (this.peek() == "\\" && this.pos + 1 < this.length) {
                            patternChars.add(this.advance());
                          }
                          patternChars.add(this.advance());
                        }
                        if (!(this.atEnd())) {
                          patternChars.add(this.advance());
                        }
                      } else {
                        if (_isWhitespace(ch)) {
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
      String pattern = patternChars.join(""); 
      if (!((pattern.isNotEmpty))) {
        throw ParseError("Expected pattern in case statement", this._lexPeekToken().pos, 0);
      }
      this.skipWhitespace();
      Node? body = null;
      bool isEmptyBody = this._lexPeekCaseTerminator() != ""; 
      if (!(isEmptyBody)) {
        this.skipWhitespaceAndNewlines();
        if (!(this.atEnd()) && !(this._lexIsAtReservedWord("esac"))) {
          bool isAtTerminator = this._lexPeekCaseTerminator() != ""; 
          if (!(isAtTerminator)) {
            body = this.parseListUntil(<String>{"esac"});
            this.skipWhitespace();
          }
        }
      }
      String terminator = this._consumeCaseTerminator(); 
      this.skipWhitespaceAndNewlines();
      patterns.add(CasePattern(pattern, body, terminator, "pattern"));
    }
    this._clearState(parserstateflagsPstCasepat);
    this.skipWhitespaceAndNewlines();
    if (!(this._lexConsumeWord("esac"))) {
      this._clearState(parserstateflagsPstCasestmt);
      throw ParseError("Expected 'esac' to close case statement", this._lexPeekToken().pos, 0);
    }
    this._clearState(parserstateflagsPstCasestmt);
    return Case(word, patterns, this._collectRedirects(), "case");
  }

  dynamic parseCoproc() {
    this.skipWhitespace();
    if (!(this._lexConsumeWord("coproc"))) {
      return null as dynamic;
    }
    this.skipWhitespace();
    String name = ""; 
    String ch = ""; 
    if (!(this.atEnd())) {
      ch = this.peek();
    }
    dynamic body;
    if (ch == "{") {
      body = this.parseBraceGroup();
      if (body != null) {
        return Coproc(body, name, "coproc");
      }
    }
    if (ch == "(") {
      if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
        body = this.parseArithmeticCommand();
        if (body != null) {
          return Coproc(body, name, "coproc");
        }
      }
      body = this.parseSubshell();
      if (body != null) {
        return Coproc(body, name, "coproc");
      }
    }
    String nextWord = this._lexPeekReservedWord(); 
    if (nextWord != "" && compoundKeywords.contains(nextWord)) {
      body = this.parseCompoundCommand();
      if (body != null) {
        return Coproc(body, name, "coproc");
      }
    }
    int wordStart = this.pos; 
    String potentialName = this.peekWord(); 
    if ((potentialName.isNotEmpty)) {
      while (!(this.atEnd()) && !(_isMetachar(this.peek())) && !(_isQuote(this.peek()))) {
        this.advance();
      }
      this.skipWhitespace();
      ch = "";
      if (!(this.atEnd())) {
        ch = this.peek();
      }
      nextWord = this._lexPeekReservedWord();
      if (_isValidIdentifier(potentialName)) {
        if (ch == "{") {
          name = potentialName;
          body = this.parseBraceGroup();
          if (body != null) {
            return Coproc(body, name, "coproc");
          }
        } else {
          if (ch == "(") {
            name = potentialName;
            if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
              body = this.parseArithmeticCommand();
            } else {
              body = this.parseSubshell();
            }
            if (body != null) {
              return Coproc(body, name, "coproc");
            }
          } else {
            if (nextWord != "" && compoundKeywords.contains(nextWord)) {
              name = potentialName;
              body = this.parseCompoundCommand();
              if (body != null) {
                return Coproc(body, name, "coproc");
              }
            }
          }
        }
      }
      this.pos = wordStart;
    }
    body = this.parseCommand();
    if (body != null) {
      return Coproc(body, name, "coproc");
    }
    throw ParseError("Expected command after coproc", this.pos, 0);
  }

  dynamic parseFunction() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null as dynamic;
    }
    int savedPos = this.pos; 
    String name = "";
    dynamic body;
    if (this._lexIsAtReservedWord("function")) {
      this._lexConsumeWord("function");
      this.skipWhitespace();
      name = this.peekWord();
      if (name == "") {
        this.pos = savedPos;
        return null as dynamic;
      }
      this.consumeWord(name);
      this.skipWhitespace();
      if (!(this.atEnd()) && this.peek() == "(") {
        if (this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == ")") {
          this.advance();
          this.advance();
        }
      }
      this.skipWhitespaceAndNewlines();
      body = this._parseCompoundCommand();
      if (body == null) {
        throw ParseError("Expected function body", this.pos, 0);
      }
      return Function_(name, body, "function");
    }
    name = this.peekWord();
    if (name == "" || reservedWords.contains(name)) {
      return null as dynamic;
    }
    if (_looksLikeAssignment(name)) {
      return null as dynamic;
    }
    this.skipWhitespace();
    int nameStart = this.pos; 
    while (!(this.atEnd()) && !(_isMetachar(this.peek())) && !(_isQuote(this.peek())) && !(_isParen(this.peek()))) {
      this.advance();
    }
    name = _substring(this.source, nameStart, this.pos);
    if (!((name.isNotEmpty))) {
      this.pos = savedPos;
      return null as dynamic;
    }
    int braceDepth = 0; 
    int i = 0; 
    while (i < name.length) {
      if (_isExpansionStart(name, i, "\${")) {
        braceDepth += 1;
        i += 2;
        continue;
      }
      if ((name[i]).toString() == "}") {
        braceDepth -= 1;
      }
      i += 1;
    }
    if (braceDepth > 0) {
      this.pos = savedPos;
      return null as dynamic;
    }
    int posAfterName = this.pos; 
    this.skipWhitespace();
    bool hasWhitespace = this.pos > posAfterName; 
    if (!(hasWhitespace) && (name.isNotEmpty) && "*?@+!\$".contains((name[name.length - 1]).toString())) {
      this.pos = savedPos;
      return null as dynamic;
    }
    if (this.atEnd() || this.peek() != "(") {
      this.pos = savedPos;
      return null as dynamic;
    }
    this.advance();
    this.skipWhitespace();
    if (this.atEnd() || this.peek() != ")") {
      this.pos = savedPos;
      return null as dynamic;
    }
    this.advance();
    this.skipWhitespaceAndNewlines();
    body = this._parseCompoundCommand();
    if (body == null) {
      throw ParseError("Expected function body", this.pos, 0);
    }
    return Function_(name, body, "function");
  }

  dynamic _parseCompoundCommand() {
    dynamic result = this.parseBraceGroup();
    if (result != null) {
      return result;
    }
    if (!(this.atEnd()) && this.peek() == "(" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
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
    return null as dynamic;
  }

  bool _atListUntilTerminator(Set<String> stopWords) {
    if (this.atEnd()) {
      return true;
    }
    if (this.peek() == ")") {
      return true;
    }
    if (this.peek() == "}") {
      int nextPos = this.pos + 1; 
      if (nextPos >= this.length || _isWordEndContext((this.source[nextPos]).toString())) {
        return true;
      }
    }
    String reserved = this._lexPeekReservedWord(); 
    if (reserved != "" && stopWords.contains(reserved)) {
      return true;
    }
    if (this._lexPeekCaseTerminator() != "") {
      return true;
    }
    return false;
  }

  dynamic parseListUntil(Set<String> stopWords) {
    this.skipWhitespaceAndNewlines();
    String reserved = this._lexPeekReservedWord(); 
    if (reserved != "" && stopWords.contains(reserved)) {
      return null as dynamic;
    }
    dynamic pipeline = this.parsePipeline();
    if (pipeline == null) {
      return null as dynamic;
    }
    List<Node> parts = <Node>[pipeline]; 
    while (true) {
      this.skipWhitespace();
      String op = this.parseListOperator(); 
      if (op == "") {
        if (!(this.atEnd()) && this.peek() == "\n") {
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
          if (nextOp == "&" || nextOp == ";") {
            break;
          }
          op = "\n";
        } else {
          break;
        }
      }
      if (op == "") {
        break;
      }
      if (op == ";") {
        this.skipWhitespaceAndNewlines();
        if (this._atListUntilTerminator(stopWords)) {
          break;
        }
        parts.add(Operator(op, "operator"));
      } else {
        if (op == "&") {
          parts.add(Operator(op, "operator"));
          this.skipWhitespaceAndNewlines();
          if (this._atListUntilTerminator(stopWords)) {
            break;
          }
        } else {
          if (op == "&&" || op == "||") {
            parts.add(Operator(op, "operator"));
            this.skipWhitespaceAndNewlines();
          } else {
            parts.add(Operator(op, "operator"));
          }
        }
      }
      if (this._atListUntilTerminator(stopWords)) {
        break;
      }
      pipeline = this.parsePipeline();
      if (pipeline == null) {
        throw ParseError("Expected command after " + op, this.pos, 0);
      }
      parts.add(pipeline);
    }
    if (parts.length == 1) {
      return parts[0];
    }
    return List_(parts, "list");
  }

  dynamic parseCompoundCommand() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null as dynamic;
    }
    String ch = this.peek(); 
    dynamic result;
    if (ch == "(" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "(") {
      result = this.parseArithmeticCommand();
      if (result != null) {
        return result;
      }
    }
    if (ch == "(") {
      return this.parseSubshell();
    }
    if (ch == "{") {
      result = this.parseBraceGroup();
      if (result != null) {
        return result;
      }
    }
    if (ch == "[" && this.pos + 1 < this.length && (this.source[this.pos + 1]).toString() == "[") {
      result = this.parseConditionalExpr();
      if (result != null) {
        return result;
      }
    }
    String reserved = this._lexPeekReservedWord(); 
    if (reserved == "" && this._inProcessSub) {
      String word = this.peekWord(); 
      if (word != "" && word.length > 1 && (word[0]).toString() == "}") {
        String keywordWord = word.substring(1); 
        if (reservedWords.contains(keywordWord) || keywordWord == "{" || keywordWord == "}" || keywordWord == "[[" || keywordWord == "]]" || keywordWord == "!" || keywordWord == "time") {
          reserved = keywordWord;
        }
      }
    }
    if (reserved == "fi" || reserved == "then" || reserved == "elif" || reserved == "else" || reserved == "done" || reserved == "esac" || reserved == "do" || reserved == "in") {
      throw ParseError("Unexpected reserved word '${reserved}'", this._lexPeekToken().pos, 0);
    }
    if (reserved == "if") {
      return this.parseIf();
    }
    if (reserved == "while") {
      return this.parseWhile();
    }
    if (reserved == "until") {
      return this.parseUntil();
    }
    if (reserved == "for") {
      return this.parseFor();
    }
    if (reserved == "select") {
      return this.parseSelect();
    }
    if (reserved == "case") {
      return this.parseCase();
    }
    if (reserved == "function") {
      return this.parseFunction();
    }
    if (reserved == "coproc") {
      return this.parseCoproc();
    }
    dynamic func = this.parseFunction();
    if (func != null) {
      return func;
    }
    return this.parseCommand();
  }

  dynamic parsePipeline() {
    this.skipWhitespace();
    String prefixOrder = ""; 
    bool timePosix = false; 
    if (this._lexIsAtReservedWord("time")) {
      this._lexConsumeWord("time");
      prefixOrder = "time";
      this.skipWhitespace();
      int saved = 0;
      if (!(this.atEnd()) && this.peek() == "-") {
        saved = this.pos;
        this.advance();
        if (!(this.atEnd()) && this.peek() == "p") {
          this.advance();
          if (this.atEnd() || _isMetachar(this.peek())) {
            timePosix = true;
          } else {
            this.pos = saved;
          }
        } else {
          this.pos = saved;
        }
      }
      this.skipWhitespace();
      if (!(this.atEnd()) && _startsWithAt(this.source, this.pos, "--")) {
        if (this.pos + 2 >= this.length || _isWhitespace((this.source[this.pos + 2]).toString())) {
          this.advance();
          this.advance();
          timePosix = true;
          this.skipWhitespace();
        }
      }
      while (this._lexIsAtReservedWord("time")) {
        this._lexConsumeWord("time");
        this.skipWhitespace();
        if (!(this.atEnd()) && this.peek() == "-") {
          saved = this.pos;
          this.advance();
          if (!(this.atEnd()) && this.peek() == "p") {
            this.advance();
            if (this.atEnd() || _isMetachar(this.peek())) {
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
      if (!(this.atEnd()) && this.peek() == "!") {
        if ((this.pos + 1 >= this.length || _isNegationBoundary((this.source[this.pos + 1]).toString())) && !(this._isBangFollowedByProcsub())) {
          this.advance();
          prefixOrder = "time_negation";
          this.skipWhitespace();
        }
      }
    } else {
      if (!(this.atEnd()) && this.peek() == "!") {
        if ((this.pos + 1 >= this.length || _isNegationBoundary((this.source[this.pos + 1]).toString())) && !(this._isBangFollowedByProcsub())) {
          this.advance();
          this.skipWhitespace();
          dynamic inner = this.parsePipeline();
          if (inner != null && inner.kind == "negation") {
            if ((inner as Negation).pipeline != null) {
              return (inner as Negation).pipeline;
            } else {
              return Command(<Word>[], <Node>[], "command");
            }
          }
          return Negation(inner, "negation");
        }
      }
    }
    dynamic result = this._parseSimplePipeline();
    if (prefixOrder == "time") {
      result = Time(result, timePosix, "time");
    } else {
      if (prefixOrder == "negation") {
        result = Negation(result, "negation");
      } else {
        if (prefixOrder == "time_negation") {
          result = Time(result, timePosix, "time");
          result = Negation(result, "negation");
        } else {
          if (prefixOrder == "negation_time") {
            result = Time(result, timePosix, "time");
            result = Negation(result, "negation");
          } else {
            if (result == null) {
              return null as dynamic;
            }
          }
        }
      }
    }
    return result;
  }

  dynamic _parseSimplePipeline() {
    dynamic cmd = this.parseCompoundCommand();
    if (cmd == null) {
      return null as dynamic;
    }
    List<Node> commands = <Node>[cmd]; 
    while (true) {
      this.skipWhitespace();
      final _tuple37 = this._lexPeekOperator();
      int tokenType = _tuple37.$1;
      String value = _tuple37.$2;
      if (tokenType == 0) {
        break;
      }
      if (tokenType != tokentypePipe && tokenType != tokentypePipeAmp) {
        break;
      }
      this._lexNextToken();
      bool isPipeBoth = tokenType == tokentypePipeAmp; 
      this.skipWhitespaceAndNewlines();
      if (isPipeBoth) {
        commands.add(PipeBoth("pipe-both"));
      }
      cmd = this.parseCompoundCommand();
      if (cmd == null) {
        throw ParseError("Expected command after |", this.pos, 0);
      }
      commands.add(cmd);
    }
    if (commands.length == 1) {
      return commands[0];
    }
    return Pipeline(commands, "pipeline");
  }

  String parseListOperator() {
    this.skipWhitespace();
    final _tuple38 = this._lexPeekOperator();
    int tokenType = _tuple38.$1;
    String _ = _tuple38.$2;
    if (tokenType == 0) {
      return "";
    }
    if (tokenType == tokentypeAndAnd) {
      this._lexNextToken();
      return "&&";
    }
    if (tokenType == tokentypeOrOr) {
      this._lexNextToken();
      return "||";
    }
    if (tokenType == tokentypeSemi) {
      this._lexNextToken();
      return ";";
    }
    if (tokenType == tokentypeAmp) {
      this._lexNextToken();
      return "&";
    }
    return "";
  }

  String _peekListOperator() {
    int savedPos = this.pos; 
    String op = this.parseListOperator(); 
    this.pos = savedPos;
    return op;
  }

  dynamic parseList(bool newlineAsSeparator) {
    if (newlineAsSeparator) {
      this.skipWhitespaceAndNewlines();
    } else {
      this.skipWhitespace();
    }
    dynamic pipeline = this.parsePipeline();
    if (pipeline == null) {
      return null as dynamic;
    }
    List<Node> parts = <Node>[pipeline]; 
    if (this._inState(parserstateflagsPstEoftoken) && this._atEofToken()) {
      return (parts.length == 1 ? parts[0] : List_(parts, "list"));
    }
    while (true) {
      this.skipWhitespace();
      String op = this.parseListOperator(); 
      if (op == "") {
        if (!(this.atEnd()) && this.peek() == "\n") {
          if (!(newlineAsSeparator)) {
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
          if (nextOp == "&" || nextOp == ";") {
            break;
          }
          op = "\n";
        } else {
          break;
        }
      }
      if (op == "") {
        break;
      }
      parts.add(Operator(op, "operator"));
      if (op == "&&" || op == "||") {
        this.skipWhitespaceAndNewlines();
      } else {
        if (op == "&") {
          this.skipWhitespace();
          if (this.atEnd() || this._atListTerminatingBracket()) {
            break;
          }
          if (this.peek() == "\n") {
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
          if (op == ";") {
            this.skipWhitespace();
            if (this.atEnd() || this._atListTerminatingBracket()) {
              break;
            }
            if (this.peek() == "\n") {
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
        throw ParseError("Expected command after " + op, this.pos, 0);
      }
      parts.add(pipeline);
      if (this._inState(parserstateflagsPstEoftoken) && this._atEofToken()) {
        break;
      }
    }
    if (parts.length == 1) {
      return parts[0];
    }
    return List_(parts, "list");
  }

  dynamic parseComment() {
    if (this.atEnd() || this.peek() != "#") {
      return null as dynamic;
    }
    int start = this.pos; 
    while (!(this.atEnd()) && this.peek() != "\n") {
      this.advance();
    }
    String text = _substring(this.source, start, this.pos); 
    return Comment(text, "comment");
  }

  List<Node> parse() {
    String source = _trimBoth(this.source, " \t\n\r"); 
    if (!((source.isNotEmpty))) {
      return <Node>[Empty("empty")];
    }
    List<Node> results = <Node>[]; 
    while (true) {
      this.skipWhitespace();
      while (!(this.atEnd()) && this.peek() == "\n") {
        this.advance();
      }
      if (this.atEnd()) {
        break;
      }
      dynamic comment = this.parseComment();
      if (!(comment != null)) {
        break;
      }
    }
    while (!(this.atEnd())) {
      dynamic result = this.parseList(false);
      if (result != null) {
        results.add(result);
      }
      this.skipWhitespace();
      bool foundNewline = false; 
      while (!(this.atEnd()) && this.peek() == "\n") {
        foundNewline = true;
        this.advance();
        this._gatherHeredocBodies();
        if (this._cmdsubHeredocEnd != -1 && this._cmdsubHeredocEnd > this.pos) {
          this.pos = this._cmdsubHeredocEnd;
          this._cmdsubHeredocEnd = -1;
        }
        this.skipWhitespace();
      }
      if (!(foundNewline) && !(this.atEnd())) {
        throw ParseError("Syntax error", this.pos, 0);
      }
    }
    if (!((results.isNotEmpty))) {
      return <Node>[Empty("empty")];
    }
    if (this._sawNewlineInSingleQuote && (this.source.isNotEmpty) && (this.source[this.source.length - 1]).toString() == "\\" && !(this.source.length >= 3 && _safeSubstring(this.source, this.source.length - 3, this.source.length - 1) == "\\\n")) {
      if (!(this._lastWordOnOwnLine(results))) {
        this._stripTrailingBackslashFromLastWord(results);
      }
    }
    return results;
  }

  bool _lastWordOnOwnLine(List<Node> nodes) {
    return nodes.length >= 2;
  }

  void _stripTrailingBackslashFromLastWord(List<Node> nodes) {
    if (!((nodes.isNotEmpty))) {
      return;
    }
    Node lastNode = nodes[nodes.length - 1]; 
    dynamic lastWord = this._findLastWord(lastNode);
    if (lastWord != null && lastWord.value.endsWith("\\")) {
      lastWord.value = _substring(lastWord.value, 0, lastWord.value.length - 1);
      if (!((lastWord.value.isNotEmpty)) && (lastNode is Command) && ((lastNode as Command).words.isNotEmpty)) {
        (lastNode as Command).words.removeLast();
      }
    }
  }

  dynamic _findLastWord(Node node) {
    switch (node) {
      case Word nodeWord:
        return nodeWord;
    }
    switch (node) {
      case Command nodeCommand:
        if ((nodeCommand.words.isNotEmpty)) {
          Word lastWord = nodeCommand.words[nodeCommand.words.length - 1]; 
          if (lastWord.value.endsWith("\\")) {
            return lastWord;
          }
        }
        if ((nodeCommand.redirects.isNotEmpty)) {
          Node lastRedirect = nodeCommand.redirects[nodeCommand.redirects.length - 1]; 
          switch (lastRedirect) {
            case Redirect lastRedirectRedirect:
              return lastRedirectRedirect.target;
          }
        }
        if ((nodeCommand.words.isNotEmpty)) {
          return nodeCommand.words[nodeCommand.words.length - 1];
        }
        break;
    }
    switch (node) {
      case Pipeline nodePipeline:
        if ((nodePipeline.commands.isNotEmpty)) {
          return this._findLastWord(nodePipeline.commands[nodePipeline.commands.length - 1]);
        }
        break;
    }
    switch (node) {
      case List_ nodeList_:
        if ((nodeList_.parts.isNotEmpty)) {
          return this._findLastWord(nodeList_.parts[nodeList_.parts.length - 1]);
        }
        break;
    }
    return null as dynamic;
  }
}

bool _isHexDigit(String c) {
  return (c.compareTo("0") >= 0) && (c.compareTo("9") <= 0) || (c.compareTo("a") >= 0) && (c.compareTo("f") <= 0) || (c.compareTo("A") >= 0) && (c.compareTo("F") <= 0);
}

bool _isOctalDigit(String c) {
  return (c.compareTo("0") >= 0) && (c.compareTo("7") <= 0);
}

int _getAnsiEscape(String c) {
  return (ansiCEscapes[c] ?? -1);
}

bool _isWhitespace(String c) {
  return c == " " || c == "\t" || c == "\n";
}

List<int> _stringToBytes(String s) {
  return List<int>.from(utf8.encode(s));
}

bool _isWhitespaceNoNewline(String c) {
  return c == " " || c == "\t";
}

String _substring(String s, int start, int end) {
  return _safeSubstring(s, start, end);
}

bool _startsWithAt(String s, int pos, String prefix) {
  return (s.indexOf(prefix, pos) == pos);
}

int _countConsecutiveDollarsBefore(String s, int pos) {
  int count = 0; 
  int k = pos - 1; 
  while (k >= 0 && (s[k]).toString() == "\$") {
    int bsCount = 0; 
    int j = k - 1; 
    while (j >= 0 && (s[j]).toString() == "\\") {
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

bool _isExpansionStart(String s, int pos, String delimiter) {
  if (!(_startsWithAt(s, pos, delimiter))) {
    return false;
  }
  return _countConsecutiveDollarsBefore(s, pos) % 2 == 0;
}

List<Node> _sublist(List<Node> lst, int start, int end) {
  return lst.sublist(start, end);
}

String _repeatStr(String s, int n) {
  List<String> result = <String>[]; 
  int i = 0; 
  while (i < n) {
    result.add(s);
    i += 1;
  }
  return result.join("");
}

String _stripLineContinuationsCommentAware(String text) {
  List<String> result = <String>[]; 
  int i = 0; 
  bool inComment = false; 
  dynamic quote = newQuoteState();
  while (i < text.length) {
    String c = (text[i]).toString(); 
    if (c == "\\" && i + 1 < text.length && (text[i + 1]).toString() == "\n") {
      int numPrecedingBackslashes = 0; 
      int j = i - 1; 
      while (j >= 0 && (text[j]).toString() == "\\") {
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
    if (c == "\n") {
      inComment = false;
      result.add(c);
      i += 1;
      continue;
    }
    if (c == "'" && !(quote.double) && !(inComment)) {
      quote.single = !(quote.single);
    } else {
      if (c == "\"" && !(quote.single) && !(inComment)) {
        quote.double = !(quote.double);
      } else {
        if (c == "#" && !(quote.single) && !(inComment)) {
          inComment = true;
        }
      }
    }
    result.add(c);
    i += 1;
  }
  return result.join("");
}

String _appendRedirects(String base, List<Node>? redirects) {
  if ((redirects?.isNotEmpty ?? false)) {
    List<String> parts = <String>[]; 
    for (final r in (redirects ?? <Node>[])) {
      parts.add(r.toSexp());
    }
    return base + " " + parts.join(" ");
  }
  return base;
}

String _formatArithVal(String s) {
  Word w = Word(s, <Node>[], "word"); 
  String val = w._expandAllAnsiCQuotes(s); 
  val = w._stripLocaleStringDollars(val);
  val = w._formatCommandSubstitutions(val, false);
  val = val.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
  val = val.replaceAll("\n", "\\n").replaceAll("\t", "\\t");
  return val;
}

(int, List<String>) _consumeSingleQuote(String s, int start) {
  List<String> chars = <String>["'"]; 
  int i = start + 1; 
  while (i < s.length && (s[i]).toString() != "'") {
    chars.add((s[i]).toString());
    i += 1;
  }
  if (i < s.length) {
    chars.add((s[i]).toString());
    i += 1;
  }
  return (i, chars);
}

(int, List<String>) _consumeDoubleQuote(String s, int start) {
  List<String> chars = <String>["\""]; 
  int i = start + 1; 
  while (i < s.length && (s[i]).toString() != "\"") {
    if ((s[i]).toString() == "\\" && i + 1 < s.length) {
      chars.add((s[i]).toString());
      i += 1;
    }
    chars.add((s[i]).toString());
    i += 1;
  }
  if (i < s.length) {
    chars.add((s[i]).toString());
    i += 1;
  }
  return (i, chars);
}

bool _hasBracketClose(String s, int start, int depth) {
  int i = start; 
  while (i < s.length) {
    if ((s[i]).toString() == "]") {
      return true;
    }
    if (((s[i]).toString() == "|" || (s[i]).toString() == ")") && depth == 0) {
      return false;
    }
    i += 1;
  }
  return false;
}

(int, List<String>, bool) _consumeBracketClass(String s, int start, int depth) {
  int scanPos = start + 1; 
  if (scanPos < s.length && ((s[scanPos]).toString() == "!" || (s[scanPos]).toString() == "^")) {
    scanPos += 1;
  }
  if (scanPos < s.length && (s[scanPos]).toString() == "]") {
    if (_hasBracketClose(s, scanPos + 1, depth)) {
      scanPos += 1;
    }
  }
  bool isBracket = false; 
  while (scanPos < s.length) {
    if ((s[scanPos]).toString() == "]") {
      isBracket = true;
      break;
    }
    if ((s[scanPos]).toString() == ")" && depth == 0) {
      break;
    }
    if ((s[scanPos]).toString() == "|" && depth == 0) {
      break;
    }
    scanPos += 1;
  }
  if (!(isBracket)) {
    return (start + 1, <String>["["], false);
  }
  List<String> chars = <String>["["]; 
  int i = start + 1; 
  if (i < s.length && ((s[i]).toString() == "!" || (s[i]).toString() == "^")) {
    chars.add((s[i]).toString());
    i += 1;
  }
  if (i < s.length && (s[i]).toString() == "]") {
    if (_hasBracketClose(s, i + 1, depth)) {
      chars.add((s[i]).toString());
      i += 1;
    }
  }
  while (i < s.length && (s[i]).toString() != "]") {
    chars.add((s[i]).toString());
    i += 1;
  }
  if (i < s.length) {
    chars.add((s[i]).toString());
    i += 1;
  }
  return (i, chars, true);
}

String _formatCondBody(Node node) {
  String kind = node.kind; 
  if (kind == "unary-test") {
    String operandVal = (node as UnaryTest).operand.getCondFormattedValue(); 
    return (node as UnaryTest).op + " " + operandVal;
  }
  if (kind == "binary-test") {
    String leftVal = (node as BinaryTest).left.getCondFormattedValue(); 
    String rightVal = (node as BinaryTest).right.getCondFormattedValue(); 
    return leftVal + " " + (node as BinaryTest).op + " " + rightVal;
  }
  if (kind == "cond-and") {
    return _formatCondBody((node as CondAnd).left) + " && " + _formatCondBody((node as CondAnd).right);
  }
  if (kind == "cond-or") {
    return _formatCondBody((node as CondOr).left) + " || " + _formatCondBody((node as CondOr).right);
  }
  if (kind == "cond-not") {
    return "! " + _formatCondBody((node as CondNot).operand);
  }
  if (kind == "cond-paren") {
    return "( " + _formatCondBody((node as CondParen).inner) + " )";
  }
  return "";
}

bool _startsWithSubshell(Node node) {
  switch (node) {
    case Subshell nodeSubshell:
      return true;
  }
  switch (node) {
    case List_ nodeList_:
      for (final p in nodeList_.parts) {
        if (p.kind != "operator") {
          return _startsWithSubshell(p);
        }
      }
      return false;
  }
  switch (node) {
    case Pipeline nodePipeline:
      if ((nodePipeline.commands.isNotEmpty)) {
        return _startsWithSubshell(nodePipeline.commands[0]);
      }
      return false;
  }
  return false;
}

String _formatCmdsubNode(Node node, int indent, bool inProcsub, bool compactRedirects, bool procsubFirst) {
  if (node == null) {
    return "";
  }
  String sp = _repeatStr(" ", indent); 
  String innerSp = _repeatStr(" ", indent + 4); 
  switch (node) {
    case ArithEmpty nodeArithEmpty:
      return "";
  }
  switch (node) {
    case Command nodeCommand:
      List<String> parts = <String>[]; 
      for (final w in nodeCommand.words) {
        String val = w._expandAllAnsiCQuotes(w.value); 
        val = w._stripLocaleStringDollars(val);
        val = w._normalizeArrayWhitespace(val);
        val = w._formatCommandSubstitutions(val, false);
        parts.add(val);
      }
      List<HereDoc> heredocs = <HereDoc>[]; 
      for (final r in nodeCommand.redirects) {
        switch (r) {
          case HereDoc rHereDoc:
            heredocs.add(rHereDoc);
            break;
        }
      }
      for (final r in nodeCommand.redirects) {
        parts.add(_formatRedirect(r, compactRedirects, true));
      }
      String result = "";
      if (compactRedirects && (nodeCommand.words.isNotEmpty) && (nodeCommand.redirects.isNotEmpty)) {
        List<String> wordParts = parts.sublist(0, nodeCommand.words.length); 
        List<String> redirectParts = parts.sublist(nodeCommand.words.length); 
        result = wordParts.join(" ") + redirectParts.join("");
      } else {
        result = parts.join(" ");
      }
      for (final h in heredocs) {
        result = result + _formatHeredocBody(h);
      }
      return result;
  }
  switch (node) {
    case Pipeline nodePipeline:
      List<(Node, bool)> cmds = <(Node, bool)>[]; 
      int i = 0; 
      dynamic cmd;
      bool needsRedirect = false;
      while (i < nodePipeline.commands.length) {
        cmd = nodePipeline.commands[i];
        switch (cmd) {
          case PipeBoth cmdPipeBoth:
            i += 1;
            continue;
        }
        needsRedirect = i + 1 < nodePipeline.commands.length && nodePipeline.commands[i + 1].kind == "pipe-both";
        cmds.add((cmd, needsRedirect));
        i += 1;
      }
      List<String> resultParts = <String>[]; 
      int idx = 0; 
      while (idx < cmds.length) {
        {
          (Node, bool) _entry = cmds[idx]; 
          cmd = _entry.$1;
          needsRedirect = _entry.$2;
        }
        String formatted = _formatCmdsubNode(cmd, indent, inProcsub, false, procsubFirst && idx == 0); 
        bool isLast = idx == cmds.length - 1; 
        bool hasHeredoc = false; 
        if (cmd.kind == "command" && ((cmd as Command).redirects.isNotEmpty)) {
          for (final r in (cmd as Command).redirects) {
            bool _breakLoop39 = false;
            switch (r) {
              case HereDoc rHereDoc:
                hasHeredoc = true;
                _breakLoop39 = true;
                break;
            }
            if (_breakLoop39) break;
          }
        }
        int firstNl = 0;
        if (needsRedirect) {
          if (hasHeredoc) {
            firstNl = formatted.indexOf("\n");
            if (firstNl != -1) {
              formatted = _safeSubstring(formatted, 0, firstNl) + " 2>&1" + formatted.substring(firstNl);
            } else {
              formatted = formatted + " 2>&1";
            }
          } else {
            formatted = formatted + " 2>&1";
          }
        }
        if (!(isLast) && hasHeredoc) {
          firstNl = formatted.indexOf("\n");
          if (firstNl != -1) {
            formatted = _safeSubstring(formatted, 0, firstNl) + " |" + formatted.substring(firstNl);
          }
          resultParts.add(formatted);
        } else {
          resultParts.add(formatted);
        }
        idx += 1;
      }
      bool compactPipe = inProcsub && (cmds.isNotEmpty) && cmds[0].$1.kind == "subshell"; 
      String result = ""; 
      idx = 0;
      while (idx < resultParts.length) {
        String part_ = resultParts[idx]; 
        if (idx > 0) {
          if (result.endsWith("\n")) {
            result = result + "  " + part_;
          } else {
            if (compactPipe) {
              result = result + "|" + part_;
            } else {
              result = result + " | " + part_;
            }
          }
        } else {
          result = part_;
        }
        idx += 1;
      }
      return result;
  }
  switch (node) {
    case List_ nodeList_:
      bool hasHeredoc = false; 
      for (final p in nodeList_.parts) {
        if (p.kind == "command" && ((p as Command).redirects.isNotEmpty)) {
          for (final r in (p as Command).redirects) {
            bool _breakLoop40 = false;
            switch (r) {
              case HereDoc rHereDoc:
                hasHeredoc = true;
                _breakLoop40 = true;
                break;
            }
            if (_breakLoop40) break;
          }
        } else {
          switch (p) {
            case Pipeline pPipeline:
              for (final cmd in pPipeline.commands) {
                if (cmd.kind == "command" && ((cmd as Command).redirects.isNotEmpty)) {
                  for (final r in (cmd as Command).redirects) {
                    bool _breakLoop41 = false;
                    switch (r) {
                      case HereDoc rHereDoc:
                        hasHeredoc = true;
                        _breakLoop41 = true;
                        break;
                    }
                    if (_breakLoop41) break;
                  }
                }
                if (hasHeredoc) {
                  break;
                }
              }
              break;
          }
        }
      }
      List<String> result = <String>[]; 
      bool skippedSemi = false; 
      int cmdCount = 0; 
      for (final p in nodeList_.parts) {
        switch (p) {
          case Operator pOperator:
            if (pOperator.op == ";") {
              if ((result.isNotEmpty) && result[result.length - 1].endsWith("\n")) {
                skippedSemi = true;
                continue;
              }
              if (result.length >= 3 && result[result.length - 2] == "\n" && result[result.length - 3].endsWith("\n")) {
                skippedSemi = true;
                continue;
              }
              result.add(";");
              skippedSemi = false;
            } else {
              if (pOperator.op == "\n") {
                if ((result.isNotEmpty) && result[result.length - 1] == ";") {
                  skippedSemi = false;
                  continue;
                }
                if ((result.isNotEmpty) && result[result.length - 1].endsWith("\n")) {
                  result.add((skippedSemi ? " " : "\n"));
                  skippedSemi = false;
                  continue;
                }
                result.add("\n");
                skippedSemi = false;
              } else {
                String last = "";
                int firstNl = 0;
                if (pOperator.op == "&") {
                  if ((result.isNotEmpty) && result[result.length - 1].contains("<<") && result[result.length - 1].contains("\n")) {
                    last = result[result.length - 1];
                    if (last.contains(" |") || last.startsWith("|")) {
                      result[result.length - 1] = last + " &";
                    } else {
                      firstNl = last.indexOf("\n");
                      result[result.length - 1] = _safeSubstring(last, 0, firstNl) + " &" + last.substring(firstNl);
                    }
                  } else {
                    result.add(" &");
                  }
                } else {
                  if ((result.isNotEmpty) && result[result.length - 1].contains("<<") && result[result.length - 1].contains("\n")) {
                    last = result[result.length - 1];
                    firstNl = last.indexOf("\n");
                    result[result.length - 1] = _safeSubstring(last, 0, firstNl) + " " + pOperator.op + " " + last.substring(firstNl);
                  } else {
                    result.add(" " + pOperator.op);
                  }
                }
              }
            }
            break;
          default:
            if ((result.isNotEmpty) && !((result[result.length - 1].endsWith(" ") || result[result.length - 1].endsWith("\n")))) {
              result.add(" ");
            }
            String formattedCmd = _formatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0); 
            if (result.length > 0) {
              String last = result[result.length - 1]; 
              if (last.contains(" || \n") || last.contains(" && \n")) {
                formattedCmd = " " + formattedCmd;
              }
            }
            if (skippedSemi) {
              formattedCmd = " " + formattedCmd;
              skippedSemi = false;
            }
            result.add(formattedCmd);
            cmdCount += 1;
            break;
        }
      }
      String s = result.join(""); 
      if (s.contains(" &\n") && s.endsWith("\n")) {
        return s + " ";
      }
      while (s.endsWith(";")) {
        s = _substring(s, 0, s.length - 1);
      }
      if (!(hasHeredoc)) {
        while (s.endsWith("\n")) {
          s = _substring(s, 0, s.length - 1);
        }
      }
      return s;
  }
  switch (node) {
    case If nodeIf:
      String cond = _formatCmdsubNode(nodeIf.condition, indent, false, false, false); 
      String thenBody = _formatCmdsubNode(nodeIf.thenBody, indent + 4, false, false, false); 
      String result = "if " + cond + "; then\n" + innerSp + thenBody + ";"; 
      if (nodeIf.elseBody != null) {
        String elseBody = _formatCmdsubNode(nodeIf.elseBody!, indent + 4, false, false, false); 
        result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";";
      }
      result = result + "\n" + sp + "fi";
      return result;
  }
  switch (node) {
    case While nodeWhile:
      String cond = _formatCmdsubNode(nodeWhile.condition, indent, false, false, false); 
      String body = _formatCmdsubNode(nodeWhile.body, indent + 4, false, false, false); 
      String result = "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"; 
      if ((nodeWhile.redirects.isNotEmpty)) {
        for (final r in nodeWhile.redirects) {
          result = result + " " + _formatRedirect(r, false, false);
        }
      }
      return result;
  }
  switch (node) {
    case Until nodeUntil:
      String cond = _formatCmdsubNode(nodeUntil.condition, indent, false, false, false); 
      String body = _formatCmdsubNode(nodeUntil.body, indent + 4, false, false, false); 
      String result = "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"; 
      if ((nodeUntil.redirects.isNotEmpty)) {
        for (final r in nodeUntil.redirects) {
          result = result + " " + _formatRedirect(r, false, false);
        }
      }
      return result;
  }
  switch (node) {
    case For nodeFor:
      String var_ = nodeFor.var_; 
      String body = _formatCmdsubNode(nodeFor.body, indent + 4, false, false, false); 
      String result = "";
      if (nodeFor.words != null) {
        List<String> wordVals = <String>[]; 
        for (final w in (nodeFor.words ?? <Word>[])) {
          wordVals.add(w.value);
        }
        String words = wordVals.join(" "); 
        if ((words.isNotEmpty)) {
          result = "for " + var_ + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
        } else {
          result = "for " + var_ + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
        }
      } else {
        result = "for " + var_ + " in \"\$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
      }
      if ((nodeFor.redirects.isNotEmpty)) {
        for (final r in nodeFor.redirects) {
          result = result + " " + _formatRedirect(r, false, false);
        }
      }
      return result;
  }
  switch (node) {
    case ForArith nodeForArith:
      String body = _formatCmdsubNode(nodeForArith.body, indent + 4, false, false, false); 
      String result = "for ((" + nodeForArith.init + "; " + nodeForArith.cond + "; " + nodeForArith.incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done"; 
      if ((nodeForArith.redirects.isNotEmpty)) {
        for (final r in nodeForArith.redirects) {
          result = result + " " + _formatRedirect(r, false, false);
        }
      }
      return result;
  }
  switch (node) {
    case Case nodeCase:
      String word = nodeCase.word.value; 
      List<String> patterns = <String>[]; 
      int i = 0; 
      while (i < nodeCase.patterns.length) {
        CasePattern p = nodeCase.patterns[i]; 
        String pat = p.pattern.replaceAll("|", " | "); 
        String body = "";
        if (p.body != null) {
          body = _formatCmdsubNode(p.body!, indent + 8, false, false, false);
        } else {
          body = "";
        }
        String term = p.terminator; 
        String patIndent = _repeatStr(" ", indent + 8); 
        String termIndent = _repeatStr(" ", indent + 4); 
        String bodyPart = ((body.isNotEmpty) ? patIndent + body + "\n" : "\n"); 
        if (i == 0) {
          patterns.add(" " + pat + ")\n" + bodyPart + termIndent + term);
        } else {
          patterns.add(pat + ")\n" + bodyPart + termIndent + term);
        }
        i += 1;
      }
      dynamic patternStr = patterns.join("\n" + _repeatStr(" ", indent + 4));
      String redirects = ""; 
      if ((nodeCase.redirects.isNotEmpty)) {
        List<String> redirectParts = <String>[]; 
        for (final r in nodeCase.redirects) {
          redirectParts.add(_formatRedirect(r, false, false));
        }
        redirects = " " + redirectParts.join(" ");
      }
      return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects;
  }
  switch (node) {
    case Function_ nodeFunction_:
      String name = nodeFunction_.name; 
      Node innerBody = (nodeFunction_.body.kind == "brace-group" ? (nodeFunction_.body as BraceGroup).body : nodeFunction_.body); 
      String body = _trimRight(_formatCmdsubNode(innerBody, indent + 4, false, false, false), ";"); 
      return "function ${name} () \n{ \n${innerSp}${body}\n}";
  }
  switch (node) {
    case Subshell nodeSubshell:
      String body = _formatCmdsubNode(nodeSubshell.body, indent, inProcsub, compactRedirects, false); 
      String redirects = ""; 
      if ((nodeSubshell.redirects?.isNotEmpty ?? false)) {
        List<String> redirectParts = <String>[]; 
        for (final r in (nodeSubshell.redirects ?? <Node>[])) {
          redirectParts.add(_formatRedirect(r, false, false));
        }
        redirects = redirectParts.join(" ");
      }
      if (procsubFirst) {
        if ((redirects.isNotEmpty)) {
          return "(" + body + ") " + redirects;
        }
        return "(" + body + ")";
      }
      if ((redirects.isNotEmpty)) {
        return "( " + body + " ) " + redirects;
      }
      return "( " + body + " )";
  }
  switch (node) {
    case BraceGroup nodeBraceGroup:
      String body = _formatCmdsubNode(nodeBraceGroup.body, indent, false, false, false); 
      body = _trimRight(body, ";");
      String terminator = (body.endsWith(" &") ? " }" : "; }"); 
      String redirects = ""; 
      if ((nodeBraceGroup.redirects?.isNotEmpty ?? false)) {
        List<String> redirectParts = <String>[]; 
        for (final r in (nodeBraceGroup.redirects ?? <Node>[])) {
          redirectParts.add(_formatRedirect(r, false, false));
        }
        redirects = redirectParts.join(" ");
      }
      if ((redirects.isNotEmpty)) {
        return "{ " + body + terminator + " " + redirects;
      }
      return "{ " + body + terminator;
  }
  switch (node) {
    case ArithmeticCommand nodeArithmeticCommand:
      return "((" + nodeArithmeticCommand.rawContent + "))";
  }
  switch (node) {
    case ConditionalExpr nodeConditionalExpr:
      String body = _formatCondBody((nodeConditionalExpr.body as Node)); 
      return "[[ " + body + " ]]";
  }
  switch (node) {
    case Negation nodeNegation:
      if (nodeNegation.pipeline != null) {
        return "! " + _formatCmdsubNode(nodeNegation.pipeline, indent, false, false, false);
      }
      return "! ";
  }
  switch (node) {
    case Time nodeTime:
      String prefix = (nodeTime.posix ? "time -p " : "time "); 
      if (nodeTime.pipeline != null) {
        return prefix + _formatCmdsubNode(nodeTime.pipeline, indent, false, false, false);
      }
      return prefix;
  }
  return "";
}

String _formatRedirect(Node r, bool compact, bool heredocOpOnly) {
  String op = "";
  switch (r) {
    case HereDoc rHereDoc:
      if (rHereDoc.stripTabs) {
        op = "<<-";
      } else {
        op = "<<";
      }
      if (rHereDoc.fd > 0) {
        op = rHereDoc.fd.toString() + op;
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
  op = (r as Redirect).op;
  if (op == "1>") {
    op = ">";
  } else {
    if (op == "0<") {
      op = "<";
    }
  }
  String target = (r as Redirect).target.value; 
  target = (r as Redirect).target._expandAllAnsiCQuotes(target);
  target = (r as Redirect).target._stripLocaleStringDollars(target);
  target = (r as Redirect).target._formatCommandSubstitutions(target, false);
  if (target.startsWith("&")) {
    bool wasInputClose = false; 
    if (target == "&-" && op.endsWith("<")) {
      wasInputClose = true;
      op = _substring(op, 0, op.length - 1) + ">";
    }
    String afterAmp = _substring(target, 1, target.length); 
    bool isLiteralFd = afterAmp == "-" || afterAmp.length > 0 && ((afterAmp[0]).toString().isNotEmpty && RegExp(r'^\d+$').hasMatch((afterAmp[0]).toString())); 
    if (isLiteralFd) {
      if (op == ">" || op == ">&") {
        op = (wasInputClose ? "0>" : "1>");
      } else {
        if (op == "<" || op == "<&") {
          op = "0<";
        }
      }
    } else {
      if (op == "1>") {
        op = ">";
      } else {
        if (op == "0<") {
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

String _formatHeredocBody(HereDoc r) {
  return "\n" + r.content + r.delimiter + "\n";
}

bool _lookaheadForEsac(String value, int start, int caseDepth) {
  int i = start; 
  int depth = caseDepth; 
  dynamic quote = newQuoteState();
  while (i < value.length) {
    String c = (value[i]).toString(); 
    if (c == "\\" && i + 1 < value.length && quote.double) {
      i += 2;
      continue;
    }
    if (c == "'" && !(quote.double)) {
      quote.single = !(quote.single);
      i += 1;
      continue;
    }
    if (c == "\"" && !(quote.single)) {
      quote.double = !(quote.double);
      i += 1;
      continue;
    }
    if (quote.single || quote.double) {
      i += 1;
      continue;
    }
    if (_startsWithAt(value, i, "case") && _isWordBoundary(value, i, 4)) {
      depth += 1;
      i += 4;
    } else {
      if (_startsWithAt(value, i, "esac") && _isWordBoundary(value, i, 4)) {
        depth -= 1;
        if (depth == 0) {
          return true;
        }
        i += 4;
      } else {
        if (c == "(") {
          i += 1;
        } else {
          if (c == ")") {
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

int _skipBacktick(String value, int start) {
  int i = start + 1; 
  while (i < value.length && (value[i]).toString() != "`") {
    if ((value[i]).toString() == "\\" && i + 1 < value.length) {
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

int _skipSingleQuoted(String s, int start) {
  int i = start; 
  while (i < s.length && (s[i]).toString() != "'") {
    i += 1;
  }
  return (i < s.length ? i + 1 : i);
}

int _skipDoubleQuoted(String s, int start) {
  int i = start; 
  int n = s.length; 
  bool passNext = false; 
  bool backq = false; 
  while (i < n) {
    String c = (s[i]).toString(); 
    if (passNext) {
      passNext = false;
      i += 1;
      continue;
    }
    if (c == "\\") {
      passNext = true;
      i += 1;
      continue;
    }
    if (backq) {
      if (c == "`") {
        backq = false;
      }
      i += 1;
      continue;
    }
    if (c == "`") {
      backq = true;
      i += 1;
      continue;
    }
    if (c == "\$" && i + 1 < n) {
      if ((s[i + 1]).toString() == "(") {
        i = _findCmdsubEnd(s, i + 2);
        continue;
      }
      if ((s[i + 1]).toString() == "{") {
        i = _findBracedParamEnd(s, i + 2);
        continue;
      }
    }
    if (c == "\"") {
      return i + 1;
    }
    i += 1;
  }
  return i;
}

bool _isValidArithmeticStart(String value, int start) {
  int scanParen = 0; 
  int scanI = start + 3; 
  while (scanI < value.length) {
    String scanC = (value[scanI]).toString(); 
    if (_isExpansionStart(value, scanI, "\$(")) {
      scanI = _findCmdsubEnd(value, scanI + 2);
      continue;
    }
    if (scanC == "(") {
      scanParen += 1;
    } else {
      if (scanC == ")") {
        if (scanParen > 0) {
          scanParen -= 1;
        } else {
          if (scanI + 1 < value.length && (value[scanI + 1]).toString() == ")") {
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

int _findFunsubEnd(String value, int start) {
  int depth = 1; 
  int i = start; 
  dynamic quote = newQuoteState();
  while (i < value.length && depth > 0) {
    String c = (value[i]).toString(); 
    if (c == "\\" && i + 1 < value.length && !(quote.single)) {
      i += 2;
      continue;
    }
    if (c == "'" && !(quote.double)) {
      quote.single = !(quote.single);
      i += 1;
      continue;
    }
    if (c == "\"" && !(quote.single)) {
      quote.double = !(quote.double);
      i += 1;
      continue;
    }
    if (quote.single || quote.double) {
      i += 1;
      continue;
    }
    if (c == "{") {
      depth += 1;
    } else {
      if (c == "}") {
        depth -= 1;
        if (depth == 0) {
          return i + 1;
        }
      }
    }
    i += 1;
  }
  return value.length;
}

int _findCmdsubEnd(String value, int start) {
  int depth = 1; 
  int i = start; 
  int caseDepth = 0; 
  bool inCasePatterns = false; 
  int arithDepth = 0; 
  int arithParenDepth = 0; 
  while (i < value.length && depth > 0) {
    String c = (value[i]).toString(); 
    if (c == "\\" && i + 1 < value.length) {
      i += 2;
      continue;
    }
    if (c == "'") {
      i = _skipSingleQuoted(value, i + 1);
      continue;
    }
    if (c == "\"") {
      i = _skipDoubleQuoted(value, i + 1);
      continue;
    }
    if (c == "#" && arithDepth == 0 && (i == start || (value[i - 1]).toString() == " " || (value[i - 1]).toString() == "\t" || (value[i - 1]).toString() == "\n" || (value[i - 1]).toString() == ";" || (value[i - 1]).toString() == "|" || (value[i - 1]).toString() == "&" || (value[i - 1]).toString() == "(" || (value[i - 1]).toString() == ")")) {
      while (i < value.length && (value[i]).toString() != "\n") {
        i += 1;
      }
      continue;
    }
    if (_startsWithAt(value, i, "<<<")) {
      i += 3;
      while (i < value.length && ((value[i]).toString() == " " || (value[i]).toString() == "\t")) {
        i += 1;
      }
      if (i < value.length && (value[i]).toString() == "\"") {
        i += 1;
        while (i < value.length && (value[i]).toString() != "\"") {
          if ((value[i]).toString() == "\\" && i + 1 < value.length) {
            i += 2;
          } else {
            i += 1;
          }
        }
        if (i < value.length) {
          i += 1;
        }
      } else {
        if (i < value.length && (value[i]).toString() == "'") {
          i += 1;
          while (i < value.length && (value[i]).toString() != "'") {
            i += 1;
          }
          if (i < value.length) {
            i += 1;
          }
        } else {
          while (i < value.length && !" \t\n;|&<>()".contains((value[i]).toString())) {
            i += 1;
          }
        }
      }
      continue;
    }
    if (_isExpansionStart(value, i, "\$((")) {
      if (_isValidArithmeticStart(value, i)) {
        arithDepth += 1;
        i += 3;
        continue;
      }
      int j = _findCmdsubEnd(value, i + 2); 
      i = j;
      continue;
    }
    if (arithDepth > 0 && arithParenDepth == 0 && _startsWithAt(value, i, "))")) {
      arithDepth -= 1;
      i += 2;
      continue;
    }
    if (c == "`") {
      i = _skipBacktick(value, i);
      continue;
    }
    if (arithDepth == 0 && _startsWithAt(value, i, "<<")) {
      i = _skipHeredoc(value, i);
      continue;
    }
    if (_startsWithAt(value, i, "case") && _isWordBoundary(value, i, 4)) {
      caseDepth += 1;
      inCasePatterns = false;
      i += 4;
      continue;
    }
    if (caseDepth > 0 && _startsWithAt(value, i, "in") && _isWordBoundary(value, i, 2)) {
      inCasePatterns = true;
      i += 2;
      continue;
    }
    if (_startsWithAt(value, i, "esac") && _isWordBoundary(value, i, 4)) {
      if (caseDepth > 0) {
        caseDepth -= 1;
        inCasePatterns = false;
      }
      i += 4;
      continue;
    }
    if (_startsWithAt(value, i, ";;")) {
      i += 2;
      continue;
    }
    if (c == "(") {
      if (!(inCasePatterns && caseDepth > 0)) {
        if (arithDepth > 0) {
          arithParenDepth += 1;
        } else {
          depth += 1;
        }
      }
    } else {
      if (c == ")") {
        if (inCasePatterns && caseDepth > 0) {
          if (!(_lookaheadForEsac(value, i + 1, caseDepth))) {
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

int _findBracedParamEnd(String value, int start) {
  int depth = 1; 
  int i = start; 
  bool inDouble = false; 
  int dolbraceState = dolbracestateParam; 
  while (i < value.length && depth > 0) {
    String c = (value[i]).toString(); 
    if (c == "\\" && i + 1 < value.length) {
      i += 2;
      continue;
    }
    if (c == "'" && dolbraceState == dolbracestateQuote && !(inDouble)) {
      i = _skipSingleQuoted(value, i + 1);
      continue;
    }
    if (c == "\"") {
      inDouble = !(inDouble);
      i += 1;
      continue;
    }
    if (inDouble) {
      i += 1;
      continue;
    }
    if (dolbraceState == dolbracestateParam && "%#^,".contains(c)) {
      dolbraceState = dolbracestateQuote;
    } else {
      if (dolbraceState == dolbracestateParam && ":-=?+/".contains(c)) {
        dolbraceState = dolbracestateWord;
      }
    }
    if (c == "[" && dolbraceState == dolbracestateParam && !(inDouble)) {
      int end = _skipSubscript(value, i, 0); 
      if (end != -1) {
        i = end;
        continue;
      }
    }
    if ((c == "<" || c == ">") && i + 1 < value.length && (value[i + 1]).toString() == "(") {
      i = _findCmdsubEnd(value, i + 2);
      continue;
    }
    if (c == "{") {
      depth += 1;
    } else {
      if (c == "}") {
        depth -= 1;
        if (depth == 0) {
          return i + 1;
        }
      }
    }
    if (_isExpansionStart(value, i, "\$(")) {
      i = _findCmdsubEnd(value, i + 2);
      continue;
    }
    if (_isExpansionStart(value, i, "\${")) {
      i = _findBracedParamEnd(value, i + 2);
      continue;
    }
    i += 1;
  }
  return i;
}

int _skipHeredoc(String value, int start) {
  int i = start + 2; 
  if (i < value.length && (value[i]).toString() == "-") {
    i += 1;
  }
  while (i < value.length && _isWhitespaceNoNewline((value[i]).toString())) {
    i += 1;
  }
  int delimStart = i; 
  dynamic? quoteChar = null;
  String delimiter = "";
  if (i < value.length && ((value[i]).toString() == "\"" || (value[i]).toString() == "'")) {
    quoteChar = (value[i]).toString();
    i += 1;
    delimStart = i;
    while (i < value.length && (value[i]).toString() != quoteChar) {
      i += 1;
    }
    delimiter = _substring(value, delimStart, i);
    if (i < value.length) {
      i += 1;
    }
  } else {
    if (i < value.length && (value[i]).toString() == "\\") {
      i += 1;
      delimStart = i;
      if (i < value.length) {
        i += 1;
      }
      while (i < value.length && !(_isMetachar((value[i]).toString()))) {
        i += 1;
      }
      delimiter = _substring(value, delimStart, i);
    } else {
      while (i < value.length && !(_isMetachar((value[i]).toString()))) {
        i += 1;
      }
      delimiter = _substring(value, delimStart, i);
    }
  }
  int parenDepth = 0; 
  dynamic quote = newQuoteState();
  bool inBacktick = false; 
  while (i < value.length && (value[i]).toString() != "\n") {
    String c = (value[i]).toString(); 
    if (c == "\\" && i + 1 < value.length && (quote.double || inBacktick)) {
      i += 2;
      continue;
    }
    if (c == "'" && !(quote.double) && !(inBacktick)) {
      quote.single = !(quote.single);
      i += 1;
      continue;
    }
    if (c == "\"" && !(quote.single) && !(inBacktick)) {
      quote.double = !(quote.double);
      i += 1;
      continue;
    }
    if (c == "`" && !(quote.single)) {
      inBacktick = !(inBacktick);
      i += 1;
      continue;
    }
    if (quote.single || quote.double || inBacktick) {
      i += 1;
      continue;
    }
    if (c == "(") {
      parenDepth += 1;
    } else {
      if (c == ")") {
        if (parenDepth == 0) {
          break;
        }
        parenDepth -= 1;
      }
    }
    i += 1;
  }
  if (i < value.length && (value[i]).toString() == ")") {
    return i;
  }
  if (i < value.length && (value[i]).toString() == "\n") {
    i += 1;
  }
  while (i < value.length) {
    int lineStart = i; 
    int lineEnd = i; 
    while (lineEnd < value.length && (value[lineEnd]).toString() != "\n") {
      lineEnd += 1;
    }
    String line = _substring(value, lineStart, lineEnd); 
    while (lineEnd < value.length) {
      int trailingBs = 0; 
      for (int j = line.length - 1; j > -1; j += -1) {
        if ((line[j]).toString() == "\\") {
          trailingBs += 1;
        } else {
          break;
        }
      }
      if (trailingBs % 2 == 0) {
        break;
      }
      line = _safeSubstring(line, 0, line.length - 1);
      lineEnd += 1;
      int nextLineStart = lineEnd; 
      while (lineEnd < value.length && (value[lineEnd]).toString() != "\n") {
        lineEnd += 1;
      }
      line = line + _substring(value, nextLineStart, lineEnd);
    }
    String stripped = "";
    if (start + 2 < value.length && (value[start + 2]).toString() == "-") {
      stripped = _trimLeft(line, "\t");
    } else {
      stripped = line;
    }
    if (stripped == delimiter) {
      if (lineEnd < value.length) {
        return lineEnd + 1;
      } else {
        return lineEnd;
      }
    }
    if (stripped.startsWith(delimiter) && stripped.length > delimiter.length) {
      int tabsStripped = line.length - stripped.length; 
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

(int, int) _findHeredocContentEnd(String source, int start, List<(String, bool)> delimiters) {
  if (!((delimiters.isNotEmpty))) {
    return (start, start);
  }
  int pos = start; 
  while (pos < source.length && (source[pos]).toString() != "\n") {
    pos += 1;
  }
  if (pos >= source.length) {
    return (start, start);
  }
  int contentStart = pos; 
  pos += 1;
  for (final _item in delimiters) {
    String delimiter = _item.$1; 
    bool stripTabs = _item.$2; 
    while (pos < source.length) {
      int lineStart = pos; 
      int lineEnd = pos; 
      while (lineEnd < source.length && (source[lineEnd]).toString() != "\n") {
        lineEnd += 1;
      }
      String line = _substring(source, lineStart, lineEnd); 
      while (lineEnd < source.length) {
        int trailingBs = 0; 
        for (int j = line.length - 1; j > -1; j += -1) {
          if ((line[j]).toString() == "\\") {
            trailingBs += 1;
          } else {
            break;
          }
        }
        if (trailingBs % 2 == 0) {
          break;
        }
        line = _safeSubstring(line, 0, line.length - 1);
        lineEnd += 1;
        int nextLineStart = lineEnd; 
        while (lineEnd < source.length && (source[lineEnd]).toString() != "\n") {
          lineEnd += 1;
        }
        line = line + _substring(source, nextLineStart, lineEnd);
      }
      String lineStripped = "";
      if (stripTabs) {
        lineStripped = _trimLeft(line, "\t");
      } else {
        lineStripped = line;
      }
      if (lineStripped == delimiter) {
        pos = (lineEnd < source.length ? lineEnd + 1 : lineEnd);
        break;
      }
      if (lineStripped.startsWith(delimiter) && lineStripped.length > delimiter.length) {
        int tabsStripped = line.length - lineStripped.length; 
        pos = lineStart + tabsStripped + delimiter.length;
        break;
      }
      pos = (lineEnd < source.length ? lineEnd + 1 : lineEnd);
    }
  }
  return (contentStart, pos);
}

bool _isWordBoundary(String s, int pos, int wordLen) {
  if (pos > 0) {
    String prev = (s[pos - 1]).toString(); 
    if ((prev.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(prev)) || prev == "_") {
      return false;
    }
    if ("{}!".contains(prev)) {
      return false;
    }
  }
  int end = pos + wordLen; 
  if (end < s.length && (((s[end]).toString().isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch((s[end]).toString())) || (s[end]).toString() == "_")) {
    return false;
  }
  return true;
}

bool _isQuote(String c) {
  return c == "'" || c == "\"";
}

String _collapseWhitespace(String s) {
  List<String> result = <String>[]; 
  bool prevWasWs = false; 
  for (final _c7 in s.split('')) {
    var c = _c7;
    if (c == " " || c == "\t") {
      if (!(prevWasWs)) {
        result.add(" ");
      }
      prevWasWs = true;
    } else {
      result.add(c);
      prevWasWs = false;
    }
  }
  String joined = result.join(""); 
  return _trimBoth(joined, " \t");
}

int _countTrailingBackslashes(String s) {
  int count = 0; 
  for (int i = s.length - 1; i > -1; i += -1) {
    if ((s[i]).toString() == "\\") {
      count += 1;
    } else {
      break;
    }
  }
  return count;
}

String _normalizeHeredocDelimiter(String delimiter) {
  List<String> result = <String>[]; 
  int i = 0; 
  while (i < delimiter.length) {
    int depth = 0;
    List<String> inner = <String>[];
    String innerStr = "";
    if (i + 1 < delimiter.length && _safeSubstring(delimiter, i, i + 2) == "\$(") {
      result.add("\$(");
      i += 2;
      depth = 1;
      inner = <String>[];
      while (i < delimiter.length && depth > 0) {
        if ((delimiter[i]).toString() == "(") {
          depth += 1;
          inner.add((delimiter[i]).toString());
        } else {
          if ((delimiter[i]).toString() == ")") {
            depth -= 1;
            if (depth == 0) {
              innerStr = inner.join("");
              innerStr = _collapseWhitespace(innerStr);
              result.add(innerStr);
              result.add(")");
            } else {
              inner.add((delimiter[i]).toString());
            }
          } else {
            inner.add((delimiter[i]).toString());
          }
        }
        i += 1;
      }
    } else {
      if (i + 1 < delimiter.length && _safeSubstring(delimiter, i, i + 2) == "\${") {
        result.add("\${");
        i += 2;
        depth = 1;
        inner = <String>[];
        while (i < delimiter.length && depth > 0) {
          if ((delimiter[i]).toString() == "{") {
            depth += 1;
            inner.add((delimiter[i]).toString());
          } else {
            if ((delimiter[i]).toString() == "}") {
              depth -= 1;
              if (depth == 0) {
                innerStr = inner.join("");
                innerStr = _collapseWhitespace(innerStr);
                result.add(innerStr);
                result.add("}");
              } else {
                inner.add((delimiter[i]).toString());
              }
            } else {
              inner.add((delimiter[i]).toString());
            }
          }
          i += 1;
        }
      } else {
        if (i + 1 < delimiter.length && "<>".contains((delimiter[i]).toString()) && (delimiter[i + 1]).toString() == "(") {
          result.add((delimiter[i]).toString());
          result.add("(");
          i += 2;
          depth = 1;
          inner = <String>[];
          while (i < delimiter.length && depth > 0) {
            if ((delimiter[i]).toString() == "(") {
              depth += 1;
              inner.add((delimiter[i]).toString());
            } else {
              if ((delimiter[i]).toString() == ")") {
                depth -= 1;
                if (depth == 0) {
                  innerStr = inner.join("");
                  innerStr = _collapseWhitespace(innerStr);
                  result.add(innerStr);
                  result.add(")");
                } else {
                  inner.add((delimiter[i]).toString());
                }
              } else {
                inner.add((delimiter[i]).toString());
              }
            }
            i += 1;
          }
        } else {
          result.add((delimiter[i]).toString());
          i += 1;
        }
      }
    }
  }
  return result.join("");
}

bool _isMetachar(String c) {
  return c == " " || c == "\t" || c == "\n" || c == "|" || c == "&" || c == ";" || c == "(" || c == ")" || c == "<" || c == ">";
}

bool _isFunsubChar(String c) {
  return c == " " || c == "\t" || c == "\n" || c == "|";
}

bool _isExtglobPrefix(String c) {
  return c == "@" || c == "?" || c == "*" || c == "+" || c == "!";
}

bool _isRedirectChar(String c) {
  return c == "<" || c == ">";
}

bool _isSpecialParam(String c) {
  return c == "?" || c == "\$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-" || c == "&";
}

bool _isSpecialParamUnbraced(String c) {
  return c == "?" || c == "\$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-";
}

bool _isDigit(String c) {
  return (c.compareTo("0") >= 0) && (c.compareTo("9") <= 0);
}

bool _isSemicolonOrNewline(String c) {
  return c == ";" || c == "\n";
}

bool _isWordEndContext(String c) {
  return c == " " || c == "\t" || c == "\n" || c == ";" || c == "|" || c == "&" || c == "<" || c == ">" || c == "(" || c == ")";
}

int _skipMatchedPair(String s, int start, String open, String close, int flags) {
  int n = s.length; 
  int i = 0;
  if ((flags & _smpPastOpen != 0)) {
    i = start;
  } else {
    if (start >= n || (s[start]).toString() != open) {
      return -1;
    }
    i = start + 1;
  }
  int depth = 1; 
  bool passNext = false; 
  bool backq = false; 
  while (i < n && depth > 0) {
    String c = (s[i]).toString(); 
    if (passNext) {
      passNext = false;
      i += 1;
      continue;
    }
    int literal = flags & _smpLiteral; 
    if (!((literal != 0)) && c == "\\") {
      passNext = true;
      i += 1;
      continue;
    }
    if (backq) {
      if (c == "`") {
        backq = false;
      }
      i += 1;
      continue;
    }
    if (!((literal != 0)) && c == "`") {
      backq = true;
      i += 1;
      continue;
    }
    if (!((literal != 0)) && c == "'") {
      i = _skipSingleQuoted(s, i + 1);
      continue;
    }
    if (!((literal != 0)) && c == "\"") {
      i = _skipDoubleQuoted(s, i + 1);
      continue;
    }
    if (!((literal != 0)) && _isExpansionStart(s, i, "\$(")) {
      i = _findCmdsubEnd(s, i + 2);
      continue;
    }
    if (!((literal != 0)) && _isExpansionStart(s, i, "\${")) {
      i = _findBracedParamEnd(s, i + 2);
      continue;
    }
    if (!((literal != 0)) && c == open) {
      depth += 1;
    } else {
      if (c == close) {
        depth -= 1;
      }
    }
    i += 1;
  }
  return (depth == 0 ? i : -1);
}

int _skipSubscript(String s, int start, int flags) {
  return _skipMatchedPair(s, start, "[", "]", flags);
}

int _assignment(String s, int flags) {
  if (!((s.isNotEmpty))) {
    return -1;
  }
  if (!(((s[0]).toString().isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch((s[0]).toString())) || (s[0]).toString() == "_")) {
    return -1;
  }
  int i = 1; 
  while (i < s.length) {
    String c = (s[i]).toString(); 
    if (c == "=") {
      return i;
    }
    if (c == "[") {
      int subFlags = ((flags & 2 != 0) ? _smpLiteral : 0); 
      int end = _skipSubscript(s, i, subFlags); 
      if (end == -1) {
        return -1;
      }
      i = end;
      if (i < s.length && (s[i]).toString() == "+") {
        i += 1;
      }
      if (i < s.length && (s[i]).toString() == "=") {
        return i;
      }
      return -1;
    }
    if (c == "+") {
      if (i + 1 < s.length && (s[i + 1]).toString() == "=") {
        return i + 1;
      }
      return -1;
    }
    if (!((c.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(c)) || c == "_")) {
      return -1;
    }
    i += 1;
  }
  return -1;
}

bool _isArrayAssignmentPrefix(List<String> chars) {
  if (!((chars.isNotEmpty))) {
    return false;
  }
  if (!((chars[0].isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch(chars[0])) || chars[0] == "_")) {
    return false;
  }
  String s = chars.join(""); 
  int i = 1; 
  while (i < s.length && (((s[i]).toString().isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch((s[i]).toString())) || (s[i]).toString() == "_")) {
    i += 1;
  }
  while (i < s.length) {
    if ((s[i]).toString() != "[") {
      return false;
    }
    int end = _skipSubscript(s, i, _smpLiteral); 
    if (end == -1) {
      return false;
    }
    i = end;
  }
  return true;
}

bool _isSpecialParamOrDigit(String c) {
  return _isSpecialParam(c) || _isDigit(c);
}

bool _isParamExpansionOp(String c) {
  return c == ":" || c == "-" || c == "=" || c == "+" || c == "?" || c == "#" || c == "%" || c == "/" || c == "^" || c == "," || c == "@" || c == "*" || c == "[";
}

bool _isSimpleParamOp(String c) {
  return c == "-" || c == "=" || c == "?" || c == "+";
}

bool _isEscapeCharInBacktick(String c) {
  return c == "\$" || c == "`" || c == "\\";
}

bool _isNegationBoundary(String c) {
  return _isWhitespace(c) || c == ";" || c == "|" || c == ")" || c == "&" || c == ">" || c == "<";
}

bool _isBackslashEscaped(String value, int idx) {
  int bsCount = 0; 
  int j = idx - 1; 
  while (j >= 0 && (value[j]).toString() == "\\") {
    bsCount += 1;
    j -= 1;
  }
  return bsCount % 2 == 1;
}

bool _isDollarDollarParen(String value, int idx) {
  int dollarCount = 0; 
  int j = idx - 1; 
  while (j >= 0 && (value[j]).toString() == "\$") {
    dollarCount += 1;
    j -= 1;
  }
  return dollarCount % 2 == 1;
}

bool _isParen(String c) {
  return c == "(" || c == ")";
}

bool _isCaretOrBang(String c) {
  return c == "!" || c == "^";
}

bool _isAtOrStar(String c) {
  return c == "@" || c == "*";
}

bool _isDigitOrDash(String c) {
  return _isDigit(c) || c == "-";
}

bool _isNewlineOrRightParen(String c) {
  return c == "\n" || c == ")";
}

bool _isSemicolonNewlineBrace(String c) {
  return c == ";" || c == "\n" || c == "{";
}

bool _looksLikeAssignment(String s) {
  return _assignment(s, 0) != -1;
}

bool _isValidIdentifier(String name) {
  if (!((name.isNotEmpty))) {
    return false;
  }
  if (!(((name[0]).toString().isNotEmpty && RegExp(r'^[a-zA-Z]+$').hasMatch((name[0]).toString())) || (name[0]).toString() == "_")) {
    return false;
  }
  for (final _c8 in name.substring(1).split('')) {
    var c = _c8;
    if (!((c.isNotEmpty && RegExp(r'^[a-zA-Z0-9]+$').hasMatch(c)) || c == "_")) {
      return false;
    }
  }
  return true;
}

List<Node> parse(String source, bool extglob) {
  dynamic parser = newParser(source, false, extglob);
  return parser.parse();
}

ParseError newParseError(String message, int pos, int line) {
  ParseError self = ParseError("", 0, 0); 
  self.message = message;
  self.pos = pos;
  self.line = line;
  return self;
}

MatchedPairError newMatchedPairError(String message, int pos, int line) {
  return MatchedPairError(message, pos, line);
}

QuoteState newQuoteState() {
  QuoteState self = QuoteState(false, false, <(bool, bool)>[]); 
  self.single = false;
  self.double = false;
  self._stack = <(bool, bool)>[];
  return self;
}

ParseContext newParseContext(int kind) {
  ParseContext self = ParseContext(0, 0, 0, 0, 0, 0, 0, null as dynamic); 
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

ContextStack newContextStack() {
  ContextStack self = ContextStack(<ParseContext>[]); 
  self._stack = <ParseContext>[newParseContext(0)];
  return self;
}

Lexer newLexer(String source, bool extglob) {
  Lexer self = Lexer({}, "", 0, 0, null as dynamic, null, 0, 0, <Node>[], false, null, "", null, 0, false, false, false, 0, 0, false, false, false); 
  self.source = source;
  self.pos = 0;
  self.length = source.length;
  self.quote = newQuoteState();
  self._tokenCache = null as dynamic;
  self._parserState = parserstateflagsNone;
  self._dolbraceState = dolbracestateNone;
  self._pendingHeredocs = <Node>[];
  self._extglob = extglob;
  self._parser = null as dynamic;
  self._eofToken = "";
  self._lastReadToken = null as dynamic;
  self._wordContext = wordCtxNormal;
  self._atCommandStart = false;
  self._inArrayLiteral = false;
  self._inAssignBuiltin = false;
  self._postReadPos = 0;
  self._cachedWordContext = wordCtxNormal;
  self._cachedAtCommandStart = false;
  self._cachedInArrayLiteral = false;
  self._cachedInAssignBuiltin = false;
  return self;
}

Parser newParser(String source, bool inProcessSub, bool extglob) {
  Parser self = Parser("", 0, 0, <HereDoc>[], 0, false, false, false, null as dynamic, null as dynamic, <Token?>[], 0, 0, "", 0, false, false, false, "", 0, 0); 
  self.source = source;
  self.pos = 0;
  self.length = source.length;
  self._pendingHeredocs = <HereDoc>[];
  self._cmdsubHeredocEnd = -1;
  self._sawNewlineInSingleQuote = false;
  self._inProcessSub = inProcessSub;
  self._extglob = extglob;
  self._ctx = newContextStack();
  self._lexer = newLexer(source, extglob);
  self._lexer._parser = self;
  self._tokenHistory = <Token?>[null, null, null, null];
  self._parserState = parserstateflagsNone;
  self._dolbraceState = dolbracestateNone;
  self._eofToken = "";
  self._wordContext = wordCtxNormal;
  self._atCommandStart = false;
  self._inArrayLiteral = false;
  self._inAssignBuiltin = false;
  self._arithSrc = "";
  self._arithPos = 0;
  self._arithLen = 0;
  return self;
}

// Helper functions
int _min(int a, int b) => a < b ? a : b;
int _max(int a, int b) => a > b ? a : b;

// Safe substring that clamps indices like Python slice semantics
String _safeSubstring(String s, int start, int end) {
  if (start < 0) start = 0;
  if (end > s.length) end = s.length;
  if (start >= end) return '';
  return s.substring(start, end);
}

List<int> _range(int start, int stop, int step) {
  final result = <int>[];
  if (step > 0) {
    for (var i = start; i < stop; i += step) result.add(i);
  } else {
    for (var i = start; i > stop; i += step) result.add(i);
  }
  return result;
}

String _trimLeft(String s, String chars) {
  int i = 0;
  while (i < s.length && chars.contains(s[i])) i++;
  return s.substring(i);
}

String _trimRight(String s, String chars) {
  int i = s.length;
  while (i > 0 && chars.contains(s[i - 1])) i--;
  return s.substring(0, i);
}

String _trimBoth(String s, String chars) {
  return _trimRight(_trimLeft(s, chars), chars);
}
