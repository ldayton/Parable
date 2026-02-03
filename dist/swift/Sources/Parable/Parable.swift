import Foundation

// Helper functions
func _charAt(_ s: String, _ i: Int) -> String {
    let idx = s.index(s.startIndex, offsetBy: i)
    return String(s[idx])
}

func _charArray(_ s: String) -> [String] {
    s.map { String($0) }
}

func range(_ end: Int) -> [Int] {
    Swift.Array(0..<end)
}

func range(_ start: Int, _ end: Int) -> [Int] {
    Swift.Array(start..<end)
}

func range(_ start: Int, _ end: Int, _ step: Int) -> [Int] {
    stride(from: start, to: end, by: step).map { $0 }
}

func readAllStdin() -> String {
    var result = ""
    while let line = readLine(strippingNewline: false) {
        result += line
    }
    return result
}

let ansiCEscapes: [String: Int] = ["a": 7, "b": 8, "e": 27, "E": 27, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11, "\\": 92, "\"": 34, "?": 63]
let tokentypeEof: Int = 0
let tokentypeWord: Int = 1
let tokentypeNewline: Int = 2
let tokentypeSemi: Int = 10
let tokentypePipe: Int = 11
let tokentypeAmp: Int = 12
let tokentypeLparen: Int = 13
let tokentypeRparen: Int = 14
let tokentypeLbrace: Int = 15
let tokentypeRbrace: Int = 16
let tokentypeLess: Int = 17
let tokentypeGreater: Int = 18
let tokentypeAndAnd: Int = 30
let tokentypeOrOr: Int = 31
let tokentypeSemiSemi: Int = 32
let tokentypeSemiAmp: Int = 33
let tokentypeSemiSemiAmp: Int = 34
let tokentypeLessLess: Int = 35
let tokentypeGreaterGreater: Int = 36
let tokentypeLessAmp: Int = 37
let tokentypeGreaterAmp: Int = 38
let tokentypeLessGreater: Int = 39
let tokentypeGreaterPipe: Int = 40
let tokentypeLessLessMinus: Int = 41
let tokentypeLessLessLess: Int = 42
let tokentypeAmpGreater: Int = 43
let tokentypeAmpGreaterGreater: Int = 44
let tokentypePipeAmp: Int = 45
let tokentypeIf: Int = 50
let tokentypeThen: Int = 51
let tokentypeElse: Int = 52
let tokentypeElif: Int = 53
let tokentypeFi: Int = 54
let tokentypeCase: Int = 55
let tokentypeEsac: Int = 56
let tokentypeFor: Int = 57
let tokentypeWhile: Int = 58
let tokentypeUntil: Int = 59
let tokentypeDo: Int = 60
let tokentypeDone: Int = 61
let tokentypeIn: Int = 62
let tokentypeFunction: Int = 63
let tokentypeSelect: Int = 64
let tokentypeCoproc: Int = 65
let tokentypeTime: Int = 66
let tokentypeBang: Int = 67
let tokentypeLbracketLbracket: Int = 68
let tokentypeRbracketRbracket: Int = 69
let tokentypeAssignmentWord: Int = 80
let tokentypeNumber: Int = 81
let parserstateflagsNone: Int = 0
let parserstateflagsPstCasepat: Int = 1
let parserstateflagsPstCmdsubst: Int = 2
let parserstateflagsPstCasestmt: Int = 4
let parserstateflagsPstCondexpr: Int = 8
let parserstateflagsPstCompassign: Int = 16
let parserstateflagsPstArith: Int = 32
let parserstateflagsPstHeredoc: Int = 64
let parserstateflagsPstRegexp: Int = 128
let parserstateflagsPstExtpat: Int = 256
let parserstateflagsPstSubshell: Int = 512
let parserstateflagsPstRedirlist: Int = 1024
let parserstateflagsPstComment: Int = 2048
let parserstateflagsPstEoftoken: Int = 4096
let dolbracestateNone: Int = 0
let dolbracestateParam: Int = 1
let dolbracestateOp: Int = 2
let dolbracestateWord: Int = 4
let dolbracestateQuote: Int = 64
let dolbracestateQuote2: Int = 128
let matchedpairflagsNone: Int = 0
let matchedpairflagsDquote: Int = 1
let matchedpairflagsDolbrace: Int = 2
let matchedpairflagsCommand: Int = 4
let matchedpairflagsArith: Int = 8
let matchedpairflagsAllowesc: Int = 16
let matchedpairflagsExtglob: Int = 32
let matchedpairflagsFirstclose: Int = 64
let matchedpairflagsArraysub: Int = 128
let matchedpairflagsBackquote: Int = 256
let parsecontextNormal: Int = 0
let parsecontextCommandSub: Int = 1
let parsecontextArithmetic: Int = 2
let parsecontextCasePattern: Int = 3
let parsecontextBraceExpansion: Int = 4
let reservedWords: Set<String> = Set(["if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"])
let condUnaryOps: Set<String> = Set(["-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"])
let condBinaryOps: Set<String> = Set(["==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"])
let compoundKeywords: Set<String> = Set(["while", "until", "for", "if", "case", "select"])
let assignmentBuiltins: Set<String> = Set(["alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"])
let _smpLiteral: Int = 1
let _smpPastOpen: Int = 2
let wordCtxNormal: Int = 0
let wordCtxCond: Int = 1
let wordCtxRegex: Int = 2

protocol Node {
    var kind: String { get set }
    func getKind() -> String
    func toSexp() -> String
}

class ParseError: Error {
    var message: String = ""
    var pos: Int = 0
    var line: Int = 0

    init(message: String = "", pos: Int = 0, line: Int = 0) {
        self.message = message
        self.pos = pos
        self.line = line
    }

    func _formatMessage() -> String {
        if self.line != 0 && self.pos != 0 {
            return "Parse error at line \\(self.line), position \\(self.pos): \\(self.message)"
        } else {
            if self.pos != 0 {
                return "Parse error at position \\(self.pos): \\(self.message)"
            }
        }
        return "Parse error: \\(self.message)"
    }
}

class MatchedPairError: ParseError {
    override init(message: String = "", pos: Int = 0, line: Int = 0) {
        super.init(message: message, pos: pos, line: line)
    }
}

class TokenType {
    init() {}
}

class Token {
    var type: Int = 0
    var value: String = ""
    var pos: Int = 0
    var parts: [Node] = []
    var word: Word?

    init(type: Int = 0, value: String = "", pos: Int = 0, parts: [Node] = [], word: Word? = nil) {
        self.type = type
        self.value = value
        self.pos = pos
        self.parts = parts
        self.word = word
    }

    func _Repr() -> String {
        if self.word != nil {
            return "Token(\\(self.type), \\(self.value), \\(self.pos), word=\\(self.word))"
        }
        if (!self.parts.isEmpty) {
            return "Token(\\(self.type), \\(self.value), \\(self.pos), parts=\\(self.parts.count))"
        }
        return "Token(\\(self.type), \\(self.value), \\(self.pos))"
    }
}

class ParserStateFlags {
    init() {}
}

class DolbraceState {
    init() {}
}

class MatchedPairFlags {
    init() {}
}

class SavedParserState {
    var parserState: Int = 0
    var dolbraceState: Int = 0
    var pendingHeredocs: [Node] = []
    var ctxStack: [ParseContext] = []
    var eofToken: String = ""

    init(parserState: Int = 0, dolbraceState: Int = 0, pendingHeredocs: [Node] = [], ctxStack: [ParseContext] = [], eofToken: String = "") {
        self.parserState = parserState
        self.dolbraceState = dolbraceState
        self.pendingHeredocs = pendingHeredocs
        self.ctxStack = ctxStack
        self.eofToken = eofToken
    }
}

class QuoteState {
    var single: Bool = false
    var double: Bool = false
    var _stack: [(Bool, Bool)] = []

    init(single: Bool = false, double: Bool = false, _stack: [(Bool, Bool)] = []) {
        self.single = single
        self.double = double
        self._stack = _stack
    }

    func push() {
        self._stack.append((self.single, self.double))
        self.single = false
        self.double = false
    }

    func pop() {
        if (!self._stack.isEmpty) {
            let _tuple1 = self._stack.removeLast()
            self.single = _tuple1.0
            self.double = _tuple1.1
        }
    }

    func inQuotes() -> Bool {
        return self.single || self.double
    }

    func copy() -> QuoteState {
        var qs: QuoteState = newQuoteState()
        qs.single = self.single
        qs.double = self.double
        qs._stack = Swift.Array(self._stack)
        return qs
    }

    func outerDouble() -> Bool {
        if self._stack.count == 0 {
            return false
        }
        return self._stack[self._stack.count - 1].1
    }
}

class ParseContext {
    var kind: Int = 0
    var parenDepth: Int = 0
    var braceDepth: Int = 0
    var bracketDepth: Int = 0
    var caseDepth: Int = 0
    var arithDepth: Int = 0
    var arithParenDepth: Int = 0
    var quote: QuoteState!

    init(kind: Int = 0, parenDepth: Int = 0, braceDepth: Int = 0, bracketDepth: Int = 0, caseDepth: Int = 0, arithDepth: Int = 0, arithParenDepth: Int = 0, quote: QuoteState? = nil) {
        self.kind = kind
        self.parenDepth = parenDepth
        self.braceDepth = braceDepth
        self.bracketDepth = bracketDepth
        self.caseDepth = caseDepth
        self.arithDepth = arithDepth
        self.arithParenDepth = arithParenDepth
        if let quote = quote { self.quote = quote }
    }

    func copy() -> ParseContext {
        var ctx: ParseContext = newParseContext(self.kind)
        ctx.parenDepth = self.parenDepth
        ctx.braceDepth = self.braceDepth
        ctx.bracketDepth = self.bracketDepth
        ctx.caseDepth = self.caseDepth
        ctx.arithDepth = self.arithDepth
        ctx.arithParenDepth = self.arithParenDepth
        ctx.quote = self.quote.copy()
        return ctx
    }
}

class ContextStack {
    var _stack: [ParseContext] = []

    init(_stack: [ParseContext] = []) {
        self._stack = _stack
    }

    func getCurrent() -> ParseContext {
        return self._stack[self._stack.count - 1]
    }

    func push(_ kind: Int) {
        self._stack.append(newParseContext(kind))
    }

    func pop() -> ParseContext {
        if self._stack.count > 1 {
            return self._stack.removeLast()
        }
        return self._stack[0]
    }

    func copyStack() -> [ParseContext] {
        var result: [ParseContext] = []
        for ctx in self._stack {
            result.append(ctx.copy())
        }
        return result
    }

    func restoreFrom(_ savedStack: [ParseContext]) {
        var result: [ParseContext] = []
        for ctx in savedStack {
            result.append(ctx.copy())
        }
        self._stack = result
    }
}

class Lexer {
    var reservedWords: [String: Int] = [:]
    var source: String = ""
    var pos: Int = 0
    var length: Int = 0
    var quote: QuoteState!
    var _tokenCache: Token?
    var _parserState: Int = 0
    var _dolbraceState: Int = 0
    var _pendingHeredocs: [Node] = []
    var _extglob: Bool = false
    var _parser: Parser?
    var _eofToken: String = ""
    var _lastReadToken: Token?
    var _wordContext: Int = 0
    var _atCommandStart: Bool = false
    var _inArrayLiteral: Bool = false
    var _inAssignBuiltin: Bool = false
    var _postReadPos: Int = 0
    var _cachedWordContext: Int = 0
    var _cachedAtCommandStart: Bool = false
    var _cachedInArrayLiteral: Bool = false
    var _cachedInAssignBuiltin: Bool = false

    init(reservedWords: [String: Int] = [:], source: String = "", pos: Int = 0, length: Int = 0, quote: QuoteState? = nil, _tokenCache: Token? = nil, _parserState: Int = 0, _dolbraceState: Int = 0, _pendingHeredocs: [Node] = [], _extglob: Bool = false, _parser: Parser? = nil, _eofToken: String = "", _lastReadToken: Token? = nil, _wordContext: Int = 0, _atCommandStart: Bool = false, _inArrayLiteral: Bool = false, _inAssignBuiltin: Bool = false, _postReadPos: Int = 0, _cachedWordContext: Int = 0, _cachedAtCommandStart: Bool = false, _cachedInArrayLiteral: Bool = false, _cachedInAssignBuiltin: Bool = false) {
        self.reservedWords = reservedWords
        self.source = source
        self.pos = pos
        self.length = length
        if let quote = quote { self.quote = quote }
        self._tokenCache = _tokenCache
        self._parserState = _parserState
        self._dolbraceState = _dolbraceState
        self._pendingHeredocs = _pendingHeredocs
        self._extglob = _extglob
        self._parser = _parser
        self._eofToken = _eofToken
        self._lastReadToken = _lastReadToken
        self._wordContext = _wordContext
        self._atCommandStart = _atCommandStart
        self._inArrayLiteral = _inArrayLiteral
        self._inAssignBuiltin = _inAssignBuiltin
        self._postReadPos = _postReadPos
        self._cachedWordContext = _cachedWordContext
        self._cachedAtCommandStart = _cachedAtCommandStart
        self._cachedInArrayLiteral = _cachedInArrayLiteral
        self._cachedInAssignBuiltin = _cachedInAssignBuiltin
    }

    func peek() -> String {
        if self.pos >= self.length {
            return ""
        }
        return String(_charAt(self.source, self.pos))
    }

    func advance() -> String {
        if self.pos >= self.length {
            return ""
        }
        var c: String = String(_charAt(self.source, self.pos))
        self.pos += 1
        return c
    }

    func atEnd() -> Bool {
        return self.pos >= self.length
    }

    func lookahead(_ n: Int) -> String {
        return _substring(self.source, self.pos, self.pos + n)
    }

    func isMetachar(_ c: String) -> Bool {
        return "|&;()<> \t\n".contains(c)
    }

    func _readOperator() -> Token? {
        var start: Int = self.pos
        var c: String = self.peek()
        if c == "" {
            return nil
        }
        var two: String = self.lookahead(2)
        var three: String = self.lookahead(3)
        if three == ";;&" {
            self.pos += 3
            return Token(type: tokentypeSemiSemiAmp, value: three, pos: start, parts: [], word: nil)
        }
        if three == "<<-" {
            self.pos += 3
            return Token(type: tokentypeLessLessMinus, value: three, pos: start, parts: [], word: nil)
        }
        if three == "<<<" {
            self.pos += 3
            return Token(type: tokentypeLessLessLess, value: three, pos: start, parts: [], word: nil)
        }
        if three == "&>>" {
            self.pos += 3
            return Token(type: tokentypeAmpGreaterGreater, value: three, pos: start, parts: [], word: nil)
        }
        if two == "&&" {
            self.pos += 2
            return Token(type: tokentypeAndAnd, value: two, pos: start, parts: [], word: nil)
        }
        if two == "||" {
            self.pos += 2
            return Token(type: tokentypeOrOr, value: two, pos: start, parts: [], word: nil)
        }
        if two == ";;" {
            self.pos += 2
            return Token(type: tokentypeSemiSemi, value: two, pos: start, parts: [], word: nil)
        }
        if two == ";&" {
            self.pos += 2
            return Token(type: tokentypeSemiAmp, value: two, pos: start, parts: [], word: nil)
        }
        if two == "<<" {
            self.pos += 2
            return Token(type: tokentypeLessLess, value: two, pos: start, parts: [], word: nil)
        }
        if two == ">>" {
            self.pos += 2
            return Token(type: tokentypeGreaterGreater, value: two, pos: start, parts: [], word: nil)
        }
        if two == "<&" {
            self.pos += 2
            return Token(type: tokentypeLessAmp, value: two, pos: start, parts: [], word: nil)
        }
        if two == ">&" {
            self.pos += 2
            return Token(type: tokentypeGreaterAmp, value: two, pos: start, parts: [], word: nil)
        }
        if two == "<>" {
            self.pos += 2
            return Token(type: tokentypeLessGreater, value: two, pos: start, parts: [], word: nil)
        }
        if two == ">|" {
            self.pos += 2
            return Token(type: tokentypeGreaterPipe, value: two, pos: start, parts: [], word: nil)
        }
        if two == "&>" {
            self.pos += 2
            return Token(type: tokentypeAmpGreater, value: two, pos: start, parts: [], word: nil)
        }
        if two == "|&" {
            self.pos += 2
            return Token(type: tokentypePipeAmp, value: two, pos: start, parts: [], word: nil)
        }
        if c == ";" {
            self.pos += 1
            return Token(type: tokentypeSemi, value: c, pos: start, parts: [], word: nil)
        }
        if c == "|" {
            self.pos += 1
            return Token(type: tokentypePipe, value: c, pos: start, parts: [], word: nil)
        }
        if c == "&" {
            self.pos += 1
            return Token(type: tokentypeAmp, value: c, pos: start, parts: [], word: nil)
        }
        if c == "(" {
            if self._wordContext == wordCtxRegex {
                return nil
            }
            self.pos += 1
            return Token(type: tokentypeLparen, value: c, pos: start, parts: [], word: nil)
        }
        if c == ")" {
            if self._wordContext == wordCtxRegex {
                return nil
            }
            self.pos += 1
            return Token(type: tokentypeRparen, value: c, pos: start, parts: [], word: nil)
        }
        if c == "<" {
            if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                return nil
            }
            self.pos += 1
            return Token(type: tokentypeLess, value: c, pos: start, parts: [], word: nil)
        }
        if c == ">" {
            if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                return nil
            }
            self.pos += 1
            return Token(type: tokentypeGreater, value: c, pos: start, parts: [], word: nil)
        }
        if c == "\n" {
            self.pos += 1
            return Token(type: tokentypeNewline, value: c, pos: start, parts: [], word: nil)
        }
        return nil
    }

    func skipBlanks() {
        while self.pos < self.length {
            var c: String = String(_charAt(self.source, self.pos))
            if c != " " && c != "\t" {
                break
            }
            self.pos += 1
        }
    }

    func _skipComment() -> Bool {
        if self.pos >= self.length {
            return false
        }
        if String(_charAt(self.source, self.pos)) != "#" {
            return false
        }
        if self.quote.inQuotes() {
            return false
        }
        if self.pos > 0 {
            var prev: String = String(_charAt(self.source, self.pos - 1))
            if !" \t\n;|&(){}".contains(prev) {
                return false
            }
        }
        while self.pos < self.length && String(_charAt(self.source, self.pos)) != "\n" {
            self.pos += 1
        }
        return true
    }

    func _readSingleQuote(_ start: Int) throws -> (String, Bool) {
        var chars: [String] = ["'"]
        var sawNewline: Bool = false
        while self.pos < self.length {
            var c: String = String(_charAt(self.source, self.pos))
            if c == "\n" {
                sawNewline = true
            }
            chars.append(c)
            self.pos += 1
            if c == "'" {
                return (chars.joined(separator: ""), sawNewline)
            }
        }
        throw ParseError(message: "Unterminated single quote", pos: start)
    }

    func _isWordTerminator(_ ctx: Int, _ ch: String, _ bracketDepth: Int, _ parenDepth: Int) -> Bool {
        if ctx == wordCtxRegex {
            if ch == "]" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "]" {
                return true
            }
            if ch == "&" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "&" {
                return true
            }
            if ch == ")" && parenDepth == 0 {
                return true
            }
            return _isWhitespace(ch) && parenDepth == 0
        }
        if ctx == wordCtxCond {
            if ch == "]" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "]" {
                return true
            }
            if ch == ")" {
                return true
            }
            if ch == "&" {
                return true
            }
            if ch == "|" {
                return true
            }
            if ch == ";" {
                return true
            }
            if _isRedirectChar(ch) && !(self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(") {
                return true
            }
            return _isWhitespace(ch)
        }
        if (self._parserState & parserstateflagsPstEoftoken != 0) && self._eofToken != "" && ch == self._eofToken && bracketDepth == 0 {
            return true
        }
        if _isRedirectChar(ch) && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
            return false
        }
        return _isMetachar(ch) && bracketDepth == 0
    }

    func _readBracketExpression(_ chars: [String], _ parts: [Node], _ forRegex: Bool, _ parenDepth: Int) -> Bool {
        if forRegex {
            var scan: Int = self.pos + 1
            if scan < self.length && String(_charAt(self.source, scan)) == "^" {
                scan += 1
            }
            if scan < self.length && String(_charAt(self.source, scan)) == "]" {
                scan += 1
            }
            var bracketWillClose: Bool = false
            while scan < self.length {
                var sc: String = String(_charAt(self.source, scan))
                if sc == "]" && scan + 1 < self.length && String(_charAt(self.source, scan + 1)) == "]" {
                    break
                }
                if sc == ")" && parenDepth > 0 {
                    break
                }
                if sc == "&" && scan + 1 < self.length && String(_charAt(self.source, scan + 1)) == "&" {
                    break
                }
                if sc == "]" {
                    bracketWillClose = true
                    break
                }
                if sc == "[" && scan + 1 < self.length && String(_charAt(self.source, scan + 1)) == ":" {
                    scan += 2
                    while scan < self.length && !(String(_charAt(self.source, scan)) == ":" && scan + 1 < self.length && String(_charAt(self.source, scan + 1)) == "]") {
                        scan += 1
                    }
                    if scan < self.length {
                        scan += 2
                    }
                    continue
                }
                scan += 1
            }
            if !bracketWillClose {
                return false
            }
        } else {
            if self.pos + 1 >= self.length {
                return false
            }
            var nextCh: String = String(_charAt(self.source, self.pos + 1))
            if _isWhitespaceNoNewline(nextCh) || nextCh == "&" || nextCh == "|" {
                return false
            }
        }
        chars.append(self.advance())
        if !self.atEnd() && self.peek() == "^" {
            chars.append(self.advance())
        }
        if !self.atEnd() && self.peek() == "]" {
            chars.append(self.advance())
        }
        while !self.atEnd() {
            var c: String = self.peek()
            if c == "]" {
                chars.append(self.advance())
                break
            }
            if c == "[" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == ":" {
                chars.append(self.advance())
                chars.append(self.advance())
                while !self.atEnd() && !(self.peek() == ":" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "]") {
                    chars.append(self.advance())
                }
                if !self.atEnd() {
                    chars.append(self.advance())
                    chars.append(self.advance())
                }
            } else {
                if !forRegex && c == "[" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "=" {
                    chars.append(self.advance())
                    chars.append(self.advance())
                    while !self.atEnd() && !(self.peek() == "=" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "]") {
                        chars.append(self.advance())
                    }
                    if !self.atEnd() {
                        chars.append(self.advance())
                        chars.append(self.advance())
                    }
                } else {
                    if !forRegex && c == "[" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "." {
                        chars.append(self.advance())
                        chars.append(self.advance())
                        while !self.atEnd() && !(self.peek() == "." && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "]") {
                            chars.append(self.advance())
                        }
                        if !self.atEnd() {
                            chars.append(self.advance())
                            chars.append(self.advance())
                        }
                    } else {
                        if forRegex && c == "$" {
                            self._syncToParser()
                            if try !self._parser!._parseDollarExpansion(chars, parts, false) {
                                self._syncFromParser()
                                chars.append(self.advance())
                            } else {
                                self._syncFromParser()
                            }
                        } else {
                            chars.append(self.advance())
                        }
                    }
                }
            }
        }
        return true
    }

    func _parseMatchedPair(_ openChar: String, _ closeChar: String, _ flags: Int, _ initialWasDollar: Bool) throws -> String {
        var start: Int = self.pos
        var count: Int = 1
        var chars: [String] = []
        var passNext: Bool = false
        var wasDollar: Bool = initialWasDollar
        var wasGtlt: Bool = false
        while count > 0 {
            if self.atEnd() {
                throw MatchedPairError(message: "unexpected EOF while looking for matching `\\(closeChar)'", pos: start)
            }
            var ch: String = self.advance()
            if (flags & matchedpairflagsDolbrace != 0) && self._dolbraceState == dolbracestateOp {
                if !"#%^,~:-=?+/".contains(ch) {
                    self._dolbraceState = dolbracestateWord
                }
            }
            if passNext {
                passNext = false
                chars.append(ch)
                wasDollar = ch == "$"
                wasGtlt = "<>".contains(ch)
                continue
            }
            if openChar == "'" {
                if ch == closeChar {
                    count -= 1
                    if count == 0 {
                        break
                    }
                }
                if ch == "\\" && (flags & matchedpairflagsAllowesc != 0) {
                    passNext = true
                }
                chars.append(ch)
                wasDollar = false
                wasGtlt = false
                continue
            }
            if ch == "\\" {
                if !self.atEnd() && self.peek() == "\n" {
                    self.advance()
                    wasDollar = false
                    wasGtlt = false
                    continue
                }
                passNext = true
                chars.append(ch)
                wasDollar = false
                wasGtlt = false
                continue
            }
            if ch == closeChar {
                count -= 1
                if count == 0 {
                    break
                }
                chars.append(ch)
                wasDollar = false
                wasGtlt = "<>".contains(ch)
                continue
            }
            if ch == openChar && openChar != closeChar {
                if !((flags & matchedpairflagsDolbrace != 0) && openChar == "{") {
                    count += 1
                }
                chars.append(ch)
                wasDollar = false
                wasGtlt = "<>".contains(ch)
                continue
            }
            if "'\"`".contains(ch) && openChar != closeChar {
                var nested: String = ""
                if ch == "'" {
                    chars.append(ch)
                    var quoteFlags: Int = (wasDollar ? flags | matchedpairflagsAllowesc : flags)
                    nested = try self._parseMatchedPair("'", "'", quoteFlags, false)
                    chars.append(nested)
                    chars.append("'")
                    wasDollar = false
                    wasGtlt = false
                    continue
                } else {
                    if ch == "\"" {
                        chars.append(ch)
                        nested = try self._parseMatchedPair("\"", "\"", flags | matchedpairflagsDquote, false)
                        chars.append(nested)
                        chars.append("\"")
                        wasDollar = false
                        wasGtlt = false
                        continue
                    } else {
                        if ch == "`" {
                            chars.append(ch)
                            nested = try self._parseMatchedPair("`", "`", flags, false)
                            chars.append(nested)
                            chars.append("`")
                            wasDollar = false
                            wasGtlt = false
                            continue
                        }
                    }
                }
            }
            if ch == "$" && !self.atEnd() && !(flags & matchedpairflagsExtglob != 0) {
                var nextCh: String = self.peek()
                if wasDollar {
                    chars.append(ch)
                    wasDollar = false
                    wasGtlt = false
                    continue
                }
                if nextCh == "{" {
                    if (flags & matchedpairflagsArith != 0) {
                        var afterBracePos: Int = self.pos + 1
                        if afterBracePos >= self.length || !_isFunsubChar(String(_charAt(self.source, afterBracePos))) {
                            chars.append(ch)
                            wasDollar = true
                            wasGtlt = false
                            continue
                        }
                    }
                    self.pos -= 1
                    self._syncToParser()
                    var inDquote: Bool = flags & matchedpairflagsDquote != 0
                    let _tuple2 = try self._parser!._parseParamExpansion(inDquote)
                    var paramNode: Node? = _tuple2.0
                    var paramText: String = _tuple2.1
                    self._syncFromParser()
                    if paramNode != nil {
                        chars.append(paramText)
                        wasDollar = false
                        wasGtlt = false
                    } else {
                        chars.append(self.advance())
                        wasDollar = true
                        wasGtlt = false
                    }
                    continue
                } else {
                    var arithNode: Node? = nil
                    var arithText: String = ""
                    if nextCh == "(" {
                        self.pos -= 1
                        self._syncToParser()
                        var cmdNode: Node? = nil
                        var cmdText: String = ""
                        if self.pos + 2 < self.length && String(_charAt(self.source, self.pos + 2)) == "(" {
                            let _tuple3 = try self._parser!._parseArithmeticExpansion()
                            arithNode = _tuple3.0
                            arithText = _tuple3.1
                            self._syncFromParser()
                            if arithNode != nil {
                                chars.append(arithText)
                                wasDollar = false
                                wasGtlt = false
                            } else {
                                self._syncToParser()
                                let _tuple4 = try self._parser!._parseCommandSubstitution()
                                cmdNode = _tuple4.0
                                cmdText = _tuple4.1
                                self._syncFromParser()
                                if cmdNode != nil {
                                    chars.append(cmdText)
                                    wasDollar = false
                                    wasGtlt = false
                                } else {
                                    chars.append(self.advance())
                                    chars.append(self.advance())
                                    wasDollar = false
                                    wasGtlt = false
                                }
                            }
                        } else {
                            let _tuple5 = try self._parser!._parseCommandSubstitution()
                            cmdNode = _tuple5.0
                            cmdText = _tuple5.1
                            self._syncFromParser()
                            if cmdNode != nil {
                                chars.append(cmdText)
                                wasDollar = false
                                wasGtlt = false
                            } else {
                                chars.append(self.advance())
                                chars.append(self.advance())
                                wasDollar = false
                                wasGtlt = false
                            }
                        }
                        continue
                    } else {
                        if nextCh == "[" {
                            self.pos -= 1
                            self._syncToParser()
                            let _tuple6 = try self._parser!._parseDeprecatedArithmetic()
                            arithNode = _tuple6.0
                            arithText = _tuple6.1
                            self._syncFromParser()
                            if arithNode != nil {
                                chars.append(arithText)
                                wasDollar = false
                                wasGtlt = false
                            } else {
                                chars.append(self.advance())
                                wasDollar = true
                                wasGtlt = false
                            }
                            continue
                        }
                    }
                }
            }
            if ch == "(" && wasGtlt && (flags & matchedpairflagsDolbrace | matchedpairflagsArraysub != 0) {
                var direction: String = chars[chars.count - 1]
                chars = Swift.Array(chars[..<(chars.count - 1)])
                self.pos -= 1
                self._syncToParser()
                let _tuple7 = try self._parser!._parseProcessSubstitution()
                var procsubNode: Node? = _tuple7.0
                var procsubText: String = _tuple7.1
                self._syncFromParser()
                if procsubNode != nil {
                    chars.append(procsubText)
                    wasDollar = false
                    wasGtlt = false
                } else {
                    chars.append(direction)
                    chars.append(self.advance())
                    wasDollar = false
                    wasGtlt = false
                }
                continue
            }
            chars.append(ch)
            wasDollar = ch == "$"
            wasGtlt = "<>".contains(ch)
        }
        return chars.joined(separator: "")
    }

    func _collectParamArgument(_ flags: Int, _ wasDollar: Bool) throws -> String {
        return try self._parseMatchedPair("{", "}", flags | matchedpairflagsDolbrace, wasDollar)
    }

    func _readWordInternal(_ ctx: Int, _ atCommandStart: Bool, _ inArrayLiteral: Bool, _ inAssignBuiltin: Bool) throws -> Word? {
        var start: Int = self.pos
        var chars: [String] = []
        var parts: [Node] = []
        var bracketDepth: Int = 0
        var bracketStartPos: Int = -1
        var seenEquals: Bool = false
        var parenDepth: Int = 0
        while !self.atEnd() {
            var ch: String = self.peek()
            if ctx == wordCtxRegex {
                if ch == "\\" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "\n" {
                    self.advance()
                    self.advance()
                    continue
                }
            }
            if ctx != wordCtxNormal && self._isWordTerminator(ctx, ch, bracketDepth, parenDepth) {
                break
            }
            if ctx == wordCtxNormal && ch == "[" {
                if bracketDepth > 0 {
                    bracketDepth += 1
                    chars.append(self.advance())
                    continue
                }
                if (!chars.isEmpty) && atCommandStart && !seenEquals && _isArrayAssignmentPrefix(chars) {
                    var prevChar: String = chars[chars.count - 1]
                    if (prevChar.first?.isLetter ?? false || prevChar.first?.isNumber ?? false) || prevChar == "_" {
                        bracketStartPos = self.pos
                        bracketDepth += 1
                        chars.append(self.advance())
                        continue
                    }
                }
                if !(!chars.isEmpty) && !seenEquals && inArrayLiteral {
                    bracketStartPos = self.pos
                    bracketDepth += 1
                    chars.append(self.advance())
                    continue
                }
            }
            if ctx == wordCtxNormal && ch == "]" && bracketDepth > 0 {
                bracketDepth -= 1
                chars.append(self.advance())
                continue
            }
            if ctx == wordCtxNormal && ch == "=" && bracketDepth == 0 {
                seenEquals = true
            }
            if ctx == wordCtxRegex && ch == "(" {
                parenDepth += 1
                chars.append(self.advance())
                continue
            }
            if ctx == wordCtxRegex && ch == ")" {
                if parenDepth > 0 {
                    parenDepth -= 1
                    chars.append(self.advance())
                    continue
                }
                break
            }
            if ctx == wordCtxCond || ctx == wordCtxRegex && ch == "[" {
                var forRegex: Bool = ctx == wordCtxRegex
                if self._readBracketExpression(chars, parts, forRegex, parenDepth) {
                    continue
                }
                chars.append(self.advance())
                continue
            }
            var content: String = ""
            if ctx == wordCtxCond && ch == "(" {
                if self._extglob && (!chars.isEmpty) && _isExtglobPrefix(chars[chars.count - 1]) {
                    chars.append(self.advance())
                    content = try self._parseMatchedPair("(", ")", matchedpairflagsExtglob, false)
                    chars.append(content)
                    chars.append(")")
                    continue
                } else {
                    break
                }
            }
            if ctx == wordCtxRegex && _isWhitespace(ch) && parenDepth > 0 {
                chars.append(self.advance())
                continue
            }
            if ch == "'" {
                self.advance()
                var trackNewline: Bool = ctx == wordCtxNormal
                let _tuple8 = try self._readSingleQuote(start)
                content = _tuple8.0
                var sawNewline: Bool = _tuple8.1
                chars.append(content)
                if trackNewline && sawNewline && self._parser != nil {
                    self._parser!._sawNewlineInSingleQuote = true
                }
                continue
            }
            var cmdsubResult0: Node? = nil
            var cmdsubResult1: String = ""
            if ch == "\"" {
                self.advance()
                if ctx == wordCtxNormal {
                    chars.append("\"")
                    var inSingleInDquote: Bool = false
                    while !self.atEnd() && inSingleInDquote || self.peek() != "\"" {
                        var c: String = self.peek()
                        if inSingleInDquote {
                            chars.append(self.advance())
                            if c == "'" {
                                inSingleInDquote = false
                            }
                            continue
                        }
                        if c == "\\" && self.pos + 1 < self.length {
                            var nextC: String = String(_charAt(self.source, self.pos + 1))
                            if nextC == "\n" {
                                self.advance()
                                self.advance()
                            } else {
                                chars.append(self.advance())
                                chars.append(self.advance())
                            }
                        } else {
                            if c == "$" {
                                self._syncToParser()
                                if try !self._parser!._parseDollarExpansion(chars, parts, true) {
                                    self._syncFromParser()
                                    chars.append(self.advance())
                                } else {
                                    self._syncFromParser()
                                }
                            } else {
                                if c == "`" {
                                    self._syncToParser()
                                    let _tuple9 = try self._parser!._parseBacktickSubstitution()
                                    cmdsubResult0 = _tuple9.0
                                    cmdsubResult1 = _tuple9.1
                                    self._syncFromParser()
                                    if cmdsubResult0 != nil {
                                        parts.append(cmdsubResult0!)
                                        chars.append(cmdsubResult1)
                                    } else {
                                        chars.append(self.advance())
                                    }
                                } else {
                                    chars.append(self.advance())
                                }
                            }
                        }
                    }
                    if self.atEnd() {
                        throw ParseError(message: "Unterminated double quote", pos: start)
                    }
                    chars.append(self.advance())
                } else {
                    var handleLineContinuation: Bool = ctx == wordCtxCond
                    self._syncToParser()
                    try self._parser!._scanDoubleQuote(chars, parts, start, handleLineContinuation)
                    self._syncFromParser()
                }
                continue
            }
            if ch == "\\" && self.pos + 1 < self.length {
                var nextCh: String = String(_charAt(self.source, self.pos + 1))
                if ctx != wordCtxRegex && nextCh == "\n" {
                    self.advance()
                    self.advance()
                } else {
                    chars.append(self.advance())
                    chars.append(self.advance())
                }
                continue
            }
            if ctx != wordCtxRegex && ch == "$" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "'" {
                let _tuple10 = try self._readAnsiCQuote()
                var ansiResult0: Node? = _tuple10.0
                var ansiResult1: String = _tuple10.1
                if ansiResult0 != nil {
                    parts.append(ansiResult0!)
                    chars.append(ansiResult1)
                } else {
                    chars.append(self.advance())
                }
                continue
            }
            if ctx != wordCtxRegex && ch == "$" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "\"" {
                let _tuple11 = try self._readLocaleString()
                var localeResult0: Node? = _tuple11.0
                var localeResult1: String = _tuple11.1
                var localeResult2: [Node] = _tuple11.2
                if localeResult0 != nil {
                    parts.append(localeResult0!)
                    parts.append(contentsOf: localeResult2)
                    chars.append(localeResult1)
                } else {
                    chars.append(self.advance())
                }
                continue
            }
            if ch == "$" {
                self._syncToParser()
                if try !self._parser!._parseDollarExpansion(chars, parts, false) {
                    self._syncFromParser()
                    chars.append(self.advance())
                } else {
                    self._syncFromParser()
                    if self._extglob && ctx == wordCtxNormal && (!chars.isEmpty) && chars[chars.count - 1].count == 2 && String(_charAt(chars[chars.count - 1], 0)) == "$" && "?*@".contains(String(_charAt(chars[chars.count - 1], 1))) && !self.atEnd() && self.peek() == "(" {
                        chars.append(self.advance())
                        content = try self._parseMatchedPair("(", ")", matchedpairflagsExtglob, false)
                        chars.append(content)
                        chars.append(")")
                    }
                }
                continue
            }
            if ctx != wordCtxRegex && ch == "`" {
                self._syncToParser()
                let _tuple12 = try self._parser!._parseBacktickSubstitution()
                cmdsubResult0 = _tuple12.0
                cmdsubResult1 = _tuple12.1
                self._syncFromParser()
                if cmdsubResult0 != nil {
                    parts.append(cmdsubResult0!)
                    chars.append(cmdsubResult1)
                } else {
                    chars.append(self.advance())
                }
                continue
            }
            if ctx != wordCtxRegex && _isRedirectChar(ch) && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                self._syncToParser()
                let _tuple13 = try self._parser!._parseProcessSubstitution()
                var procsubResult0: Node? = _tuple13.0
                var procsubResult1: String = _tuple13.1
                self._syncFromParser()
                if procsubResult0 != nil {
                    parts.append(procsubResult0!)
                    chars.append(procsubResult1)
                } else {
                    if (!procsubResult1.isEmpty) {
                        chars.append(procsubResult1)
                    } else {
                        chars.append(self.advance())
                        if ctx == wordCtxNormal {
                            chars.append(self.advance())
                        }
                    }
                }
                continue
            }
            if ctx == wordCtxNormal && ch == "(" && (!chars.isEmpty) && bracketDepth == 0 {
                var isArrayAssign: Bool = false
                if chars.count >= 3 && chars[chars.count - 2] == "+" && chars[chars.count - 1] == "=" {
                    isArrayAssign = _isArrayAssignmentPrefix(Swift.Array(chars[..<(chars.count - 2)]))
                } else {
                    if chars[chars.count - 1] == "=" && chars.count >= 2 {
                        isArrayAssign = _isArrayAssignmentPrefix(Swift.Array(chars[..<(chars.count - 1)]))
                    }
                }
                if isArrayAssign && atCommandStart || inAssignBuiltin {
                    self._syncToParser()
                    let _tuple14 = try self._parser!._parseArrayLiteral()
                    var arrayResult0: Node? = _tuple14.0
                    var arrayResult1: String = _tuple14.1
                    self._syncFromParser()
                    if arrayResult0 != nil {
                        parts.append(arrayResult0!)
                        chars.append(arrayResult1)
                    } else {
                        break
                    }
                    continue
                }
            }
            if self._extglob && ctx == wordCtxNormal && _isExtglobPrefix(ch) && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                chars.append(self.advance())
                chars.append(self.advance())
                content = try self._parseMatchedPair("(", ")", matchedpairflagsExtglob, false)
                chars.append(content)
                chars.append(")")
                continue
            }
            if ctx == wordCtxNormal && (self._parserState & parserstateflagsPstEoftoken != 0) && self._eofToken != "" && ch == self._eofToken && bracketDepth == 0 {
                if !(!chars.isEmpty) {
                    chars.append(self.advance())
                }
                break
            }
            if ctx == wordCtxNormal && _isMetachar(ch) && bracketDepth == 0 {
                break
            }
            chars.append(self.advance())
        }
        if bracketDepth > 0 && bracketStartPos != -1 && self.atEnd() {
            throw MatchedPairError(message: "unexpected EOF looking for `]'", pos: bracketStartPos)
        }
        if !(!chars.isEmpty) {
            return nil
        }
        if (!parts.isEmpty) {
            return Word(value: chars.joined(separator: ""), parts: parts, kind: "word")
        }
        return Word(value: chars.joined(separator: ""), parts: nil, kind: "word")
    }

    func _readWord() throws -> Token? {
        var start: Int = self.pos
        if self.pos >= self.length {
            return nil
        }
        var c: String = self.peek()
        if c == "" {
            return nil
        }
        var isProcsub: Bool = c == "<" || c == ">" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "("
        var isRegexParen: Bool = self._wordContext == wordCtxRegex && c == "(" || c == ")"
        if self.isMetachar(c) && !isProcsub && !isRegexParen {
            return nil
        }
        var word: Word? = try self._readWordInternal(self._wordContext, self._atCommandStart, self._inArrayLiteral, self._inAssignBuiltin)
        if word == nil {
            return nil
        }
        return Token(type: tokentypeWord, value: word!.value, pos: start, parts: nil, word: word!)
    }

    func nextToken() throws -> Token {
        var tok: Token? = nil
        if self._tokenCache != nil {
            tok = self._tokenCache
            self._tokenCache = nil
            self._lastReadToken = tok!
            return tok!
        }
        self.skipBlanks()
        if self.atEnd() {
            tok = Token(type: tokentypeEof, value: "", pos: self.pos, parts: [], word: nil)
            self._lastReadToken = tok!
            return tok!
        }
        if self._eofToken != "" && self.peek() == self._eofToken && !(self._parserState & parserstateflagsPstCasepat != 0) && !(self._parserState & parserstateflagsPstEoftoken != 0) {
            tok = Token(type: tokentypeEof, value: "", pos: self.pos, parts: [], word: nil)
            self._lastReadToken = tok!
            return tok!
        }
        while self._skipComment() {
            self.skipBlanks()
            if self.atEnd() {
                tok = Token(type: tokentypeEof, value: "", pos: self.pos, parts: [], word: nil)
                self._lastReadToken = tok!
                return tok!
            }
            if self._eofToken != "" && self.peek() == self._eofToken && !(self._parserState & parserstateflagsPstCasepat != 0) && !(self._parserState & parserstateflagsPstEoftoken != 0) {
                tok = Token(type: tokentypeEof, value: "", pos: self.pos, parts: [], word: nil)
                self._lastReadToken = tok!
                return tok!
            }
        }
        tok = self._readOperator()
        if tok != nil {
            self._lastReadToken = tok!
            return tok!
        }
        tok = try self._readWord()
        if tok != nil {
            self._lastReadToken = tok!
            return tok!
        }
        tok = Token(type: tokentypeEof, value: "", pos: self.pos, parts: [], word: nil)
        self._lastReadToken = tok!
        return tok!
    }

    func peekToken() throws -> Token {
        if self._tokenCache == nil {
            var savedLast: Token? = self._lastReadToken
            self._tokenCache = try self.nextToken()
            self._lastReadToken = savedLast
        }
        return self._tokenCache
    }

    func _readAnsiCQuote() throws -> (Node?, String) {
        if self.atEnd() || self.peek() != "$" {
            return (nil, "")
        }
        if self.pos + 1 >= self.length || String(_charAt(self.source, self.pos + 1)) != "'" {
            return (nil, "")
        }
        var start: Int = self.pos
        self.advance()
        self.advance()
        var contentChars: [String] = []
        var foundClose: Bool = false
        while !self.atEnd() {
            var ch: String = self.peek()
            if ch == "'" {
                self.advance()
                foundClose = true
                break
            } else {
                if ch == "\\" {
                    contentChars.append(self.advance())
                    if !self.atEnd() {
                        contentChars.append(self.advance())
                    }
                } else {
                    contentChars.append(self.advance())
                }
            }
        }
        if !foundClose {
            throw MatchedPairError(message: "unexpected EOF while looking for matching `''", pos: start)
        }
        var text: String = _substring(self.source, start, self.pos)
        var content: String = contentChars.joined(separator: "")
        var node: AnsiCQuote = AnsiCQuote(content: content, kind: "ansi-c")
        return (node, text)
    }

    func _syncToParser() {
        if self._parser != nil {
            self._parser!.pos = self.pos
        }
    }

    func _syncFromParser() {
        if self._parser != nil {
            self.pos = self._parser!.pos
        }
    }

    func _readLocaleString() throws -> (Node?, String, [Node]) {
        if self.atEnd() || self.peek() != "$" {
            return (nil, "", [])
        }
        if self.pos + 1 >= self.length || String(_charAt(self.source, self.pos + 1)) != "\"" {
            return (nil, "", [])
        }
        var start: Int = self.pos
        self.advance()
        self.advance()
        var contentChars: [String] = []
        var innerParts: [Node] = []
        var foundClose: Bool = false
        while !self.atEnd() {
            var ch: String = self.peek()
            if ch == "\"" {
                self.advance()
                foundClose = true
                break
            } else {
                if ch == "\\" && self.pos + 1 < self.length {
                    var nextCh: String = String(_charAt(self.source, self.pos + 1))
                    if nextCh == "\n" {
                        self.advance()
                        self.advance()
                    } else {
                        contentChars.append(self.advance())
                        contentChars.append(self.advance())
                    }
                } else {
                    var cmdsubNode: Node? = nil
                    var cmdsubText: String = ""
                    if ch == "$" && self.pos + 2 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" && String(_charAt(self.source, self.pos + 2)) == "(" {
                        self._syncToParser()
                        let _tuple15 = try self._parser!._parseArithmeticExpansion()
                        var arithNode: Node? = _tuple15.0
                        var arithText: String = _tuple15.1
                        self._syncFromParser()
                        if arithNode != nil {
                            innerParts.append(arithNode!)
                            contentChars.append(arithText)
                        } else {
                            self._syncToParser()
                            let _tuple16 = try self._parser!._parseCommandSubstitution()
                            cmdsubNode = _tuple16.0
                            cmdsubText = _tuple16.1
                            self._syncFromParser()
                            if cmdsubNode != nil {
                                innerParts.append(cmdsubNode!)
                                contentChars.append(cmdsubText)
                            } else {
                                contentChars.append(self.advance())
                            }
                        }
                    } else {
                        if _isExpansionStart(self.source, self.pos, "$(") {
                            self._syncToParser()
                            let _tuple17 = try self._parser!._parseCommandSubstitution()
                            cmdsubNode = _tuple17.0
                            cmdsubText = _tuple17.1
                            self._syncFromParser()
                            if cmdsubNode != nil {
                                innerParts.append(cmdsubNode!)
                                contentChars.append(cmdsubText)
                            } else {
                                contentChars.append(self.advance())
                            }
                        } else {
                            if ch == "$" {
                                self._syncToParser()
                                let _tuple18 = try self._parser!._parseParamExpansion(false)
                                var paramNode: Node? = _tuple18.0
                                var paramText: String = _tuple18.1
                                self._syncFromParser()
                                if paramNode != nil {
                                    innerParts.append(paramNode!)
                                    contentChars.append(paramText)
                                } else {
                                    contentChars.append(self.advance())
                                }
                            } else {
                                if ch == "`" {
                                    self._syncToParser()
                                    let _tuple19 = try self._parser!._parseBacktickSubstitution()
                                    cmdsubNode = _tuple19.0
                                    cmdsubText = _tuple19.1
                                    self._syncFromParser()
                                    if cmdsubNode != nil {
                                        innerParts.append(cmdsubNode!)
                                        contentChars.append(cmdsubText)
                                    } else {
                                        contentChars.append(self.advance())
                                    }
                                } else {
                                    contentChars.append(self.advance())
                                }
                            }
                        }
                    }
                }
            }
        }
        if !foundClose {
            self.pos = start
            return (nil, "", [])
        }
        var content: String = contentChars.joined(separator: "")
        var text: String = "$\"" + content + "\""
        return (LocaleString(content: content, kind: "locale"), text, innerParts)
    }

    func _updateDolbraceForOp(_ op: String, _ hasParam: Bool) {
        if self._dolbraceState == dolbracestateNone {
            return
        }
        if op == "" || op.count == 0 {
            return
        }
        var firstChar: String = String(_charAt(op, 0))
        if self._dolbraceState == dolbracestateParam && hasParam {
            if "%#^,".contains(firstChar) {
                self._dolbraceState = dolbracestateQuote
                return
            }
            if firstChar == "/" {
                self._dolbraceState = dolbracestateQuote2
                return
            }
        }
        if self._dolbraceState == dolbracestateParam {
            if "#%^,~:-=?+/".contains(firstChar) {
                self._dolbraceState = dolbracestateOp
            }
        }
    }

    func _consumeParamOperator() -> String {
        if self.atEnd() {
            return ""
        }
        var ch: String = self.peek()
        var nextCh: String = ""
        if ch == ":" {
            self.advance()
            if self.atEnd() {
                return ":"
            }
            nextCh = self.peek()
            if _isSimpleParamOp(nextCh) {
                self.advance()
                return ":" + nextCh
            }
            return ":"
        }
        if _isSimpleParamOp(ch) {
            self.advance()
            return ch
        }
        if ch == "#" {
            self.advance()
            if !self.atEnd() && self.peek() == "#" {
                self.advance()
                return "##"
            }
            return "#"
        }
        if ch == "%" {
            self.advance()
            if !self.atEnd() && self.peek() == "%" {
                self.advance()
                return "%%"
            }
            return "%"
        }
        if ch == "/" {
            self.advance()
            if !self.atEnd() {
                nextCh = self.peek()
                if nextCh == "/" {
                    self.advance()
                    return "//"
                } else {
                    if nextCh == "#" {
                        self.advance()
                        return "/#"
                    } else {
                        if nextCh == "%" {
                            self.advance()
                            return "/%"
                        }
                    }
                }
            }
            return "/"
        }
        if ch == "^" {
            self.advance()
            if !self.atEnd() && self.peek() == "^" {
                self.advance()
                return "^^"
            }
            return "^"
        }
        if ch == "," {
            self.advance()
            if !self.atEnd() && self.peek() == "," {
                self.advance()
                return ",,"
            }
            return ","
        }
        if ch == "@" {
            self.advance()
            return "@"
        }
        return ""
    }

    func _paramSubscriptHasClose(_ startPos: Int) -> Bool {
        var depth: Int = 1
        var i: Int = startPos + 1
        var quote: QuoteState = newQuoteState()
        while i < self.length {
            var c: String = String(_charAt(self.source, i))
            if quote.single {
                if c == "'" {
                    quote.single = false
                }
                i += 1
                continue
            }
            if quote.double {
                if c == "\\" && i + 1 < self.length {
                    i += 2
                    continue
                }
                if c == "\"" {
                    quote.double = false
                }
                i += 1
                continue
            }
            if c == "'" {
                quote.single = true
                i += 1
                continue
            }
            if c == "\"" {
                quote.double = true
                i += 1
                continue
            }
            if c == "\\" {
                i += 2
                continue
            }
            if c == "}" {
                return false
            }
            if c == "[" {
                depth += 1
            } else {
                if c == "]" {
                    depth -= 1
                    if depth == 0 {
                        return true
                    }
                }
            }
            i += 1
        }
        return false
    }

    func _consumeParamName() throws -> String {
        if self.atEnd() {
            return ""
        }
        var ch: String = self.peek()
        if _isSpecialParam(ch) {
            if ch == "$" && self.pos + 1 < self.length && "{'\"".contains(String(_charAt(self.source, self.pos + 1))) {
                return ""
            }
            self.advance()
            return ch
        }
        if (ch.first?.isNumber ?? false) {
            var nameChars: [String] = []
            while !self.atEnd() && (self.peek().first?.isNumber ?? false) {
                nameChars.append(self.advance())
            }
            return nameChars.joined(separator: "")
        }
        if (ch.first?.isLetter ?? false) || ch == "_" {
            var nameChars: [String] = []
            while !self.atEnd() {
                var c: String = self.peek()
                if (c.first?.isLetter ?? false || c.first?.isNumber ?? false) || c == "_" {
                    nameChars.append(self.advance())
                } else {
                    if c == "[" {
                        if !self._paramSubscriptHasClose(self.pos) {
                            break
                        }
                        nameChars.append(self.advance())
                        var content: String = try self._parseMatchedPair("[", "]", matchedpairflagsArraysub, false)
                        nameChars.append(content)
                        nameChars.append("]")
                        break
                    } else {
                        break
                    }
                }
            }
            if (!nameChars.isEmpty) {
                return nameChars.joined(separator: "")
            } else {
                return ""
            }
        }
        return ""
    }

    func _readParamExpansion(_ inDquote: Bool) throws -> (Node?, String) {
        if self.atEnd() || self.peek() != "$" {
            return (nil, "")
        }
        var start: Int = self.pos
        self.advance()
        if self.atEnd() {
            self.pos = start
            return (nil, "")
        }
        var ch: String = self.peek()
        if ch == "{" {
            self.advance()
            return try self._readBracedParam(start, inDquote)
        }
        var text: String = ""
        if _isSpecialParamUnbraced(ch) || _isDigit(ch) || ch == "#" {
            self.advance()
            text = _substring(self.source, start, self.pos)
            return (ParamExpansion(param: ch, op: "", arg: "", kind: "param"), text)
        }
        if (ch.first?.isLetter ?? false) || ch == "_" {
            var nameStart: Int = self.pos
            while !self.atEnd() {
                var c: String = self.peek()
                if (c.first?.isLetter ?? false || c.first?.isNumber ?? false) || c == "_" {
                    self.advance()
                } else {
                    break
                }
            }
            var name: String = _substring(self.source, nameStart, self.pos)
            text = _substring(self.source, start, self.pos)
            return (ParamExpansion(param: name, op: "", arg: "", kind: "param"), text)
        }
        self.pos = start
        return (nil, "")
    }

    func _readBracedParam(_ start: Int, _ inDquote: Bool) throws -> (Node?, String) {
        if self.atEnd() {
            throw MatchedPairError(message: "unexpected EOF looking for `}'", pos: start)
        }
        var savedDolbrace: Int = self._dolbraceState
        self._dolbraceState = dolbracestateParam
        var ch: String = self.peek()
        if _isFunsubChar(ch) {
            self._dolbraceState = savedDolbrace
            return try self._readFunsub(start)
        }
        var param: String = ""
        var text: String = ""
        if ch == "#" {
            self.advance()
            param = try self._consumeParamName()
            if (!param.isEmpty) && !self.atEnd() && self.peek() == "}" {
                self.advance()
                text = _substring(self.source, start, self.pos)
                self._dolbraceState = savedDolbrace
                return (ParamLength(param: param, kind: "param-len"), text)
            }
            self.pos = start + 2
        }
        var op: String = ""
        var arg: String = ""
        if ch == "!" {
            self.advance()
            while !self.atEnd() && _isWhitespaceNoNewline(self.peek()) {
                self.advance()
            }
            param = try self._consumeParamName()
            if (!param.isEmpty) {
                while !self.atEnd() && _isWhitespaceNoNewline(self.peek()) {
                    self.advance()
                }
                if !self.atEnd() && self.peek() == "}" {
                    self.advance()
                    text = _substring(self.source, start, self.pos)
                    self._dolbraceState = savedDolbrace
                    return (ParamIndirect(param: param, op: "", arg: "", kind: "param-indirect"), text)
                }
                if !self.atEnd() && _isAtOrStar(self.peek()) {
                    var suffix: String = self.advance()
                    var trailing: String = try self._parseMatchedPair("{", "}", matchedpairflagsDolbrace, false)
                    text = _substring(self.source, start, self.pos)
                    self._dolbraceState = savedDolbrace
                    return (ParamIndirect(param: param + suffix + trailing, op: "", arg: "", kind: "param-indirect"), text)
                }
                op = self._consumeParamOperator()
                if op == "" && !self.atEnd() && !"}\"'`".contains(self.peek()) {
                    op = self.advance()
                }
                if op != "" && !"\"'`".contains(op) {
                    arg = try self._parseMatchedPair("{", "}", matchedpairflagsDolbrace, false)
                    text = _substring(self.source, start, self.pos)
                    self._dolbraceState = savedDolbrace
                    return (ParamIndirect(param: param, op: op, arg: arg, kind: "param-indirect"), text)
                }
                if self.atEnd() {
                    self._dolbraceState = savedDolbrace
                    throw MatchedPairError(message: "unexpected EOF looking for `}'", pos: start)
                }
                self.pos = start + 2
            } else {
                self.pos = start + 2
            }
        }
        param = try self._consumeParamName()
        if !(!param.isEmpty) {
            if !self.atEnd() && "-=+?".contains(self.peek()) || self.peek() == ":" && self.pos + 1 < self.length && _isSimpleParamOp(String(_charAt(self.source, self.pos + 1))) {
                param = ""
            } else {
                var content: String = try self._parseMatchedPair("{", "}", matchedpairflagsDolbrace, false)
                text = "${" + content + "}"
                self._dolbraceState = savedDolbrace
                return (ParamExpansion(param: content, op: "", arg: "", kind: "param"), text)
            }
        }
        if self.atEnd() {
            self._dolbraceState = savedDolbrace
            throw MatchedPairError(message: "unexpected EOF looking for `}'", pos: start)
        }
        if self.peek() == "}" {
            self.advance()
            text = _substring(self.source, start, self.pos)
            self._dolbraceState = savedDolbrace
            return (ParamExpansion(param: param, op: "", arg: "", kind: "param"), text)
        }
        op = self._consumeParamOperator()
        if op == "" {
            if !self.atEnd() && self.peek() == "$" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "\"" || String(_charAt(self.source, self.pos + 1)) == "'" {
                var dollarCount: Int = 1 + _countConsecutiveDollarsBefore(self.source, self.pos)
                if dollarCount % 2 == 1 {
                    op = ""
                } else {
                    op = self.advance()
                }
            } else {
                if !self.atEnd() && self.peek() == "`" {
                    var backtickPos: Int = self.pos
                    self.advance()
                    while !self.atEnd() && self.peek() != "`" {
                        var bc: String = self.peek()
                        if bc == "\\" && self.pos + 1 < self.length {
                            var nextC: String = String(_charAt(self.source, self.pos + 1))
                            if _isEscapeCharInBacktick(nextC) {
                                self.advance()
                            }
                        }
                        self.advance()
                    }
                    if self.atEnd() {
                        self._dolbraceState = savedDolbrace
                        throw ParseError(message: "Unterminated backtick", pos: backtickPos)
                    }
                    self.advance()
                    op = "`"
                } else {
                    if !self.atEnd() && self.peek() == "$" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "{" {
                        op = ""
                    } else {
                        if !self.atEnd() && self.peek() == "'" || self.peek() == "\"" {
                            op = ""
                        } else {
                            if !self.atEnd() && self.peek() == "\\" {
                                op = self.advance()
                                if !self.atEnd() {
                                    op += self.advance()
                                }
                            } else {
                                op = self.advance()
                            }
                        }
                    }
                }
            }
        }
        self._updateDolbraceForOp(op, param.count > 0)
        do {
            var flags: Int = (inDquote ? matchedpairflagsDquote : matchedpairflagsNone)
            var paramEndsWithDollar: Bool = param != "" && param.hasSuffix("$")
            arg = try self._collectParamArgument(flags, paramEndsWithDollar)
        } catch is MatchedPairError {
            self._dolbraceState = savedDolbrace
            throw e
        }
        if op == "<" || op == ">" && arg.hasPrefix("(") && arg.hasSuffix(")") {
            var inner: String = String(arg[arg.index(arg.startIndex, offsetBy: 1)..<arg.index(arg.startIndex, offsetBy: min(arg.count - 1, arg.count))])
            do {
                var subParser: Parser = newParser(inner, true, self._parser!._extglob)
                var parsed: Node? = try subParser.parseList(true)
                if parsed != nil && subParser.atEnd() {
                    var formatted: String = _formatCmdsubNode(parsed!, 0, true, false, true)
                    arg = "(" + formatted + ")"
                }
            } catch {
            }
        }
        text = "${" + param + op + arg + "}"
        self._dolbraceState = savedDolbrace
        return (ParamExpansion(param: param, op: op, arg: arg, kind: "param"), text)
    }

    func _readFunsub(_ start: Int) throws -> (Node?, String) {
        return try self._parser!._parseFunsub(start)
    }
}

class Word: Node {
    var value: String = ""
    var parts: [Node] = []
    var kind: String = ""

    init(value: String = "", parts: [Node] = [], kind: String = "") {
        self.value = value
        self.parts = parts
        self.kind = kind
    }

    func toSexp() -> String {
        var value: String = self.value
        value = self._expandAllAnsiCQuotes(value)
        value = self._stripLocaleStringDollars(value)
        value = self._normalizeArrayWhitespace(value)
        value = self._formatCommandSubstitutions(value, false)
        value = self._normalizeParamExpansionNewlines(value)
        value = self._stripArithLineContinuations(value)
        value = self._doubleCtlescSmart(value)
        value = value.replacingOccurrences(of: "\u{007f}", with: "\u{0001}\u{007f}")
        value = value.replacingOccurrences(of: "\\", with: "\\\\")
        if value.hasSuffix("\\\\") && !value.hasSuffix("\\\\\\\\") {
            value = value + "\\\\"
        }
        var escaped: String = value.replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n").replacingOccurrences(of: "\t", with: "\\t")
        return "(word \"" + escaped + "\")"
    }

    func _appendWithCtlesc(_ result: [UInt8], _ byteVal: Int) {
        result.append(UInt8(byteVal))
    }

    func _doubleCtlescSmart(_ value: String) -> String {
        var result: [String] = []
        var quote: QuoteState = newQuoteState()
        for _c20 in value {
            let c = String(_c20)
            if c == "'" && !quote.double {
                quote.single = !quote.single
            } else {
                if c == "\"" && !quote.single {
                    quote.double = !quote.double
                }
            }
            result.append(c)
            if c == "\u{0001}" {
                if quote.double {
                    var bsCount: Int = 0
                    var j: Int = result.count - 2
                    while j > -1 {
                        if result[j] == "\\" {
                            bsCount += 1
                        } else {
                            break
                        }
                        j += -1
                    }
                    if bsCount % 2 == 0 {
                        result.append("\u{0001}")
                    }
                } else {
                    result.append("\u{0001}")
                }
            }
        }
        return result.joined(separator: "")
    }

    func _normalizeParamExpansionNewlines(_ value: String) -> String {
        var result: [String] = []
        var i: Int = 0
        var quote: QuoteState = newQuoteState()
        while i < value.count {
            var c: String = String(_charAt(value, i))
            if c == "'" && !quote.double {
                quote.single = !quote.single
                result.append(c)
                i += 1
            } else {
                if c == "\"" && !quote.single {
                    quote.double = !quote.double
                    result.append(c)
                    i += 1
                } else {
                    if _isExpansionStart(value, i, "${") && !quote.single {
                        result.append("$")
                        result.append("{")
                        i += 2
                        var hadLeadingNewline: Bool = i < value.count && String(_charAt(value, i)) == "\n"
                        if hadLeadingNewline {
                            result.append(" ")
                            i += 1
                        }
                        var depth: Int = 1
                        while i < value.count && depth > 0 {
                            var ch: String = String(_charAt(value, i))
                            if ch == "\\" && i + 1 < value.count && !quote.single {
                                if String(_charAt(value, i + 1)) == "\n" {
                                    i += 2
                                    continue
                                }
                                result.append(ch)
                                result.append(String(_charAt(value, i + 1)))
                                i += 2
                                continue
                            }
                            if ch == "'" && !quote.double {
                                quote.single = !quote.single
                            } else {
                                if ch == "\"" && !quote.single {
                                    quote.double = !quote.double
                                } else {
                                    if !quote.inQuotes() {
                                        if ch == "{" {
                                            depth += 1
                                        } else {
                                            if ch == "}" {
                                                depth -= 1
                                                if depth == 0 {
                                                    if hadLeadingNewline {
                                                        result.append(" ")
                                                    }
                                                    result.append(ch)
                                                    i += 1
                                                    break
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            result.append(ch)
                            i += 1
                        }
                    } else {
                        result.append(c)
                        i += 1
                    }
                }
            }
        }
        return result.joined(separator: "")
    }

    func _shSingleQuote(_ s: String) -> String {
        if !(!s.isEmpty) {
            return "''"
        }
        if s == "'" {
            return "\\'"
        }
        var result: [String] = ["'"]
        for _c21 in s {
            let c = String(_c21)
            if c == "'" {
                result.append("'\\''")
            } else {
                result.append(c)
            }
        }
        result.append("'")
        return result.joined(separator: "")
    }

    func _ansiCToBytes(_ inner: String) -> [UInt8] {
        var result: [UInt8] = [UInt8]()
        var i: Int = 0
        while i < inner.count {
            if String(_charAt(inner, i)) == "\\" && i + 1 < inner.count {
                var c: String = String(_charAt(inner, i + 1))
                var simple: Int = _getAnsiEscape(c)
                if simple >= 0 {
                    result.append(UInt8(simple))
                    i += 2
                } else {
                    if c == "'" {
                        result.append(UInt8(39))
                        i += 2
                    } else {
                        var j: Int = 0
                        var byteVal: Int = 0
                        if c == "x" {
                            if i + 2 < inner.count && String(_charAt(inner, i + 2)) == "{" {
                                j = i + 3
                                while j < inner.count && _isHexDigit(String(_charAt(inner, j))) {
                                    j += 1
                                }
                                var hexStr: String = _substring(inner, i + 3, j)
                                if j < inner.count && String(_charAt(inner, j)) == "}" {
                                    j += 1
                                }
                                if !(!hexStr.isEmpty) {
                                    return result
                                }
                                byteVal = Int(hexStr, radix: 16)! & 255
                                if byteVal == 0 {
                                    return result
                                }
                                self._appendWithCtlesc(result, byteVal)
                                i = j
                            } else {
                                j = i + 2
                                while j < inner.count && j < i + 4 && _isHexDigit(String(_charAt(inner, j))) {
                                    j += 1
                                }
                                if j > i + 2 {
                                    byteVal = Int(_substring(inner, i + 2, j), radix: 16)!
                                    if byteVal == 0 {
                                        return result
                                    }
                                    self._appendWithCtlesc(result, byteVal)
                                    i = j
                                } else {
                                    result.append(UInt8(_charAt(String(_charAt(inner, i)), 0)))
                                    i += 1
                                }
                            }
                        } else {
                            var codepoint: Int = 0
                            if c == "u" {
                                j = i + 2
                                while j < inner.count && j < i + 6 && _isHexDigit(String(_charAt(inner, j))) {
                                    j += 1
                                }
                                if j > i + 2 {
                                    codepoint = Int(_substring(inner, i + 2, j), radix: 16)!
                                    if codepoint == 0 {
                                        return result
                                    }
                                    result.append(contentsOf: Swift.Array(String(Character(UnicodeScalar(codepoint)!)).utf8))
                                    i = j
                                } else {
                                    result.append(UInt8(_charAt(String(_charAt(inner, i)), 0)))
                                    i += 1
                                }
                            } else {
                                if c == "U" {
                                    j = i + 2
                                    while j < inner.count && j < i + 10 && _isHexDigit(String(_charAt(inner, j))) {
                                        j += 1
                                    }
                                    if j > i + 2 {
                                        codepoint = Int(_substring(inner, i + 2, j), radix: 16)!
                                        if codepoint == 0 {
                                            return result
                                        }
                                        result.append(contentsOf: Swift.Array(String(Character(UnicodeScalar(codepoint)!)).utf8))
                                        i = j
                                    } else {
                                        result.append(UInt8(_charAt(String(_charAt(inner, i)), 0)))
                                        i += 1
                                    }
                                } else {
                                    if c == "c" {
                                        if i + 3 <= inner.count {
                                            var ctrlChar: String = String(_charAt(inner, i + 2))
                                            var skipExtra: Int = 0
                                            if ctrlChar == "\\" && i + 4 <= inner.count && String(_charAt(inner, i + 3)) == "\\" {
                                                skipExtra = 1
                                            }
                                            var ctrlVal: Int = _charAt(ctrlChar, 0) & 31
                                            if ctrlVal == 0 {
                                                return result
                                            }
                                            self._appendWithCtlesc(result, ctrlVal)
                                            i += 3 + skipExtra
                                        } else {
                                            result.append(UInt8(_charAt(String(_charAt(inner, i)), 0)))
                                            i += 1
                                        }
                                    } else {
                                        if c == "0" {
                                            j = i + 2
                                            while j < inner.count && j < i + 4 && _isOctalDigit(String(_charAt(inner, j))) {
                                                j += 1
                                            }
                                            if j > i + 2 {
                                                byteVal = Int(_substring(inner, i + 1, j), radix: 8)! & 255
                                                if byteVal == 0 {
                                                    return result
                                                }
                                                self._appendWithCtlesc(result, byteVal)
                                                i = j
                                            } else {
                                                return result
                                            }
                                        } else {
                                            if c >= "1" && c <= "7" {
                                                j = i + 1
                                                while j < inner.count && j < i + 4 && _isOctalDigit(String(_charAt(inner, j))) {
                                                    j += 1
                                                }
                                                byteVal = Int(_substring(inner, i + 1, j), radix: 8)! & 255
                                                if byteVal == 0 {
                                                    return result
                                                }
                                                self._appendWithCtlesc(result, byteVal)
                                                i = j
                                            } else {
                                                result.append(UInt8(92))
                                                result.append(UInt8(_charAt(c, 0)))
                                                i += 2
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                result.append(contentsOf: Swift.Array(String(_charAt(inner, i)).utf8))
                i += 1
            }
        }
        return result
    }

    func _expandAnsiCEscapes(_ value: String) -> String {
        if !(value.hasPrefix("'") && value.hasSuffix("'")) {
            return value
        }
        var inner: String = _substring(value, 1, value.count - 1)
        var literalBytes: [UInt8] = self._ansiCToBytes(inner)
        var literalStr: String = String(bytes: literalBytes, encoding: .utf8)!
        return self._shSingleQuote(literalStr)
    }

    func _expandAllAnsiCQuotes(_ value: String) -> String {
        var result: [String] = []
        var i: Int = 0
        var quote: QuoteState = newQuoteState()
        var inBacktick: Bool = false
        var braceDepth: Int = 0
        while i < value.count {
            var ch: String = String(_charAt(value, i))
            if ch == "`" && !quote.single {
                inBacktick = !inBacktick
                result.append(ch)
                i += 1
                continue
            }
            if inBacktick {
                if ch == "\\" && i + 1 < value.count {
                    result.append(ch)
                    result.append(String(_charAt(value, i + 1)))
                    i += 2
                } else {
                    result.append(ch)
                    i += 1
                }
                continue
            }
            if !quote.single {
                if _isExpansionStart(value, i, "${") {
                    braceDepth += 1
                    quote.push()
                    result.append("${")
                    i += 2
                    continue
                } else {
                    if ch == "}" && braceDepth > 0 && !quote.double {
                        braceDepth -= 1
                        result.append(ch)
                        quote.pop()
                        i += 1
                        continue
                    }
                }
            }
            var effectiveInDquote: Bool = quote.double
            if ch == "'" && !effectiveInDquote {
                var isAnsiC: Bool = !quote.single && i > 0 && String(_charAt(value, i - 1)) == "$" && _countConsecutiveDollarsBefore(value, i - 1) % 2 == 0
                if !isAnsiC {
                    quote.single = !quote.single
                }
                result.append(ch)
                i += 1
            } else {
                if ch == "\"" && !quote.single {
                    quote.double = !quote.double
                    result.append(ch)
                    i += 1
                } else {
                    if ch == "\\" && i + 1 < value.count && !quote.single {
                        result.append(ch)
                        result.append(String(_charAt(value, i + 1)))
                        i += 2
                    } else {
                        if _startsWithAt(value, i, "$'") && !quote.single && !effectiveInDquote && _countConsecutiveDollarsBefore(value, i) % 2 == 0 {
                            var j: Int = i + 2
                            while j < value.count {
                                if String(_charAt(value, j)) == "\\" && j + 1 < value.count {
                                    j += 2
                                } else {
                                    if String(_charAt(value, j)) == "'" {
                                        j += 1
                                        break
                                    } else {
                                        j += 1
                                    }
                                }
                            }
                            var ansiStr: String = _substring(value, i, j)
                            var expanded: String = self._expandAnsiCEscapes(_substring(ansiStr, 1, ansiStr.count))
                            var outerInDquote: Bool = quote.outerDouble()
                            if braceDepth > 0 && outerInDquote && expanded.hasPrefix("'") && expanded.hasSuffix("'") {
                                var inner: String = _substring(expanded, 1, expanded.count - 1)
                                if (inner.range(of: "\u{0001}").map { inner.distance(from: inner.startIndex, to: $0.lowerBound) } ?? -1) == -1 {
                                    var resultStr: String = result.joined(separator: "")
                                    var inPattern: Bool = false
                                    var lastBraceIdx: Int = (resultStr.range(of: "${", options: .backwards).map { resultStr.distance(from: resultStr.startIndex, to: $0.lowerBound) } ?? -1)
                                    if lastBraceIdx >= 0 {
                                        var afterBrace: String = String(resultStr.dropFirst(lastBraceIdx + 2))
                                        var varNameLen: Int = 0
                                        if (!afterBrace.isEmpty) {
                                            if "@*#?-$!0123456789_".contains(String(_charAt(afterBrace, 0))) {
                                                varNameLen = 1
                                            } else {
                                                if (String(_charAt(afterBrace, 0)).first?.isLetter ?? false) || String(_charAt(afterBrace, 0)) == "_" {
                                                    while varNameLen < afterBrace.count {
                                                        var c: String = String(_charAt(afterBrace, varNameLen))
                                                        if !((c.first?.isLetter ?? false || c.first?.isNumber ?? false) || c == "_") {
                                                            break
                                                        }
                                                        varNameLen += 1
                                                    }
                                                }
                                            }
                                        }
                                        if varNameLen > 0 && varNameLen < afterBrace.count && !"#?-".contains(String(_charAt(afterBrace, 0))) {
                                            var opStart: String = String(afterBrace.dropFirst(varNameLen))
                                            if opStart.hasPrefix("@") && opStart.count > 1 {
                                                opStart = String(opStart.dropFirst(1))
                                            }
                                            for op in ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"] {
                                                if opStart.hasPrefix(op) {
                                                    inPattern = true
                                                    break
                                                }
                                            }
                                            if !inPattern && (!opStart.isEmpty) && !"%#/^,~:+-=?".contains(String(_charAt(opStart, 0))) {
                                                for op in ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"] {
                                                    if opStart.contains(op) {
                                                        inPattern = true
                                                        break
                                                    }
                                                }
                                            }
                                        } else {
                                            if varNameLen == 0 && afterBrace.count > 1 {
                                                var firstChar: String = String(_charAt(afterBrace, 0))
                                                if !"%#/^,".contains(firstChar) {
                                                    var rest: String = String(afterBrace.dropFirst(1))
                                                    for op in ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"] {
                                                        if rest.contains(op) {
                                                            inPattern = true
                                                            break
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    if !inPattern {
                                        expanded = inner
                                    }
                                }
                            }
                            result.append(expanded)
                            i = j
                        } else {
                            result.append(ch)
                            i += 1
                        }
                    }
                }
            }
        }
        return result.joined(separator: "")
    }

    func _stripLocaleStringDollars(_ value: String) -> String {
        var result: [String] = []
        var i: Int = 0
        var braceDepth: Int = 0
        var bracketDepth: Int = 0
        var quote: QuoteState = newQuoteState()
        var braceQuote: QuoteState = newQuoteState()
        var bracketInDoubleQuote: Bool = false
        while i < value.count {
            var ch: String = String(_charAt(value, i))
            if ch == "\\" && i + 1 < value.count && !quote.single && !braceQuote.single {
                result.append(ch)
                result.append(String(_charAt(value, i + 1)))
                i += 2
            } else {
                if _startsWithAt(value, i, "${") && !quote.single && !braceQuote.single && i == 0 || String(_charAt(value, i - 1)) != "$" {
                    braceDepth += 1
                    braceQuote.double = false
                    braceQuote.single = false
                    result.append("$")
                    result.append("{")
                    i += 2
                } else {
                    if ch == "}" && braceDepth > 0 && !quote.single && !braceQuote.double && !braceQuote.single {
                        braceDepth -= 1
                        result.append(ch)
                        i += 1
                    } else {
                        if ch == "[" && braceDepth > 0 && !quote.single && !braceQuote.double {
                            bracketDepth += 1
                            bracketInDoubleQuote = false
                            result.append(ch)
                            i += 1
                        } else {
                            if ch == "]" && bracketDepth > 0 && !quote.single && !bracketInDoubleQuote {
                                bracketDepth -= 1
                                result.append(ch)
                                i += 1
                            } else {
                                if ch == "'" && !quote.double && braceDepth == 0 {
                                    quote.single = !quote.single
                                    result.append(ch)
                                    i += 1
                                } else {
                                    if ch == "\"" && !quote.single && braceDepth == 0 {
                                        quote.double = !quote.double
                                        result.append(ch)
                                        i += 1
                                    } else {
                                        if ch == "\"" && !quote.single && bracketDepth > 0 {
                                            bracketInDoubleQuote = !bracketInDoubleQuote
                                            result.append(ch)
                                            i += 1
                                        } else {
                                            if ch == "\"" && !quote.single && !braceQuote.single && braceDepth > 0 {
                                                braceQuote.double = !braceQuote.double
                                                result.append(ch)
                                                i += 1
                                            } else {
                                                if ch == "'" && !quote.double && !braceQuote.double && braceDepth > 0 {
                                                    braceQuote.single = !braceQuote.single
                                                    result.append(ch)
                                                    i += 1
                                                } else {
                                                    if _startsWithAt(value, i, "$\"") && !quote.single && !braceQuote.single && braceDepth > 0 || bracketDepth > 0 || !quote.double && !braceQuote.double && !bracketInDoubleQuote {
                                                        var dollarCount: Int = 1 + _countConsecutiveDollarsBefore(value, i)
                                                        if dollarCount % 2 == 1 {
                                                            result.append("\"")
                                                            if bracketDepth > 0 {
                                                                bracketInDoubleQuote = true
                                                            } else {
                                                                if braceDepth > 0 {
                                                                    braceQuote.double = true
                                                                } else {
                                                                    quote.double = true
                                                                }
                                                            }
                                                            i += 2
                                                        } else {
                                                            result.append(ch)
                                                            i += 1
                                                        }
                                                    } else {
                                                        result.append(ch)
                                                        i += 1
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
        return result.joined(separator: "")
    }

    func _normalizeArrayWhitespace(_ value: String) -> String {
        var i: Int = 0
        if !(i < value.count && (String(_charAt(value, i)).first?.isLetter ?? false) || String(_charAt(value, i)) == "_") {
            return value
        }
        i += 1
        while i < value.count && (String(_charAt(value, i)).first?.isLetter ?? false || String(_charAt(value, i)).first?.isNumber ?? false) || String(_charAt(value, i)) == "_" {
            i += 1
        }
        while i < value.count && String(_charAt(value, i)) == "[" {
            var depth: Int = 1
            i += 1
            while i < value.count && depth > 0 {
                if String(_charAt(value, i)) == "[" {
                    depth += 1
                } else {
                    if String(_charAt(value, i)) == "]" {
                        depth -= 1
                    }
                }
                i += 1
            }
            if depth != 0 {
                return value
            }
        }
        if i < value.count && String(_charAt(value, i)) == "+" {
            i += 1
        }
        if !(i + 1 < value.count && String(_charAt(value, i)) == "=" && String(_charAt(value, i + 1)) == "(") {
            return value
        }
        var `prefix`: String = _substring(value, 0, i + 1)
        var openParenPos: Int = i + 1
        var closeParenPos: Int = 0
        if value.hasSuffix(")") {
            closeParenPos = value.count - 1
        } else {
            closeParenPos = self._findMatchingParen(value, openParenPos)
            if closeParenPos < 0 {
                return value
            }
        }
        var inner: String = _substring(value, openParenPos + 1, closeParenPos)
        var suffix: String = _substring(value, closeParenPos + 1, value.count)
        var result: String = self._normalizeArrayInner(inner)
        return `prefix` + "(" + result + ")" + suffix
    }

    func _findMatchingParen(_ value: String, _ openPos: Int) -> Int {
        if openPos >= value.count || String(_charAt(value, openPos)) != "(" {
            return -1
        }
        var i: Int = openPos + 1
        var depth: Int = 1
        var quote: QuoteState = newQuoteState()
        while i < value.count && depth > 0 {
            var ch: String = String(_charAt(value, i))
            if ch == "\\" && i + 1 < value.count && !quote.single {
                i += 2
                continue
            }
            if ch == "'" && !quote.double {
                quote.single = !quote.single
                i += 1
                continue
            }
            if ch == "\"" && !quote.single {
                quote.double = !quote.double
                i += 1
                continue
            }
            if quote.single || quote.double {
                i += 1
                continue
            }
            if ch == "#" {
                while i < value.count && String(_charAt(value, i)) != "\n" {
                    i += 1
                }
                continue
            }
            if ch == "(" {
                depth += 1
            } else {
                if ch == ")" {
                    depth -= 1
                    if depth == 0 {
                        return i
                    }
                }
            }
            i += 1
        }
        return -1
    }

    func _normalizeArrayInner(_ inner: String) -> String {
        var normalized: [String] = []
        var i: Int = 0
        var inWhitespace: Bool = true
        var braceDepth: Int = 0
        var bracketDepth: Int = 0
        while i < inner.count {
            var ch: String = String(_charAt(inner, i))
            if _isWhitespace(ch) {
                if !inWhitespace && (!normalized.isEmpty) && braceDepth == 0 && bracketDepth == 0 {
                    normalized.append(" ")
                    inWhitespace = true
                }
                if braceDepth > 0 || bracketDepth > 0 {
                    normalized.append(ch)
                }
                i += 1
            } else {
                var j: Int = 0
                if ch == "'" {
                    inWhitespace = false
                    j = i + 1
                    while j < inner.count && String(_charAt(inner, j)) != "'" {
                        j += 1
                    }
                    normalized.append(_substring(inner, i, j + 1))
                    i = j + 1
                } else {
                    if ch == "\"" {
                        inWhitespace = false
                        j = i + 1
                        var dqContent: [String] = ["\""]
                        var dqBraceDepth: Int = 0
                        while j < inner.count {
                            if String(_charAt(inner, j)) == "\\" && j + 1 < inner.count {
                                if String(_charAt(inner, j + 1)) == "\n" {
                                    j += 2
                                } else {
                                    dqContent.append(String(_charAt(inner, j)))
                                    dqContent.append(String(_charAt(inner, j + 1)))
                                    j += 2
                                }
                            } else {
                                if _isExpansionStart(inner, j, "${") {
                                    dqContent.append("${")
                                    dqBraceDepth += 1
                                    j += 2
                                } else {
                                    if String(_charAt(inner, j)) == "}" && dqBraceDepth > 0 {
                                        dqContent.append("}")
                                        dqBraceDepth -= 1
                                        j += 1
                                    } else {
                                        if String(_charAt(inner, j)) == "\"" && dqBraceDepth == 0 {
                                            dqContent.append("\"")
                                            j += 1
                                            break
                                        } else {
                                            dqContent.append(String(_charAt(inner, j)))
                                            j += 1
                                        }
                                    }
                                }
                            }
                        }
                        normalized.append(dqContent.joined(separator: ""))
                        i = j
                    } else {
                        if ch == "\\" && i + 1 < inner.count {
                            if String(_charAt(inner, i + 1)) == "\n" {
                                i += 2
                            } else {
                                inWhitespace = false
                                normalized.append(_substring(inner, i, i + 2))
                                i += 2
                            }
                        } else {
                            var depth: Int = 0
                            if _isExpansionStart(inner, i, "$((") {
                                inWhitespace = false
                                j = i + 3
                                depth = 1
                                while j < inner.count && depth > 0 {
                                    if j + 1 < inner.count && String(_charAt(inner, j)) == "(" && String(_charAt(inner, j + 1)) == "(" {
                                        depth += 1
                                        j += 2
                                    } else {
                                        if j + 1 < inner.count && String(_charAt(inner, j)) == ")" && String(_charAt(inner, j + 1)) == ")" {
                                            depth -= 1
                                            j += 2
                                        } else {
                                            j += 1
                                        }
                                    }
                                }
                                normalized.append(_substring(inner, i, j))
                                i = j
                            } else {
                                if _isExpansionStart(inner, i, "$(") {
                                    inWhitespace = false
                                    j = i + 2
                                    depth = 1
                                    while j < inner.count && depth > 0 {
                                        if String(_charAt(inner, j)) == "(" && j > 0 && String(_charAt(inner, j - 1)) == "$" {
                                            depth += 1
                                        } else {
                                            if String(_charAt(inner, j)) == ")" {
                                                depth -= 1
                                            } else {
                                                if String(_charAt(inner, j)) == "'" {
                                                    j += 1
                                                    while j < inner.count && String(_charAt(inner, j)) != "'" {
                                                        j += 1
                                                    }
                                                } else {
                                                    if String(_charAt(inner, j)) == "\"" {
                                                        j += 1
                                                        while j < inner.count {
                                                            if String(_charAt(inner, j)) == "\\" && j + 1 < inner.count {
                                                                j += 2
                                                                continue
                                                            }
                                                            if String(_charAt(inner, j)) == "\"" {
                                                                break
                                                            }
                                                            j += 1
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        j += 1
                                    }
                                    normalized.append(_substring(inner, i, j))
                                    i = j
                                } else {
                                    if ch == "<" || ch == ">" && i + 1 < inner.count && String(_charAt(inner, i + 1)) == "(" {
                                        inWhitespace = false
                                        j = i + 2
                                        depth = 1
                                        while j < inner.count && depth > 0 {
                                            if String(_charAt(inner, j)) == "(" {
                                                depth += 1
                                            } else {
                                                if String(_charAt(inner, j)) == ")" {
                                                    depth -= 1
                                                } else {
                                                    if String(_charAt(inner, j)) == "'" {
                                                        j += 1
                                                        while j < inner.count && String(_charAt(inner, j)) != "'" {
                                                            j += 1
                                                        }
                                                    } else {
                                                        if String(_charAt(inner, j)) == "\"" {
                                                            j += 1
                                                            while j < inner.count {
                                                                if String(_charAt(inner, j)) == "\\" && j + 1 < inner.count {
                                                                    j += 2
                                                                    continue
                                                                }
                                                                if String(_charAt(inner, j)) == "\"" {
                                                                    break
                                                                }
                                                                j += 1
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                            j += 1
                                        }
                                        normalized.append(_substring(inner, i, j))
                                        i = j
                                    } else {
                                        if _isExpansionStart(inner, i, "${") {
                                            inWhitespace = false
                                            normalized.append("${")
                                            braceDepth += 1
                                            i += 2
                                        } else {
                                            if ch == "{" && braceDepth > 0 {
                                                normalized.append(ch)
                                                braceDepth += 1
                                                i += 1
                                            } else {
                                                if ch == "}" && braceDepth > 0 {
                                                    normalized.append(ch)
                                                    braceDepth -= 1
                                                    i += 1
                                                } else {
                                                    if ch == "#" && braceDepth == 0 && inWhitespace {
                                                        while i < inner.count && String(_charAt(inner, i)) != "\n" {
                                                            i += 1
                                                        }
                                                    } else {
                                                        if ch == "[" {
                                                            if inWhitespace || bracketDepth > 0 {
                                                                bracketDepth += 1
                                                            }
                                                            inWhitespace = false
                                                            normalized.append(ch)
                                                            i += 1
                                                        } else {
                                                            if ch == "]" && bracketDepth > 0 {
                                                                normalized.append(ch)
                                                                bracketDepth -= 1
                                                                i += 1
                                                            } else {
                                                                inWhitespace = false
                                                                normalized.append(ch)
                                                                i += 1
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
        return String(normalized.joined(separator: "").reversed().drop(while: { $0.isWhitespace }).reversed())
    }

    func _stripArithLineContinuations(_ value: String) -> String {
        var result: [String] = []
        var i: Int = 0
        while i < value.count {
            if _isExpansionStart(value, i, "$((") {
                var start: Int = i
                i += 3
                var depth: Int = 2
                var arithContent: [String] = []
                var firstCloseIdx: Int = -1
                while i < value.count && depth > 0 {
                    if String(_charAt(value, i)) == "(" {
                        arithContent.append("(")
                        depth += 1
                        i += 1
                        if depth > 1 {
                            firstCloseIdx = -1
                        }
                    } else {
                        if String(_charAt(value, i)) == ")" {
                            if depth == 2 {
                                firstCloseIdx = arithContent.count
                            }
                            depth -= 1
                            if depth > 0 {
                                arithContent.append(")")
                            }
                            i += 1
                        } else {
                            if String(_charAt(value, i)) == "\\" && i + 1 < value.count && String(_charAt(value, i + 1)) == "\n" {
                                var numBackslashes: Int = 0
                                var j: Int = arithContent.count - 1
                                while j >= 0 && arithContent[j] == "\n" {
                                    j -= 1
                                }
                                while j >= 0 && arithContent[j] == "\\" {
                                    numBackslashes += 1
                                    j -= 1
                                }
                                if numBackslashes % 2 == 1 {
                                    arithContent.append("\\")
                                    arithContent.append("\n")
                                    i += 2
                                } else {
                                    i += 2
                                }
                                if depth == 1 {
                                    firstCloseIdx = -1
                                }
                            } else {
                                arithContent.append(String(_charAt(value, i)))
                                i += 1
                                if depth == 1 {
                                    firstCloseIdx = -1
                                }
                            }
                        }
                    }
                }
                if depth == 0 || depth == 1 && firstCloseIdx != -1 {
                    var content: String = arithContent.joined(separator: "")
                    if firstCloseIdx != -1 {
                        content = String(content.prefix(firstCloseIdx))
                        var closing: String = (depth == 0 ? "))" : ")")
                        result.append("$((" + content + closing)
                    } else {
                        result.append("$((" + content + ")")
                    }
                } else {
                    result.append(_substring(value, start, i))
                }
            } else {
                result.append(String(_charAt(value, i)))
                i += 1
            }
        }
        return result.joined(separator: "")
    }

    func _collectCmdsubs(_ node: Node) -> [Node] {
        var result: [Node] = []
        switch node {
        case let node as CommandSubstitution:
            result.append(node)
        case let node as `Array`:
            for elem in node.elements {
                for p in elem.parts {
                    switch p {
                    case let p as CommandSubstitution:
                        result.append(p)
                    default:
                        result.append(contentsOf: self._collectCmdsubs(p))
                    }
                }
            }
        case let node as ArithmeticExpansion:
            if node.expression != nil {
                result.append(contentsOf: self._collectCmdsubs(node.expression))
            }
        case let node as ArithBinaryOp:
            result.append(contentsOf: self._collectCmdsubs(node.`left`))
            result.append(contentsOf: self._collectCmdsubs(node.`right`))
        case let node as ArithComma:
            result.append(contentsOf: self._collectCmdsubs(node.`left`))
            result.append(contentsOf: self._collectCmdsubs(node.`right`))
        case let node as ArithUnaryOp:
            result.append(contentsOf: self._collectCmdsubs(node.operand))
        case let node as ArithPreIncr:
            result.append(contentsOf: self._collectCmdsubs(node.operand))
        case let node as ArithPostIncr:
            result.append(contentsOf: self._collectCmdsubs(node.operand))
        case let node as ArithPreDecr:
            result.append(contentsOf: self._collectCmdsubs(node.operand))
        case let node as ArithPostDecr:
            result.append(contentsOf: self._collectCmdsubs(node.operand))
        case let node as ArithTernary:
            result.append(contentsOf: self._collectCmdsubs(node.condition))
            result.append(contentsOf: self._collectCmdsubs(node.ifTrue))
            result.append(contentsOf: self._collectCmdsubs(node.ifFalse))
        case let node as ArithAssign:
            result.append(contentsOf: self._collectCmdsubs(node.target))
            result.append(contentsOf: self._collectCmdsubs(node.value))
        default:
            break
        }
        return result
    }

    func _collectProcsubs(_ node: Node) -> [Node] {
        var result: [Node] = []
        switch node {
        case let node as ProcessSubstitution:
            result.append(node)
        case let node as `Array`:
            for elem in node.elements {
                for p in elem.parts {
                    switch p {
                    case let p as ProcessSubstitution:
                        result.append(p)
                    default:
                        result.append(contentsOf: self._collectProcsubs(p))
                    }
                }
            }
        default:
            break
        }
        return result
    }

    func _formatCommandSubstitutions(_ value: String, _ inArith: Bool) -> String {
        var cmdsubParts: [Node] = []
        var procsubParts: [Node] = []
        var hasArith: Bool = false
        for p in self.parts {
            switch p {
            case let p as CommandSubstitution:
                cmdsubParts.append(p)
            case let p as ProcessSubstitution:
                procsubParts.append(p)
            case let p as ArithmeticExpansion:
                hasArith = true
            default:
                cmdsubParts.append(contentsOf: self._collectCmdsubs(p))
                procsubParts.append(contentsOf: self._collectProcsubs(p))
            }
        }
        var hasBraceCmdsub: Bool = (value.range(of: "${ ").map { value.distance(from: value.startIndex, to: $0.lowerBound) } ?? -1) != -1 || (value.range(of: "${\t").map { value.distance(from: value.startIndex, to: $0.lowerBound) } ?? -1) != -1 || (value.range(of: "${\n").map { value.distance(from: value.startIndex, to: $0.lowerBound) } ?? -1) != -1 || (value.range(of: "${|").map { value.distance(from: value.startIndex, to: $0.lowerBound) } ?? -1) != -1
        var hasUntrackedCmdsub: Bool = false
        var hasUntrackedProcsub: Bool = false
        var idx: Int = 0
        var scanQuote: QuoteState = newQuoteState()
        while idx < value.count {
            if String(_charAt(value, idx)) == "\"" {
                scanQuote.double = !scanQuote.double
                idx += 1
            } else {
                if String(_charAt(value, idx)) == "'" && !scanQuote.double {
                    idx += 1
                    while idx < value.count && String(_charAt(value, idx)) != "'" {
                        idx += 1
                    }
                    if idx < value.count {
                        idx += 1
                    }
                } else {
                    if _startsWithAt(value, idx, "$(") && !_startsWithAt(value, idx, "$((") && !_isBackslashEscaped(value, idx) && !_isDollarDollarParen(value, idx) {
                        hasUntrackedCmdsub = true
                        break
                    } else {
                        if _startsWithAt(value, idx, "<(") || _startsWithAt(value, idx, ">(") && !scanQuote.double {
                            if idx == 0 || !(String(_charAt(value, idx - 1)).first?.isLetter ?? false || String(_charAt(value, idx - 1)).first?.isNumber ?? false) && !"\"'".contains(String(_charAt(value, idx - 1))) {
                                hasUntrackedProcsub = true
                                break
                            }
                            idx += 1
                        } else {
                            idx += 1
                        }
                    }
                }
            }
        }
        var hasParamWithProcsubPattern: Bool = value.contains("${") && value.contains("<(") || value.contains(">(")
        if !(!cmdsubParts.isEmpty) && !(!procsubParts.isEmpty) && !hasBraceCmdsub && !hasUntrackedCmdsub && !hasUntrackedProcsub && !hasParamWithProcsubPattern {
            return value
        }
        var result: [String] = []
        var i: Int = 0
        var cmdsubIdx: Int = 0
        var procsubIdx: Int = 0
        var mainQuote: QuoteState = newQuoteState()
        var extglobDepth: Int = 0
        var deprecatedArithDepth: Int = 0
        var arithDepth: Int = 0
        var arithParenDepth: Int = 0
        while i < value.count {
            if i > 0 && _isExtglobPrefix(String(_charAt(value, i - 1))) && String(_charAt(value, i)) == "(" && !_isBackslashEscaped(value, i - 1) {
                extglobDepth += 1
                result.append(String(_charAt(value, i)))
                i += 1
                continue
            }
            if String(_charAt(value, i)) == ")" && extglobDepth > 0 {
                extglobDepth -= 1
                result.append(String(_charAt(value, i)))
                i += 1
                continue
            }
            if _startsWithAt(value, i, "$[") && !_isBackslashEscaped(value, i) {
                deprecatedArithDepth += 1
                result.append(String(_charAt(value, i)))
                i += 1
                continue
            }
            if String(_charAt(value, i)) == "]" && deprecatedArithDepth > 0 {
                deprecatedArithDepth -= 1
                result.append(String(_charAt(value, i)))
                i += 1
                continue
            }
            if _isExpansionStart(value, i, "$((") && !_isBackslashEscaped(value, i) && hasArith {
                arithDepth += 1
                arithParenDepth += 2
                result.append("$((")
                i += 3
                continue
            }
            if arithDepth > 0 && arithParenDepth == 2 && _startsWithAt(value, i, "))") {
                arithDepth -= 1
                arithParenDepth -= 2
                result.append("))")
                i += 2
                continue
            }
            if arithDepth > 0 {
                if String(_charAt(value, i)) == "(" {
                    arithParenDepth += 1
                    result.append(String(_charAt(value, i)))
                    i += 1
                    continue
                } else {
                    if String(_charAt(value, i)) == ")" {
                        arithParenDepth -= 1
                        result.append(String(_charAt(value, i)))
                        i += 1
                        continue
                    }
                }
            }
            var j: Int = 0
            if _isExpansionStart(value, i, "$((") && !hasArith {
                j = _findCmdsubEnd(value, i + 2)
                result.append(_substring(value, i, j))
                if cmdsubIdx < cmdsubParts.count {
                    cmdsubIdx += 1
                }
                i = j
                continue
            }
            var inner: String = ""
            var node: Node? = nil
            var formatted: String = ""
            var parser: Parser? = nil
            var parsed: Node? = nil
            if _startsWithAt(value, i, "$(") && !_startsWithAt(value, i, "$((") && !_isBackslashEscaped(value, i) && !_isDollarDollarParen(value, i) {
                j = _findCmdsubEnd(value, i + 2)
                if extglobDepth > 0 {
                    result.append(_substring(value, i, j))
                    if cmdsubIdx < cmdsubParts.count {
                        cmdsubIdx += 1
                    }
                    i = j
                    continue
                }
                inner = _substring(value, i + 2, j - 1)
                if cmdsubIdx < cmdsubParts.count {
                    node = cmdsubParts[cmdsubIdx]
                    formatted = _formatCmdsubNode((node! as! CommandSubstitution).command, 0, false, false, false)
                    cmdsubIdx += 1
                } else {
                    do {
                        parser = newParser(inner, false, false)
                        parsed = try parser!.parseList(true)
                        formatted = (parsed != nil ? _formatCmdsubNode(parsed!, 0, false, false, false) : "")
                    } catch {
                        formatted = inner
                    }
                }
                if formatted.hasPrefix("(") {
                    result.append("$( " + formatted + ")")
                } else {
                    result.append("$(" + formatted + ")")
                }
                i = j
            } else {
                if String(_charAt(value, i)) == "`" && cmdsubIdx < cmdsubParts.count {
                    j = i + 1
                    while j < value.count {
                        if String(_charAt(value, j)) == "\\" && j + 1 < value.count {
                            j += 2
                            continue
                        }
                        if String(_charAt(value, j)) == "`" {
                            j += 1
                            break
                        }
                        j += 1
                    }
                    result.append(_substring(value, i, j))
                    cmdsubIdx += 1
                    i = j
                } else {
                    var `prefix`: String = ""
                    if _isExpansionStart(value, i, "${") && i + 2 < value.count && _isFunsubChar(String(_charAt(value, i + 2))) && !_isBackslashEscaped(value, i) {
                        j = _findFunsubEnd(value, i + 2)
                        var cmdsubNode: Node? = (cmdsubIdx < cmdsubParts.count ? cmdsubParts[cmdsubIdx] : nil)
                        if (cmdsubNode! is CommandSubstitution) && (cmdsubNode! as! CommandSubstitution).brace {
                            node = cmdsubNode!
                            formatted = _formatCmdsubNode((node! as! CommandSubstitution).command, 0, false, false, false)
                            var hasPipe: Bool = String(_charAt(value, i + 2)) == "|"
                            `prefix` = (hasPipe ? "${|" : "${ ")
                            var origInner: String = _substring(value, i + 2, j - 1)
                            var endsWithNewline: Bool = origInner.hasSuffix("\n")
                            var suffix: String = ""
                            if !(!formatted.isEmpty) || (formatted.first?.isWhitespace ?? false) {
                                suffix = "}"
                            } else {
                                if formatted.hasSuffix("&") || formatted.hasSuffix("& ") {
                                    suffix = (formatted.hasSuffix("&") ? " }" : "}")
                                } else {
                                    if endsWithNewline {
                                        suffix = "\n }"
                                    } else {
                                        suffix = "; }"
                                    }
                                }
                            }
                            result.append(`prefix` + formatted + suffix)
                            cmdsubIdx += 1
                        } else {
                            result.append(_substring(value, i, j))
                        }
                        i = j
                    } else {
                        if _startsWithAt(value, i, ">(") || _startsWithAt(value, i, "<(") && !mainQuote.double && deprecatedArithDepth == 0 && arithDepth == 0 {
                            var isProcsub: Bool = i == 0 || !(String(_charAt(value, i - 1)).first?.isLetter ?? false || String(_charAt(value, i - 1)).first?.isNumber ?? false) && !"\"'".contains(String(_charAt(value, i - 1)))
                            if extglobDepth > 0 {
                                j = _findCmdsubEnd(value, i + 2)
                                result.append(_substring(value, i, j))
                                if procsubIdx < procsubParts.count {
                                    procsubIdx += 1
                                }
                                i = j
                                continue
                            }
                            var direction: String = ""
                            var compact: Bool = false
                            var stripped: String = ""
                            if procsubIdx < procsubParts.count {
                                direction = String(_charAt(value, i))
                                j = _findCmdsubEnd(value, i + 2)
                                node = procsubParts[procsubIdx]
                                compact = _startsWithSubshell((node! as! ProcessSubstitution).command)
                                formatted = _formatCmdsubNode((node! as! ProcessSubstitution).command, 0, true, compact, true)
                                var rawContent: String = _substring(value, i + 2, j - 1)
                                if (node! as! ProcessSubstitution).command.kind == "subshell" {
                                    var leadingWsEnd: Int = 0
                                    while leadingWsEnd < rawContent.count && " \t\n".contains(String(_charAt(rawContent, leadingWsEnd))) {
                                        leadingWsEnd += 1
                                    }
                                    var leadingWs: String = String(rawContent.prefix(leadingWsEnd))
                                    stripped = String(rawContent.dropFirst(leadingWsEnd))
                                    if stripped.hasPrefix("(") {
                                        if (!leadingWs.isEmpty) {
                                            var normalizedWs: String = leadingWs.replacingOccurrences(of: "\n", with: " ").replacingOccurrences(of: "\t", with: " ")
                                            var spaced: String = _formatCmdsubNode((node! as! ProcessSubstitution).command, 0, false, false, false)
                                            result.append(direction + "(" + normalizedWs + spaced + ")")
                                        } else {
                                            rawContent = rawContent.replacingOccurrences(of: "\\\n", with: "")
                                            result.append(direction + "(" + rawContent + ")")
                                        }
                                        procsubIdx += 1
                                        i = j
                                        continue
                                    }
                                }
                                rawContent = _substring(value, i + 2, j - 1)
                                var rawStripped: String = rawContent.replacingOccurrences(of: "\\\n", with: "")
                                if _startsWithSubshell((node! as! ProcessSubstitution).command) && formatted != rawStripped {
                                    result.append(direction + "(" + rawStripped + ")")
                                } else {
                                    var finalOutput: String = direction + "(" + formatted + ")"
                                    result.append(finalOutput)
                                }
                                procsubIdx += 1
                                i = j
                            } else {
                                if isProcsub && (self.parts.count != 0) {
                                    direction = String(_charAt(value, i))
                                    j = _findCmdsubEnd(value, i + 2)
                                    if j > value.count || j > 0 && j <= value.count && String(_charAt(value, j - 1)) != ")" {
                                        result.append(String(_charAt(value, i)))
                                        i += 1
                                        continue
                                    }
                                    inner = _substring(value, i + 2, j - 1)
                                    do {
                                        parser = newParser(inner, false, false)
                                        parsed = try parser!.parseList(true)
                                        if parsed != nil && parser!.pos == inner.count && !inner.contains("\n") {
                                            compact = _startsWithSubshell(parsed!)
                                            formatted = _formatCmdsubNode(parsed!, 0, true, compact, true)
                                        } else {
                                            formatted = inner
                                        }
                                    } catch {
                                        formatted = inner
                                    }
                                    result.append(direction + "(" + formatted + ")")
                                    i = j
                                } else {
                                    if isProcsub {
                                        direction = String(_charAt(value, i))
                                        j = _findCmdsubEnd(value, i + 2)
                                        if j > value.count || j > 0 && j <= value.count && String(_charAt(value, j - 1)) != ")" {
                                            result.append(String(_charAt(value, i)))
                                            i += 1
                                            continue
                                        }
                                        inner = _substring(value, i + 2, j - 1)
                                        if inArith {
                                            result.append(direction + "(" + inner + ")")
                                        } else {
                                            if (!inner.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty) {
                                                stripped = inner.trimmingCharacters(in: CharacterSet(charactersIn: " \t"))
                                                result.append(direction + "(" + stripped + ")")
                                            } else {
                                                result.append(direction + "(" + inner + ")")
                                            }
                                        }
                                        i = j
                                    } else {
                                        result.append(String(_charAt(value, i)))
                                        i += 1
                                    }
                                }
                            }
                        } else {
                            var depth: Int = 0
                            if _isExpansionStart(value, i, "${ ") || _isExpansionStart(value, i, "${\t") || _isExpansionStart(value, i, "${\n") || _isExpansionStart(value, i, "${|") && !_isBackslashEscaped(value, i) {
                                `prefix` = _substring(value, i, i + 3).replacingOccurrences(of: "\t", with: " ").replacingOccurrences(of: "\n", with: " ")
                                j = i + 3
                                depth = 1
                                while j < value.count && depth > 0 {
                                    if String(_charAt(value, j)) == "{" {
                                        depth += 1
                                    } else {
                                        if String(_charAt(value, j)) == "}" {
                                            depth -= 1
                                        }
                                    }
                                    j += 1
                                }
                                inner = _substring(value, i + 2, j - 1)
                                if inner.trimmingCharacters(in: .whitespacesAndNewlines) == "" {
                                    result.append("${ }")
                                } else {
                                    do {
                                        parser = newParser(inner.trimmingCharacters(in: CharacterSet(charactersIn: " \t\n|")), false, false)
                                        parsed = try parser!.parseList(true)
                                        if parsed != nil {
                                            formatted = _formatCmdsubNode(parsed!, 0, false, false, false)
                                            formatted = formatted.trimmingCharacters(in: CharacterSet(charactersIn: ";"))
                                            var terminator: String = ""
                                            if inner.trimmingCharacters(in: CharacterSet(charactersIn: " \t")).hasSuffix("\n") {
                                                terminator = "\n }"
                                            } else {
                                                if formatted.hasSuffix(" &") {
                                                    terminator = " }"
                                                } else {
                                                    terminator = "; }"
                                                }
                                            }
                                            result.append(`prefix` + formatted + terminator)
                                        } else {
                                            result.append("${ }")
                                        }
                                    } catch {
                                        result.append(_substring(value, i, j))
                                    }
                                }
                                i = j
                            } else {
                                if _isExpansionStart(value, i, "${") && !_isBackslashEscaped(value, i) {
                                    j = i + 2
                                    depth = 1
                                    var braceQuote: QuoteState = newQuoteState()
                                    while j < value.count && depth > 0 {
                                        var c: String = String(_charAt(value, j))
                                        if c == "\\" && j + 1 < value.count && !braceQuote.single {
                                            j += 2
                                            continue
                                        }
                                        if c == "'" && !braceQuote.double {
                                            braceQuote.single = !braceQuote.single
                                        } else {
                                            if c == "\"" && !braceQuote.single {
                                                braceQuote.double = !braceQuote.double
                                            } else {
                                                if !braceQuote.inQuotes() {
                                                    if _isExpansionStart(value, j, "$(") && !_startsWithAt(value, j, "$((") {
                                                        j = _findCmdsubEnd(value, j + 2)
                                                        continue
                                                    }
                                                    if c == "{" {
                                                        depth += 1
                                                    } else {
                                                        if c == "}" {
                                                            depth -= 1
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        j += 1
                                    }
                                    if depth > 0 {
                                        inner = _substring(value, i + 2, j)
                                    } else {
                                        inner = _substring(value, i + 2, j - 1)
                                    }
                                    var formattedInner: String = self._formatCommandSubstitutions(inner, false)
                                    formattedInner = self._normalizeExtglobWhitespace(formattedInner)
                                    if depth == 0 {
                                        result.append("${" + formattedInner + "}")
                                    } else {
                                        result.append("${" + formattedInner)
                                    }
                                    i = j
                                } else {
                                    if String(_charAt(value, i)) == "\"" {
                                        mainQuote.double = !mainQuote.double
                                        result.append(String(_charAt(value, i)))
                                        i += 1
                                    } else {
                                        if String(_charAt(value, i)) == "'" && !mainQuote.double {
                                            j = i + 1
                                            while j < value.count && String(_charAt(value, j)) != "'" {
                                                j += 1
                                            }
                                            if j < value.count {
                                                j += 1
                                            }
                                            result.append(_substring(value, i, j))
                                            i = j
                                        } else {
                                            result.append(String(_charAt(value, i)))
                                            i += 1
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return result.joined(separator: "")
    }

    func _normalizeExtglobWhitespace(_ value: String) -> String {
        var result: [String] = []
        var i: Int = 0
        var extglobQuote: QuoteState = newQuoteState()
        var deprecatedArithDepth: Int = 0
        while i < value.count {
            if String(_charAt(value, i)) == "\"" {
                extglobQuote.double = !extglobQuote.double
                result.append(String(_charAt(value, i)))
                i += 1
                continue
            }
            if _startsWithAt(value, i, "$[") && !_isBackslashEscaped(value, i) {
                deprecatedArithDepth += 1
                result.append(String(_charAt(value, i)))
                i += 1
                continue
            }
            if String(_charAt(value, i)) == "]" && deprecatedArithDepth > 0 {
                deprecatedArithDepth -= 1
                result.append(String(_charAt(value, i)))
                i += 1
                continue
            }
            if i + 1 < value.count && String(_charAt(value, i + 1)) == "(" {
                var prefixChar: String = String(_charAt(value, i))
                if "><".contains(prefixChar) && !extglobQuote.double && deprecatedArithDepth == 0 {
                    result.append(prefixChar)
                    result.append("(")
                    i += 2
                    var depth: Int = 1
                    var patternParts: [String] = []
                    var currentPart: [String] = []
                    var hasPipe: Bool = false
                    while i < value.count && depth > 0 {
                        if String(_charAt(value, i)) == "\\" && i + 1 < value.count {
                            currentPart.append(String(value[value.index(value.startIndex, offsetBy: i)..<value.index(value.startIndex, offsetBy: min(i + 2, value.count))]))
                            i += 2
                            continue
                        } else {
                            if String(_charAt(value, i)) == "(" {
                                depth += 1
                                currentPart.append(String(_charAt(value, i)))
                                i += 1
                            } else {
                                var partContent: String = ""
                                if String(_charAt(value, i)) == ")" {
                                    depth -= 1
                                    if depth == 0 {
                                        partContent = currentPart.joined(separator: "")
                                        if partContent.contains("<<") {
                                            patternParts.append(partContent)
                                        } else {
                                            if hasPipe {
                                                patternParts.append(partContent.trimmingCharacters(in: .whitespacesAndNewlines))
                                            } else {
                                                patternParts.append(partContent)
                                            }
                                        }
                                        break
                                    }
                                    currentPart.append(String(_charAt(value, i)))
                                    i += 1
                                } else {
                                    if String(_charAt(value, i)) == "|" && depth == 1 {
                                        if i + 1 < value.count && String(_charAt(value, i + 1)) == "|" {
                                            currentPart.append("||")
                                            i += 2
                                        } else {
                                            hasPipe = true
                                            partContent = currentPart.joined(separator: "")
                                            if partContent.contains("<<") {
                                                patternParts.append(partContent)
                                            } else {
                                                patternParts.append(partContent.trimmingCharacters(in: .whitespacesAndNewlines))
                                            }
                                            currentPart = []
                                            i += 1
                                        }
                                    } else {
                                        currentPart.append(String(_charAt(value, i)))
                                        i += 1
                                    }
                                }
                            }
                        }
                    }
                    result.append(patternParts.joined(separator: " | "))
                    if depth == 0 {
                        result.append(")")
                        i += 1
                    }
                    continue
                }
            }
            result.append(String(_charAt(value, i)))
            i += 1
        }
        return result.joined(separator: "")
    }

    func getCondFormattedValue() -> String {
        var value: String = self._expandAllAnsiCQuotes(self.value)
        value = self._stripLocaleStringDollars(value)
        value = self._formatCommandSubstitutions(value, false)
        value = self._normalizeExtglobWhitespace(value)
        value = value.replacingOccurrences(of: "\u{0001}", with: "\u{0001}\u{0001}")
        return value.trimmingCharacters(in: CharacterSet(charactersIn: "\n"))
    }

    func getKind() -> String {
        return self.kind
    }
}

class Command: Node {
    var words: [Word] = []
    var redirects: [Node] = []
    var kind: String = ""

    init(words: [Word] = [], redirects: [Node] = [], kind: String = "") {
        self.words = words
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var parts: [String] = []
        for w in self.words {
            parts.append(w.toSexp())
        }
        for r in self.redirects {
            parts.append(r.toSexp())
        }
        var inner: String = parts.joined(separator: " ")
        if !(!inner.isEmpty) {
            return "(command)"
        }
        return "(command " + inner + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Pipeline: Node {
    var commands: [Node] = []
    var kind: String = ""

    init(commands: [Node] = [], kind: String = "") {
        self.commands = commands
        self.kind = kind
    }

    func toSexp() -> String {
        if self.commands.count == 1 {
            return self.commands[0].toSexp()
        }
        var cmds: [(Node, Bool)] = []
        var i: Int = 0
        var cmd: Node? = nil
        while i < self.commands.count {
            cmd = self.commands[i]
            switch cmd! {
            case let cmd as PipeBoth:
                i += 1
                continue
            default:
                break
            }
            var needsRedirect: Bool = i + 1 < self.commands.count && self.commands[i + 1].kind == "pipe-both"
            cmds.append((cmd!, needsRedirect))
            i += 1
        }
        var pair: (Node, Bool) = (nil, false)
        var needs: Bool = false
        if cmds.count == 1 {
            pair = cmds[0]
            cmd = pair.0
            needs = pair.1
            return self._cmdSexp(cmd!, needs)
        }
        var lastPair: (Node, Bool) = cmds[cmds.count - 1]
        var lastCmd: Node = lastPair.0
        var lastNeeds: Bool = lastPair.1
        var result: String = self._cmdSexp(lastCmd, lastNeeds)
        var j: Int = cmds.count - 2
        while j >= 0 {
            pair = cmds[j]
            cmd = pair.0
            needs = pair.1
            if needs && cmd!.kind != "command" {
                result = "(pipe " + cmd!.toSexp() + " (redirect \">&\" 1) " + result + ")"
            } else {
                result = "(pipe " + self._cmdSexp(cmd!, needs) + " " + result + ")"
            }
            j -= 1
        }
        return result
    }

    func _cmdSexp(_ cmd: Node, _ needsRedirect: Bool) -> String {
        if !needsRedirect {
            return cmd.toSexp()
        }
        switch cmd {
        case let cmd as Command:
            var parts: [String] = []
            for w in cmd.words {
                parts.append(w.toSexp())
            }
            for r in cmd.redirects {
                parts.append(r.toSexp())
            }
            parts.append("(redirect \">&\" 1)")
            return "(command " + parts.joined(separator: " ") + ")"
        default:
            break
        }
        return cmd.toSexp()
    }

    func getKind() -> String {
        return self.kind
    }
}

class List: Node {
    var parts: [Node] = []
    var kind: String = ""

    init(parts: [Node] = [], kind: String = "") {
        self.parts = parts
        self.kind = kind
    }

    func toSexp() -> String {
        var parts: [Node] = Swift.Array(self.parts)
        var opNames: [String: String] = ["&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"]
        while parts.count > 1 && parts[parts.count - 1].kind == "operator" && (parts[parts.count - 1] as! Operator).op == ";" || (parts[parts.count - 1] as! Operator).op == "\n" {
            parts = _sublist(parts, 0, parts.count - 1)
        }
        if parts.count == 1 {
            return parts[0].toSexp()
        }
        if parts[parts.count - 1].kind == "operator" && (parts[parts.count - 1] as! Operator).op == "&" {
            var i: Int = parts.count - 3
            while i > 0 {
                if parts[i].kind == "operator" && (parts[i] as! Operator).op == ";" || (parts[i] as! Operator).op == "\n" {
                    var `left`: [Node] = _sublist(parts, 0, i)
                    var `right`: [Node] = _sublist(parts, i + 1, parts.count - 1)
                    var leftSexp: String = ""
                    if `left`.count > 1 {
                        leftSexp = List(parts: `left`, kind: "list").toSexp()
                    } else {
                        leftSexp = `left`[0].toSexp()
                    }
                    var rightSexp: String = ""
                    if `right`.count > 1 {
                        rightSexp = List(parts: `right`, kind: "list").toSexp()
                    } else {
                        rightSexp = `right`[0].toSexp()
                    }
                    return "(semi " + leftSexp + " (background " + rightSexp + "))"
                }
                i += -2
            }
            var innerParts: [Node] = _sublist(parts, 0, parts.count - 1)
            if innerParts.count == 1 {
                return "(background " + innerParts[0].toSexp() + ")"
            }
            var innerList: List = List(parts: innerParts, kind: "list")
            return "(background " + innerList.toSexp() + ")"
        }
        return self._toSexpWithPrecedence(parts, opNames)
    }

    func _toSexpWithPrecedence(_ parts: [Node], _ opNames: [String: String]) -> String {
        var semiPositions: [Int] = []
        var i: Int = 0
        while i < parts.count {
            if parts[i].kind == "operator" && (parts[i] as! Operator).op == ";" || (parts[i] as! Operator).op == "\n" {
                semiPositions.append(i)
            }
            i += 1
        }
        if (!semiPositions.isEmpty) {
            var segments: [[Node]] = []
            var start: Int = 0
            var seg: [Node] = []
            for pos in semiPositions {
                seg = _sublist(parts, start, pos)
                if (!seg.isEmpty) && seg[0].kind != "operator" {
                    segments.append(seg)
                }
                start = pos + 1
            }
            seg = _sublist(parts, start, parts.count)
            if (!seg.isEmpty) && seg[0].kind != "operator" {
                segments.append(seg)
            }
            if !(!segments.isEmpty) {
                return "()"
            }
            var result: String = self._toSexpAmpAndHigher(segments[0], opNames)
            var i: Int = 1
            while i < segments.count {
                result = "(semi " + result + " " + self._toSexpAmpAndHigher(segments[i], opNames) + ")"
                i += 1
            }
            return result
        }
        return self._toSexpAmpAndHigher(parts, opNames)
    }

    func _toSexpAmpAndHigher(_ parts: [Node], _ opNames: [String: String]) -> String {
        if parts.count == 1 {
            return parts[0].toSexp()
        }
        var ampPositions: [Int] = []
        var i: Int = 1
        while i < parts.count - 1 {
            if parts[i].kind == "operator" && (parts[i] as! Operator).op == "&" {
                ampPositions.append(i)
            }
            i += 2
        }
        if (!ampPositions.isEmpty) {
            var segments: [[Node]] = []
            var start: Int = 0
            for pos in ampPositions {
                segments.append(_sublist(parts, start, pos))
                start = pos + 1
            }
            segments.append(_sublist(parts, start, parts.count))
            var result: String = self._toSexpAndOr(segments[0], opNames)
            var i: Int = 1
            while i < segments.count {
                result = "(background " + result + " " + self._toSexpAndOr(segments[i], opNames) + ")"
                i += 1
            }
            return result
        }
        return self._toSexpAndOr(parts, opNames)
    }

    func _toSexpAndOr(_ parts: [Node], _ opNames: inout [String: String]) -> String {
        if parts.count == 1 {
            return parts[0].toSexp()
        }
        var result: String = parts[0].toSexp()
        var i: Int = 1
        while i < parts.count - 1 {
            var op: Node = parts[i]
            var cmd: Node = parts[i + 1]
            var opName: String = (opNames[(op as! Operator).op] ?? (op as! Operator).op)
            result = "(" + opName + " " + result + " " + cmd.toSexp() + ")"
            i += 2
        }
        return result
    }

    func getKind() -> String {
        return self.kind
    }
}

class Operator: Node {
    var op: String = ""
    var kind: String = ""

    init(op: String = "", kind: String = "") {
        self.op = op
        self.kind = kind
    }

    func toSexp() -> String {
        var names: [String: String] = ["&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"]
        return "(" + (names[self.op] ?? self.op) + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class PipeBoth: Node {
    var kind: String = ""

    init(kind: String = "") {
        self.kind = kind
    }

    func toSexp() -> String {
        return "(pipe-both)"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Empty: Node {
    var kind: String = ""

    init(kind: String = "") {
        self.kind = kind
    }

    func toSexp() -> String {
        return ""
    }

    func getKind() -> String {
        return self.kind
    }
}

class Comment: Node {
    var text: String = ""
    var kind: String = ""

    init(text: String = "", kind: String = "") {
        self.text = text
        self.kind = kind
    }

    func toSexp() -> String {
        return ""
    }

    func getKind() -> String {
        return self.kind
    }
}

class Redirect: Node {
    var op: String = ""
    var target: Word!
    var fd: Int = 0
    var kind: String = ""

    init(op: String = "", target: Word? = nil, fd: Int = 0, kind: String = "") {
        self.op = op
        if let target = target { self.target = target }
        self.fd = fd
        self.kind = kind
    }

    func toSexp() -> String {
        var op: String = self.op.trimmingCharacters(in: CharacterSet(charactersIn: "0123456789"))
        if op.hasPrefix("{") {
            var j: Int = 1
            if j < op.count && (String(_charAt(op, j)).first?.isLetter ?? false) || String(_charAt(op, j)) == "_" {
                j += 1
                while j < op.count && (String(_charAt(op, j)).first?.isLetter ?? false || String(_charAt(op, j)).first?.isNumber ?? false) || String(_charAt(op, j)) == "_" {
                    j += 1
                }
                if j < op.count && String(_charAt(op, j)) == "[" {
                    j += 1
                    while j < op.count && String(_charAt(op, j)) != "]" {
                        j += 1
                    }
                    if j < op.count && String(_charAt(op, j)) == "]" {
                        j += 1
                    }
                }
                if j < op.count && String(_charAt(op, j)) == "}" {
                    op = _substring(op, j + 1, op.count)
                }
            }
        }
        var targetVal: String = self.target.value
        targetVal = self.target._expandAllAnsiCQuotes(targetVal)
        targetVal = self.target._stripLocaleStringDollars(targetVal)
        targetVal = self.target._formatCommandSubstitutions(targetVal, false)
        targetVal = self.target._stripArithLineContinuations(targetVal)
        if targetVal.hasSuffix("\\") && !targetVal.hasSuffix("\\\\") {
            targetVal = targetVal + "\\"
        }
        if targetVal.hasPrefix("&") {
            if op == ">" {
                op = ">&"
            } else {
                if op == "<" {
                    op = "<&"
                }
            }
            var raw: String = _substring(targetVal, 1, targetVal.count)
            if (raw.first?.isNumber ?? false) && Int(raw, radix: 10)! <= 2147483647 {
                return "(redirect \"" + op + "\" " + String(Int(raw, radix: 10)!) + ")"
            }
            if raw.hasSuffix("-") && (String(raw.prefix(raw.count - 1)).first?.isNumber ?? false) && Int(String(raw.prefix(raw.count - 1)), radix: 10)! <= 2147483647 {
                return "(redirect \"" + op + "\" " + String(Int(String(raw.prefix(raw.count - 1)), radix: 10)!) + ")"
            }
            if targetVal == "&-" {
                return "(redirect \">&-\" 0)"
            }
            var fdTarget: String = (raw.hasSuffix("-") ? String(raw.prefix(raw.count - 1)) : raw)
            return "(redirect \"" + op + "\" \"" + fdTarget + "\")"
        }
        if op == ">&" || op == "<&" {
            if (targetVal.first?.isNumber ?? false) && Int(targetVal, radix: 10)! <= 2147483647 {
                return "(redirect \"" + op + "\" " + String(Int(targetVal, radix: 10)!) + ")"
            }
            if targetVal == "-" {
                return "(redirect \">&-\" 0)"
            }
            if targetVal.hasSuffix("-") && (String(targetVal.prefix(targetVal.count - 1)).first?.isNumber ?? false) && Int(String(targetVal.prefix(targetVal.count - 1)), radix: 10)! <= 2147483647 {
                return "(redirect \"" + op + "\" " + String(Int(String(targetVal.prefix(targetVal.count - 1)), radix: 10)!) + ")"
            }
            var outVal: String = (targetVal.hasSuffix("-") ? String(targetVal.prefix(targetVal.count - 1)) : targetVal)
            return "(redirect \"" + op + "\" \"" + outVal + "\")"
        }
        return "(redirect \"" + op + "\" \"" + targetVal + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class HereDoc: Node {
    var delimiter: String = ""
    var content: String = ""
    var stripTabs: Bool = false
    var quoted: Bool = false
    var fd: Int = 0
    var complete: Bool = false
    var _startPos: Int = 0
    var kind: String = ""

    init(delimiter: String = "", content: String = "", stripTabs: Bool = false, quoted: Bool = false, fd: Int = 0, complete: Bool = false, _startPos: Int = 0, kind: String = "") {
        self.delimiter = delimiter
        self.content = content
        self.stripTabs = stripTabs
        self.quoted = quoted
        self.fd = fd
        self.complete = complete
        self._startPos = _startPos
        self.kind = kind
    }

    func toSexp() -> String {
        var op: String = (self.stripTabs ? "<<-" : "<<")
        var content: String = self.content
        if content.hasSuffix("\\") && !content.hasSuffix("\\\\") {
            content = content + "\\"
        }
        return "(redirect \"\\(op)\" \"\\(content)\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Subshell: Node {
    var body: (Node)!
    var redirects: [Node]?
    var kind: String = ""

    init(body: (Node)? = nil, redirects: [Node]? = nil, kind: String = "") {
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var base: String = "(subshell " + self.body.toSexp() + ")"
        return _appendRedirects(base, self.redirects)
    }

    func getKind() -> String {
        return self.kind
    }
}

class BraceGroup: Node {
    var body: (Node)!
    var redirects: [Node]?
    var kind: String = ""

    init(body: (Node)? = nil, redirects: [Node]? = nil, kind: String = "") {
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var base: String = "(brace-group " + self.body.toSexp() + ")"
        return _appendRedirects(base, self.redirects)
    }

    func getKind() -> String {
        return self.kind
    }
}

class If: Node {
    var condition: (Node)!
    var thenBody: (Node)!
    var elseBody: Node?
    var redirects: [Node] = []
    var kind: String = ""

    init(condition: (Node)? = nil, thenBody: (Node)? = nil, elseBody: Node? = nil, redirects: [Node] = [], kind: String = "") {
        self.condition = condition
        self.thenBody = thenBody
        self.elseBody = elseBody
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var result: String = "(if " + self.condition.toSexp() + " " + self.thenBody.toSexp()
        if self.elseBody != nil {
            result = result + " " + self.elseBody!.toSexp()
        }
        result = result + ")"
        for r in self.redirects {
            result = result + " " + r.toSexp()
        }
        return result
    }

    func getKind() -> String {
        return self.kind
    }
}

class While: Node {
    var condition: (Node)!
    var body: (Node)!
    var redirects: [Node] = []
    var kind: String = ""

    init(condition: (Node)? = nil, body: (Node)? = nil, redirects: [Node] = [], kind: String = "") {
        self.condition = condition
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var base: String = "(while " + self.condition.toSexp() + " " + self.body.toSexp() + ")"
        return _appendRedirects(base, self.redirects)
    }

    func getKind() -> String {
        return self.kind
    }
}

class Until: Node {
    var condition: (Node)!
    var body: (Node)!
    var redirects: [Node] = []
    var kind: String = ""

    init(condition: (Node)? = nil, body: (Node)? = nil, redirects: [Node] = [], kind: String = "") {
        self.condition = condition
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var base: String = "(until " + self.condition.toSexp() + " " + self.body.toSexp() + ")"
        return _appendRedirects(base, self.redirects)
    }

    func getKind() -> String {
        return self.kind
    }
}

class For: Node {
    var `var`: String = ""
    var words: [Word]?
    var body: (Node)!
    var redirects: [Node] = []
    var kind: String = ""

    init(`var`: String = "", words: [Word]? = nil, body: (Node)? = nil, redirects: [Node] = [], kind: String = "") {
        self.`var` = `var`
        self.words = words
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var suffix: String = ""
        if (!self.redirects.isEmpty) {
            var redirectParts: [String] = []
            for r in self.redirects {
                redirectParts.append(r.toSexp())
            }
            suffix = " " + redirectParts.joined(separator: " ")
        }
        var tempWord: Word = Word(value: self.`var`, parts: [], kind: "word")
        var varFormatted: String = tempWord._formatCommandSubstitutions(self.`var`, false)
        var varEscaped: String = varFormatted.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
        if self.words == nil {
            return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + self.body.toSexp() + ")" + suffix
        } else {
            if self.words!.count == 0 {
                return "(for (word \"" + varEscaped + "\") (in) " + self.body.toSexp() + ")" + suffix
            } else {
                var wordParts: [String] = []
                for w in self.words! {
                    wordParts.append(w.toSexp())
                }
                var wordStrs: String = wordParts.joined(separator: " ")
                return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + self.body.toSexp() + ")" + suffix
            }
        }
    }

    func getKind() -> String {
        return self.kind
    }
}

class ForArith: Node {
    var `init`: String = ""
    var cond: String = ""
    var incr: String = ""
    var body: (Node)!
    var redirects: [Node] = []
    var kind: String = ""

    init(`init`: String = "", cond: String = "", incr: String = "", body: (Node)? = nil, redirects: [Node] = [], kind: String = "") {
        self.`init` = `init`
        self.cond = cond
        self.incr = incr
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var suffix: String = ""
        if (!self.redirects.isEmpty) {
            var redirectParts: [String] = []
            for r in self.redirects {
                redirectParts.append(r.toSexp())
            }
            suffix = " " + redirectParts.joined(separator: " ")
        }
        var initVal: String = ((!self.`init`.isEmpty) ? self.`init` : "1")
        var condVal: String = ((!self.cond.isEmpty) ? self.cond : "1")
        var incrVal: String = ((!self.incr.isEmpty) ? self.incr : "1")
        var initStr: String = _formatArithVal(initVal)
        var condStr: String = _formatArithVal(condVal)
        var incrStr: String = _formatArithVal(incrVal)
        var bodyStr: String = self.body.toSexp()
        return "(arith-for (init (word \"\\(initStr)\")) (test (word \"\\(condStr)\")) (step (word \"\\(incrStr)\")) \\(bodyStr))\\(suffix)"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Select: Node {
    var `var`: String = ""
    var words: [Word]?
    var body: (Node)!
    var redirects: [Node] = []
    var kind: String = ""

    init(`var`: String = "", words: [Word]? = nil, body: (Node)? = nil, redirects: [Node] = [], kind: String = "") {
        self.`var` = `var`
        self.words = words
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var suffix: String = ""
        if (!self.redirects.isEmpty) {
            var redirectParts: [String] = []
            for r in self.redirects {
                redirectParts.append(r.toSexp())
            }
            suffix = " " + redirectParts.joined(separator: " ")
        }
        var varEscaped: String = self.`var`.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
        var inClause: String = ""
        if self.words != nil {
            var wordParts: [String] = []
            for w in self.words! {
                wordParts.append(w.toSexp())
            }
            var wordStrs: String = wordParts.joined(separator: " ")
            if (self.words != nil && !self.words!.isEmpty) {
                inClause = "(in " + wordStrs + ")"
            } else {
                inClause = "(in)"
            }
        } else {
            inClause = "(in (word \"\\\"$@\\\"\"))"
        }
        return "(select (word \"" + varEscaped + "\") " + inClause + " " + self.body.toSexp() + ")" + suffix
    }

    func getKind() -> String {
        return self.kind
    }
}

class Case: Node {
    var word: Word!
    var patterns: [CasePattern] = []
    var redirects: [Node] = []
    var kind: String = ""

    init(word: Word? = nil, patterns: [CasePattern] = [], redirects: [Node] = [], kind: String = "") {
        if let word = word { self.word = word }
        self.patterns = patterns
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var parts: [String] = []
        parts.append("(case " + self.word.toSexp())
        for p in self.patterns {
            parts.append(p.toSexp())
        }
        var base: String = parts.joined(separator: " ") + ")"
        return _appendRedirects(base, self.redirects)
    }

    func getKind() -> String {
        return self.kind
    }
}

class CasePattern: Node {
    var pattern: String = ""
    var body: Node?
    var terminator: String = ""
    var kind: String = ""

    init(pattern: String = "", body: Node? = nil, terminator: String = "", kind: String = "") {
        self.pattern = pattern
        self.body = body
        self.terminator = terminator
        self.kind = kind
    }

    func toSexp() -> String {
        var alternatives: [String] = []
        var current: [String] = []
        var i: Int = 0
        var depth: Int = 0
        while i < self.pattern.count {
            var ch: String = String(_charAt(self.pattern, i))
            if ch == "\\" && i + 1 < self.pattern.count {
                current.append(_substring(self.pattern, i, i + 2))
                i += 2
            } else {
                if ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!" && i + 1 < self.pattern.count && String(_charAt(self.pattern, i + 1)) == "(" {
                    current.append(ch)
                    current.append("(")
                    depth += 1
                    i += 2
                } else {
                    if _isExpansionStart(self.pattern, i, "$(") {
                        current.append(ch)
                        current.append("(")
                        depth += 1
                        i += 2
                    } else {
                        if ch == "(" && depth > 0 {
                            current.append(ch)
                            depth += 1
                            i += 1
                        } else {
                            if ch == ")" && depth > 0 {
                                current.append(ch)
                                depth -= 1
                                i += 1
                            } else {
                                var result0: Int = 0
                                var result1: [String] = []
                                if ch == "[" {
                                    let _tuple22 = _consumeBracketClass(self.pattern, i, depth)
                                    result0 = _tuple22.0
                                    result1 = _tuple22.1
                                    var result2: Bool = _tuple22.2
                                    i = result0
                                    current.append(contentsOf: result1)
                                } else {
                                    if ch == "'" && depth == 0 {
                                        let _tuple23 = _consumeSingleQuote(self.pattern, i)
                                        result0 = _tuple23.0
                                        result1 = _tuple23.1
                                        i = result0
                                        current.append(contentsOf: result1)
                                    } else {
                                        if ch == "\"" && depth == 0 {
                                            let _tuple24 = _consumeDoubleQuote(self.pattern, i)
                                            result0 = _tuple24.0
                                            result1 = _tuple24.1
                                            i = result0
                                            current.append(contentsOf: result1)
                                        } else {
                                            if ch == "|" && depth == 0 {
                                                alternatives.append(current.joined(separator: ""))
                                                current = []
                                                i += 1
                                            } else {
                                                current.append(ch)
                                                i += 1
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
        alternatives.append(current.joined(separator: ""))
        var wordList: [String] = []
        for alt in alternatives {
            wordList.append(Word(value: alt, parts: [], kind: "word").toSexp())
        }
        var patternStr: String = wordList.joined(separator: " ")
        var parts: [String] = ["(pattern (" + patternStr + ")"]
        if self.body != nil {
            parts.append(" " + self.body!.toSexp())
        } else {
            parts.append(" ()")
        }
        parts.append(")")
        return parts.joined(separator: "")
    }

    func getKind() -> String {
        return self.kind
    }
}

class Function: Node {
    var name: String = ""
    var body: (Node)!
    var kind: String = ""

    init(name: String = "", body: (Node)? = nil, kind: String = "") {
        self.name = name
        self.body = body
        self.kind = kind
    }

    func toSexp() -> String {
        return "(function \"" + self.name + "\" " + self.body.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ParamExpansion: Node {
    var param: String = ""
    var op: String = ""
    var arg: String = ""
    var kind: String = ""

    init(param: String = "", op: String = "", arg: String = "", kind: String = "") {
        self.param = param
        self.op = op
        self.arg = arg
        self.kind = kind
    }

    func toSexp() -> String {
        var escapedParam: String = self.param.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
        if self.op != "" {
            var escapedOp: String = self.op.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
            var argVal: String = ""
            if self.arg != "" {
                argVal = self.arg
            } else {
                argVal = ""
            }
            var escapedArg: String = argVal.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
            return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
        }
        return "(param \"" + escapedParam + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ParamLength: Node {
    var param: String = ""
    var kind: String = ""

    init(param: String = "", kind: String = "") {
        self.param = param
        self.kind = kind
    }

    func toSexp() -> String {
        var escaped: String = self.param.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
        return "(param-len \"" + escaped + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ParamIndirect: Node {
    var param: String = ""
    var op: String = ""
    var arg: String = ""
    var kind: String = ""

    init(param: String = "", op: String = "", arg: String = "", kind: String = "") {
        self.param = param
        self.op = op
        self.arg = arg
        self.kind = kind
    }

    func toSexp() -> String {
        var escaped: String = self.param.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
        if self.op != "" {
            var escapedOp: String = self.op.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
            var argVal: String = ""
            if self.arg != "" {
                argVal = self.arg
            } else {
                argVal = ""
            }
            var escapedArg: String = argVal.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
            return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
        }
        return "(param-indirect \"" + escaped + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class CommandSubstitution: Node {
    var command: (Node)!
    var brace: Bool = false
    var kind: String = ""

    init(command: (Node)? = nil, brace: Bool = false, kind: String = "") {
        self.command = command
        self.brace = brace
        self.kind = kind
    }

    func toSexp() -> String {
        if self.brace {
            return "(funsub " + self.command.toSexp() + ")"
        }
        return "(cmdsub " + self.command.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithmeticExpansion: Node {
    var expression: Node?
    var kind: String = ""

    init(expression: Node? = nil, kind: String = "") {
        self.expression = expression
        self.kind = kind
    }

    func toSexp() -> String {
        if self.expression == nil {
            return "(arith)"
        }
        return "(arith " + self.expression!.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithmeticCommand: Node {
    var expression: Node?
    var redirects: [Node] = []
    var rawContent: String = ""
    var kind: String = ""

    init(expression: Node? = nil, redirects: [Node] = [], rawContent: String = "", kind: String = "") {
        self.expression = expression
        self.redirects = redirects
        self.rawContent = rawContent
        self.kind = kind
    }

    func toSexp() -> String {
        var formatted: String = Word(value: self.rawContent, parts: [], kind: "word")._formatCommandSubstitutions(self.rawContent, true)
        var escaped: String = formatted.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n").replacingOccurrences(of: "\t", with: "\\t")
        var result: String = "(arith (word \"" + escaped + "\"))"
        if (!self.redirects.isEmpty) {
            var redirectParts: [String] = []
            for r in self.redirects {
                redirectParts.append(r.toSexp())
            }
            var redirectSexps: String = redirectParts.joined(separator: " ")
            return result + " " + redirectSexps
        }
        return result
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithNumber: Node {
    var value: String = ""
    var kind: String = ""

    init(value: String = "", kind: String = "") {
        self.value = value
        self.kind = kind
    }

    func toSexp() -> String {
        return "(number \"" + self.value + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithEmpty: Node {
    var kind: String = ""

    init(kind: String = "") {
        self.kind = kind
    }

    func toSexp() -> String {
        return "(empty)"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithVar: Node {
    var name: String = ""
    var kind: String = ""

    init(name: String = "", kind: String = "") {
        self.name = name
        self.kind = kind
    }

    func toSexp() -> String {
        return "(var \"" + self.name + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithBinaryOp: Node {
    var op: String = ""
    var `left`: (Node)!
    var `right`: (Node)!
    var kind: String = ""

    init(op: String = "", `left`: (Node)? = nil, `right`: (Node)? = nil, kind: String = "") {
        self.op = op
        self.`left` = `left`
        self.`right` = `right`
        self.kind = kind
    }

    func toSexp() -> String {
        return "(binary-op \"" + self.op + "\" " + self.`left`.toSexp() + " " + self.`right`.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithUnaryOp: Node {
    var op: String = ""
    var operand: (Node)!
    var kind: String = ""

    init(op: String = "", operand: (Node)? = nil, kind: String = "") {
        self.op = op
        self.operand = operand
        self.kind = kind
    }

    func toSexp() -> String {
        return "(unary-op \"" + self.op + "\" " + self.operand.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithPreIncr: Node {
    var operand: (Node)!
    var kind: String = ""

    init(operand: (Node)? = nil, kind: String = "") {
        self.operand = operand
        self.kind = kind
    }

    func toSexp() -> String {
        return "(pre-incr " + self.operand.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithPostIncr: Node {
    var operand: (Node)!
    var kind: String = ""

    init(operand: (Node)? = nil, kind: String = "") {
        self.operand = operand
        self.kind = kind
    }

    func toSexp() -> String {
        return "(post-incr " + self.operand.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithPreDecr: Node {
    var operand: (Node)!
    var kind: String = ""

    init(operand: (Node)? = nil, kind: String = "") {
        self.operand = operand
        self.kind = kind
    }

    func toSexp() -> String {
        return "(pre-decr " + self.operand.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithPostDecr: Node {
    var operand: (Node)!
    var kind: String = ""

    init(operand: (Node)? = nil, kind: String = "") {
        self.operand = operand
        self.kind = kind
    }

    func toSexp() -> String {
        return "(post-decr " + self.operand.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithAssign: Node {
    var op: String = ""
    var target: (Node)!
    var value: (Node)!
    var kind: String = ""

    init(op: String = "", target: (Node)? = nil, value: (Node)? = nil, kind: String = "") {
        self.op = op
        self.target = target
        self.value = value
        self.kind = kind
    }

    func toSexp() -> String {
        return "(assign \"" + self.op + "\" " + self.target.toSexp() + " " + self.value.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithTernary: Node {
    var condition: (Node)!
    var ifTrue: (Node)!
    var ifFalse: (Node)!
    var kind: String = ""

    init(condition: (Node)? = nil, ifTrue: (Node)? = nil, ifFalse: (Node)? = nil, kind: String = "") {
        self.condition = condition
        self.ifTrue = ifTrue
        self.ifFalse = ifFalse
        self.kind = kind
    }

    func toSexp() -> String {
        return "(ternary " + self.condition.toSexp() + " " + self.ifTrue.toSexp() + " " + self.ifFalse.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithComma: Node {
    var `left`: (Node)!
    var `right`: (Node)!
    var kind: String = ""

    init(`left`: (Node)? = nil, `right`: (Node)? = nil, kind: String = "") {
        self.`left` = `left`
        self.`right` = `right`
        self.kind = kind
    }

    func toSexp() -> String {
        return "(comma " + self.`left`.toSexp() + " " + self.`right`.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithSubscript: Node {
    var array: String = ""
    var index: (Node)!
    var kind: String = ""

    init(array: String = "", index: (Node)? = nil, kind: String = "") {
        self.array = array
        self.index = index
        self.kind = kind
    }

    func toSexp() -> String {
        return "(subscript \"" + self.array + "\" " + self.index.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithEscape: Node {
    var char: String = ""
    var kind: String = ""

    init(char: String = "", kind: String = "") {
        self.char = char
        self.kind = kind
    }

    func toSexp() -> String {
        return "(escape \"" + self.char + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithDeprecated: Node {
    var expression: String = ""
    var kind: String = ""

    init(expression: String = "", kind: String = "") {
        self.expression = expression
        self.kind = kind
    }

    func toSexp() -> String {
        var escaped: String = self.expression.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n")
        return "(arith-deprecated \"" + escaped + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ArithConcat: Node {
    var parts: [Node] = []
    var kind: String = ""

    init(parts: [Node] = [], kind: String = "") {
        self.parts = parts
        self.kind = kind
    }

    func toSexp() -> String {
        var sexps: [String] = []
        for p in self.parts {
            sexps.append(p.toSexp())
        }
        return "(arith-concat " + sexps.joined(separator: " ") + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class AnsiCQuote: Node {
    var content: String = ""
    var kind: String = ""

    init(content: String = "", kind: String = "") {
        self.content = content
        self.kind = kind
    }

    func toSexp() -> String {
        var escaped: String = self.content.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n")
        return "(ansi-c \"" + escaped + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class LocaleString: Node {
    var content: String = ""
    var kind: String = ""

    init(content: String = "", kind: String = "") {
        self.content = content
        self.kind = kind
    }

    func toSexp() -> String {
        var escaped: String = self.content.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n")
        return "(locale \"" + escaped + "\")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ProcessSubstitution: Node {
    var direction: String = ""
    var command: (Node)!
    var kind: String = ""

    init(direction: String = "", command: (Node)? = nil, kind: String = "") {
        self.direction = direction
        self.command = command
        self.kind = kind
    }

    func toSexp() -> String {
        return "(procsub \"" + self.direction + "\" " + self.command.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Negation: Node {
    var pipeline: (Node)!
    var kind: String = ""

    init(pipeline: (Node)? = nil, kind: String = "") {
        self.pipeline = pipeline
        self.kind = kind
    }

    func toSexp() -> String {
        if self.pipeline == nil {
            return "(negation (command))"
        }
        return "(negation " + self.pipeline.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Time: Node {
    var pipeline: (Node)!
    var posix: Bool = false
    var kind: String = ""

    init(pipeline: (Node)? = nil, posix: Bool = false, kind: String = "") {
        self.pipeline = pipeline
        self.posix = posix
        self.kind = kind
    }

    func toSexp() -> String {
        if self.pipeline == nil {
            if self.posix {
                return "(time -p (command))"
            } else {
                return "(time (command))"
            }
        }
        if self.posix {
            return "(time -p " + self.pipeline.toSexp() + ")"
        }
        return "(time " + self.pipeline.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class ConditionalExpr: Node {
    var body: (Any)!
    var redirects: [Node] = []
    var kind: String = ""

    init(body: (Any)? = nil, redirects: [Node] = [], kind: String = "") {
        self.body = body
        self.redirects = redirects
        self.kind = kind
    }

    func toSexp() -> String {
        var body: Any = self.body
        var result: String = ""
        switch body {
        case let body as String:
            var escaped: String = body.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n")
            result = "(cond \"" + escaped + "\")"
        default:
            result = "(cond " + body.toSexp() + ")"
        }
        if (!self.redirects.isEmpty) {
            var redirectParts: [String] = []
            for r in self.redirects {
                redirectParts.append(r.toSexp())
            }
            var redirectSexps: String = redirectParts.joined(separator: " ")
            return result + " " + redirectSexps
        }
        return result
    }

    func getKind() -> String {
        return self.kind
    }
}

class UnaryTest: Node {
    var op: String = ""
    var operand: Word!
    var kind: String = ""

    init(op: String = "", operand: Word? = nil, kind: String = "") {
        self.op = op
        if let operand = operand { self.operand = operand }
        self.kind = kind
    }

    func toSexp() -> String {
        var operandVal: String = self.operand.getCondFormattedValue()
        return "(cond-unary \"" + self.op + "\" (cond-term \"" + operandVal + "\"))"
    }

    func getKind() -> String {
        return self.kind
    }
}

class BinaryTest: Node {
    var op: String = ""
    var `left`: Word!
    var `right`: Word!
    var kind: String = ""

    init(op: String = "", `left`: Word? = nil, `right`: Word? = nil, kind: String = "") {
        self.op = op
        if let `left` = `left` { self.`left` = `left` }
        if let `right` = `right` { self.`right` = `right` }
        self.kind = kind
    }

    func toSexp() -> String {
        var leftVal: String = self.`left`.getCondFormattedValue()
        var rightVal: String = self.`right`.getCondFormattedValue()
        return "(cond-binary \"" + self.op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))"
    }

    func getKind() -> String {
        return self.kind
    }
}

class CondAnd: Node {
    var `left`: (Node)!
    var `right`: (Node)!
    var kind: String = ""

    init(`left`: (Node)? = nil, `right`: (Node)? = nil, kind: String = "") {
        self.`left` = `left`
        self.`right` = `right`
        self.kind = kind
    }

    func toSexp() -> String {
        return "(cond-and " + self.`left`.toSexp() + " " + self.`right`.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class CondOr: Node {
    var `left`: (Node)!
    var `right`: (Node)!
    var kind: String = ""

    init(`left`: (Node)? = nil, `right`: (Node)? = nil, kind: String = "") {
        self.`left` = `left`
        self.`right` = `right`
        self.kind = kind
    }

    func toSexp() -> String {
        return "(cond-or " + self.`left`.toSexp() + " " + self.`right`.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class CondNot: Node {
    var operand: (Node)!
    var kind: String = ""

    init(operand: (Node)? = nil, kind: String = "") {
        self.operand = operand
        self.kind = kind
    }

    func toSexp() -> String {
        return self.operand.toSexp()
    }

    func getKind() -> String {
        return self.kind
    }
}

class CondParen: Node {
    var inner: (Node)!
    var kind: String = ""

    init(inner: (Node)? = nil, kind: String = "") {
        self.inner = inner
        self.kind = kind
    }

    func toSexp() -> String {
        return "(cond-expr " + self.inner.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class `Array`: Node {
    var elements: [Word] = []
    var kind: String = ""

    init(elements: [Word] = [], kind: String = "") {
        self.elements = elements
        self.kind = kind
    }

    func toSexp() -> String {
        if !(!self.elements.isEmpty) {
            return "(array)"
        }
        var parts: [String] = []
        for e in self.elements {
            parts.append(e.toSexp())
        }
        var inner: String = parts.joined(separator: " ")
        return "(array " + inner + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Coproc: Node {
    var command: (Node)!
    var name: String = ""
    var kind: String = ""

    init(command: (Node)? = nil, name: String = "", kind: String = "") {
        self.command = command
        self.name = name
        self.kind = kind
    }

    func toSexp() -> String {
        var name: String = ""
        if (!self.name.isEmpty) {
            name = self.name
        } else {
            name = "COPROC"
        }
        return "(coproc \"" + name + "\" " + self.command.toSexp() + ")"
    }

    func getKind() -> String {
        return self.kind
    }
}

class Parser {
    var source: String = ""
    var pos: Int = 0
    var length: Int = 0
    var _pendingHeredocs: [HereDoc] = []
    var _cmdsubHeredocEnd: Int = 0
    var _sawNewlineInSingleQuote: Bool = false
    var _inProcessSub: Bool = false
    var _extglob: Bool = false
    var _ctx: ContextStack!
    var _lexer: Lexer!
    var _tokenHistory: [Token?] = []
    var _parserState: Int = 0
    var _dolbraceState: Int = 0
    var _eofToken: String = ""
    var _wordContext: Int = 0
    var _atCommandStart: Bool = false
    var _inArrayLiteral: Bool = false
    var _inAssignBuiltin: Bool = false
    var _arithSrc: String = ""
    var _arithPos: Int = 0
    var _arithLen: Int = 0

    init(source: String = "", pos: Int = 0, length: Int = 0, _pendingHeredocs: [HereDoc] = [], _cmdsubHeredocEnd: Int = 0, _sawNewlineInSingleQuote: Bool = false, _inProcessSub: Bool = false, _extglob: Bool = false, _ctx: ContextStack? = nil, _lexer: Lexer? = nil, _tokenHistory: [Token?] = [], _parserState: Int = 0, _dolbraceState: Int = 0, _eofToken: String = "", _wordContext: Int = 0, _atCommandStart: Bool = false, _inArrayLiteral: Bool = false, _inAssignBuiltin: Bool = false, _arithSrc: String = "", _arithPos: Int = 0, _arithLen: Int = 0) {
        self.source = source
        self.pos = pos
        self.length = length
        self._pendingHeredocs = _pendingHeredocs
        self._cmdsubHeredocEnd = _cmdsubHeredocEnd
        self._sawNewlineInSingleQuote = _sawNewlineInSingleQuote
        self._inProcessSub = _inProcessSub
        self._extglob = _extglob
        if let _ctx = _ctx { self._ctx = _ctx }
        if let _lexer = _lexer { self._lexer = _lexer }
        self._tokenHistory = _tokenHistory
        self._parserState = _parserState
        self._dolbraceState = _dolbraceState
        self._eofToken = _eofToken
        self._wordContext = _wordContext
        self._atCommandStart = _atCommandStart
        self._inArrayLiteral = _inArrayLiteral
        self._inAssignBuiltin = _inAssignBuiltin
        self._arithSrc = _arithSrc
        self._arithPos = _arithPos
        self._arithLen = _arithLen
    }

    func _setState(_ flag: Int) {
        self._parserState = self._parserState | flag
    }

    func _clearState(_ flag: Int) {
        self._parserState = self._parserState & ~flag
    }

    func _inState(_ flag: Int) -> Bool {
        return self._parserState & flag != 0
    }

    func _saveParserState() -> SavedParserState {
        return SavedParserState(parserState: self._parserState, dolbraceState: self._dolbraceState, pendingHeredocs: self._pendingHeredocs, ctxStack: self._ctx.copyStack(), eofToken: self._eofToken)
    }

    func _restoreParserState(_ saved: SavedParserState) {
        self._parserState = saved.parserState
        self._dolbraceState = saved.dolbraceState
        self._eofToken = saved.eofToken
        self._ctx.restoreFrom(saved.ctxStack)
    }

    func _recordToken(_ tok: Token) {
        self._tokenHistory = [tok, self._tokenHistory[0], self._tokenHistory[1], self._tokenHistory[2]]
    }

    func _updateDolbraceForOp(_ op: String, _ hasParam: Bool) {
        if self._dolbraceState == dolbracestateNone {
            return
        }
        if op == "" || op.count == 0 {
            return
        }
        var firstChar: String = String(_charAt(op, 0))
        if self._dolbraceState == dolbracestateParam && hasParam {
            if "%#^,".contains(firstChar) {
                self._dolbraceState = dolbracestateQuote
                return
            }
            if firstChar == "/" {
                self._dolbraceState = dolbracestateQuote2
                return
            }
        }
        if self._dolbraceState == dolbracestateParam {
            if "#%^,~:-=?+/".contains(firstChar) {
                self._dolbraceState = dolbracestateOp
            }
        }
    }

    func _syncLexer() {
        if self._lexer._tokenCache != nil {
            if self._lexer._tokenCache!.pos != self.pos || self._lexer._cachedWordContext != self._wordContext || self._lexer._cachedAtCommandStart != self._atCommandStart || self._lexer._cachedInArrayLiteral != self._inArrayLiteral || self._lexer._cachedInAssignBuiltin != self._inAssignBuiltin {
                self._lexer._tokenCache = nil
            }
        }
        if self._lexer.pos != self.pos {
            self._lexer.pos = self.pos
        }
        self._lexer._eofToken = self._eofToken
        self._lexer._parserState = self._parserState
        self._lexer._lastReadToken = self._tokenHistory[0]
        self._lexer._wordContext = self._wordContext
        self._lexer._atCommandStart = self._atCommandStart
        self._lexer._inArrayLiteral = self._inArrayLiteral
        self._lexer._inAssignBuiltin = self._inAssignBuiltin
    }

    func _syncParser() {
        self.pos = self._lexer.pos
    }

    func _lexPeekToken() throws -> Token {
        if self._lexer._tokenCache != nil && self._lexer._tokenCache!.pos == self.pos && self._lexer._cachedWordContext == self._wordContext && self._lexer._cachedAtCommandStart == self._atCommandStart && self._lexer._cachedInArrayLiteral == self._inArrayLiteral && self._lexer._cachedInAssignBuiltin == self._inAssignBuiltin {
            return self._lexer._tokenCache
        }
        var savedPos: Int = self.pos
        self._syncLexer()
        var result: Token = try self._lexer.peekToken()
        self._lexer._cachedWordContext = self._wordContext
        self._lexer._cachedAtCommandStart = self._atCommandStart
        self._lexer._cachedInArrayLiteral = self._inArrayLiteral
        self._lexer._cachedInAssignBuiltin = self._inAssignBuiltin
        self._lexer._postReadPos = self._lexer.pos
        self.pos = savedPos
        return result
    }

    func _lexNextToken() throws -> Token {
        var tok: Token? = nil
        if self._lexer._tokenCache != nil && self._lexer._tokenCache!.pos == self.pos && self._lexer._cachedWordContext == self._wordContext && self._lexer._cachedAtCommandStart == self._atCommandStart && self._lexer._cachedInArrayLiteral == self._inArrayLiteral && self._lexer._cachedInAssignBuiltin == self._inAssignBuiltin {
            tok = try self._lexer.nextToken()
            self.pos = self._lexer._postReadPos
            self._lexer.pos = self._lexer._postReadPos
        } else {
            self._syncLexer()
            tok = try self._lexer.nextToken()
            self._lexer._cachedWordContext = self._wordContext
            self._lexer._cachedAtCommandStart = self._atCommandStart
            self._lexer._cachedInArrayLiteral = self._inArrayLiteral
            self._lexer._cachedInAssignBuiltin = self._inAssignBuiltin
            self._syncParser()
        }
        self._recordToken(tok!)
        return tok!
    }

    func _lexSkipBlanks() {
        self._syncLexer()
        self._lexer.skipBlanks()
        self._syncParser()
    }

    func _lexSkipComment() -> Bool {
        self._syncLexer()
        var result: Bool = self._lexer._skipComment()
        self._syncParser()
        return result
    }

    func _lexIsCommandTerminator() throws -> Bool {
        var tok: Token = try self._lexPeekToken()
        var t: Int = tok.type
        return t == tokentypeEof || t == tokentypeNewline || t == tokentypePipe || t == tokentypeSemi || t == tokentypeLparen || t == tokentypeRparen || t == tokentypeAmp
    }

    func _lexPeekOperator() throws -> (Int, String) {
        var tok: Token = try self._lexPeekToken()
        var t: Int = tok.type
        if t >= tokentypeSemi && t <= tokentypeGreater || t >= tokentypeAndAnd && t <= tokentypePipeAmp {
            return (t, tok.value)
        }
        return (0, "")
    }

    func _lexPeekReservedWord() throws -> String {
        var tok: Token = try self._lexPeekToken()
        if tok.type != tokentypeWord {
            return ""
        }
        var word: String = tok.value
        if word.hasSuffix("\\\n") {
            word = String(word.prefix(word.count - 2))
        }
        if reservedWords.contains(word) || word == "{" || word == "}" || word == "[[" || word == "]]" || word == "!" || word == "time" {
            return word
        }
        return ""
    }

    func _lexIsAtReservedWord(_ word: String) throws -> Bool {
        var reserved: String = try self._lexPeekReservedWord()
        return reserved == word
    }

    func _lexConsumeWord(_ expected: String) throws -> Bool {
        var tok: Token = try self._lexPeekToken()
        if tok.type != tokentypeWord {
            return false
        }
        var word: String = tok.value
        if word.hasSuffix("\\\n") {
            word = String(word.prefix(word.count - 2))
        }
        if word == expected {
            try self._lexNextToken()
            return true
        }
        return false
    }

    func _lexPeekCaseTerminator() throws -> String {
        var tok: Token = try self._lexPeekToken()
        var t: Int = tok.type
        if t == tokentypeSemiSemi {
            return ";;"
        }
        if t == tokentypeSemiAmp {
            return ";&"
        }
        if t == tokentypeSemiSemiAmp {
            return ";;&"
        }
        return ""
    }

    func atEnd() -> Bool {
        return self.pos >= self.length
    }

    func peek() -> String {
        if self.atEnd() {
            return ""
        }
        return String(_charAt(self.source, self.pos))
    }

    func advance() -> String {
        if self.atEnd() {
            return ""
        }
        var ch: String = String(_charAt(self.source, self.pos))
        self.pos += 1
        return ch
    }

    func peekAt(_ offset: Int) -> String {
        var pos: Int = self.pos + offset
        if pos < 0 || pos >= self.length {
            return ""
        }
        return String(_charAt(self.source, pos))
    }

    func lookahead(_ n: Int) -> String {
        return _substring(self.source, self.pos, self.pos + n)
    }

    func _isBangFollowedByProcsub() -> Bool {
        if self.pos + 2 >= self.length {
            return false
        }
        var nextChar: String = String(_charAt(self.source, self.pos + 1))
        if nextChar != ">" && nextChar != "<" {
            return false
        }
        return String(_charAt(self.source, self.pos + 2)) == "("
    }

    func skipWhitespace() {
        while !self.atEnd() {
            self._lexSkipBlanks()
            if self.atEnd() {
                break
            }
            var ch: String = self.peek()
            if ch == "#" {
                self._lexSkipComment()
            } else {
                if ch == "\\" && self.peekAt(1) == "\n" {
                    self.advance()
                    self.advance()
                } else {
                    break
                }
            }
        }
    }

    func skipWhitespaceAndNewlines() {
        while !self.atEnd() {
            var ch: String = self.peek()
            if _isWhitespace(ch) {
                self.advance()
                if ch == "\n" {
                    self._gatherHeredocBodies()
                    if self._cmdsubHeredocEnd != -1 && self._cmdsubHeredocEnd > self.pos {
                        self.pos = self._cmdsubHeredocEnd
                        self._cmdsubHeredocEnd = -1
                    }
                }
            } else {
                if ch == "#" {
                    while !self.atEnd() && self.peek() != "\n" {
                        self.advance()
                    }
                } else {
                    if ch == "\\" && self.peekAt(1) == "\n" {
                        self.advance()
                        self.advance()
                    } else {
                        break
                    }
                }
            }
        }
    }

    func _atListTerminatingBracket() -> Bool {
        if self.atEnd() {
            return false
        }
        var ch: String = self.peek()
        if self._eofToken != "" && ch == self._eofToken {
            return true
        }
        if ch == ")" {
            return true
        }
        if ch == "}" {
            var nextPos: Int = self.pos + 1
            if nextPos >= self.length {
                return true
            }
            return _isWordEndContext(String(_charAt(self.source, nextPos)))
        }
        return false
    }

    func _atEofToken() throws -> Bool {
        if self._eofToken == "" {
            return false
        }
        var tok: Token = try self._lexPeekToken()
        if self._eofToken == ")" {
            return tok.type == tokentypeRparen
        }
        if self._eofToken == "}" {
            return tok.type == tokentypeWord && tok.value == "}"
        }
        return false
    }

    func _collectRedirects() throws -> [Node] {
        var redirects: [Node] = []
        while true {
            self.skipWhitespace()
            var redirect: Node? = try self.parseRedirect()
            if redirect == nil {
                break
            }
            redirects.append(redirect!)
        }
        return ((!redirects.isEmpty) ? redirects : nil)
    }

    func _parseLoopBody(_ context: String) throws -> Node {
        if self.peek() == "{" {
            var brace: BraceGroup? = try self.parseBraceGroup()
            if brace == nil {
                throw try ParseError(message: "Expected brace group body in \\(context)", pos: self._lexPeekToken().pos)
            }
            return brace!.body
        }
        if try self._lexConsumeWord("do") {
            var body: Node? = try self.parseListUntil(Set(["done"]))
            if body == nil {
                throw try ParseError(message: "Expected commands after 'do'", pos: self._lexPeekToken().pos)
            }
            self.skipWhitespaceAndNewlines()
            if try !self._lexConsumeWord("done") {
                throw try ParseError(message: "Expected 'done' to close \\(context)", pos: self._lexPeekToken().pos)
            }
            return body!
        }
        throw try ParseError(message: "Expected 'do' or '{' in \\(context)", pos: self._lexPeekToken().pos)
    }

    func peekWord() -> String {
        var savedPos: Int = self.pos
        self.skipWhitespace()
        if self.atEnd() || _isMetachar(self.peek()) {
            self.pos = savedPos
            return ""
        }
        var chars: [String] = []
        while !self.atEnd() && !_isMetachar(self.peek()) {
            var ch: String = self.peek()
            if _isQuote(ch) {
                break
            }
            if ch == "\\" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "\n" {
                break
            }
            if ch == "\\" && self.pos + 1 < self.length {
                chars.append(self.advance())
                chars.append(self.advance())
                continue
            }
            chars.append(self.advance())
        }
        var word: String = ""
        if (!chars.isEmpty) {
            word = chars.joined(separator: "")
        } else {
            word = ""
        }
        self.pos = savedPos
        return word
    }

    func consumeWord(_ expected: String) -> Bool {
        var savedPos: Int = self.pos
        self.skipWhitespace()
        var word: String = self.peekWord()
        var keywordWord: String = word
        var hasLeadingBrace: Bool = false
        if word != "" && self._inProcessSub && word.count > 1 && String(_charAt(word, 0)) == "}" {
            keywordWord = String(word.dropFirst(1))
            hasLeadingBrace = true
        }
        if keywordWord != expected {
            self.pos = savedPos
            return false
        }
        self.skipWhitespace()
        if hasLeadingBrace {
            self.advance()
        }
        for _ in expected {
            self.advance()
        }
        while self.peek() == "\\" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "\n" {
            self.advance()
            self.advance()
        }
        return true
    }

    func _isWordTerminator(_ ctx: Int, _ ch: String, _ bracketDepth: Int, _ parenDepth: Int) -> Bool {
        self._syncLexer()
        return self._lexer._isWordTerminator(ctx, ch, bracketDepth, parenDepth)
    }

    func _scanDoubleQuote(_ chars: [String], _ parts: [Node], _ start: Int, _ handleLineContinuation: Bool) throws {
        chars.append("\"")
        while !self.atEnd() && self.peek() != "\"" {
            var c: String = self.peek()
            if c == "\\" && self.pos + 1 < self.length {
                var nextC: String = String(_charAt(self.source, self.pos + 1))
                if handleLineContinuation && nextC == "\n" {
                    self.advance()
                    self.advance()
                } else {
                    chars.append(self.advance())
                    chars.append(self.advance())
                }
            } else {
                if c == "$" {
                    if try !self._parseDollarExpansion(chars, parts, true) {
                        chars.append(self.advance())
                    }
                } else {
                    chars.append(self.advance())
                }
            }
        }
        if self.atEnd() {
            throw ParseError(message: "Unterminated double quote", pos: start)
        }
        chars.append(self.advance())
    }

    func _parseDollarExpansion(_ chars: [String], _ parts: [Node], _ inDquote: Bool) throws -> Bool {
        var result0: Node? = nil
        var result1: String = ""
        if self.pos + 2 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" && String(_charAt(self.source, self.pos + 2)) == "(" {
            let _tuple25 = try self._parseArithmeticExpansion()
            result0 = _tuple25.0
            result1 = _tuple25.1
            if result0 != nil {
                parts.append(result0!)
                chars.append(result1)
                return true
            }
            let _tuple26 = try self._parseCommandSubstitution()
            result0 = _tuple26.0
            result1 = _tuple26.1
            if result0 != nil {
                parts.append(result0!)
                chars.append(result1)
                return true
            }
            return false
        }
        if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "[" {
            let _tuple27 = try self._parseDeprecatedArithmetic()
            result0 = _tuple27.0
            result1 = _tuple27.1
            if result0 != nil {
                parts.append(result0!)
                chars.append(result1)
                return true
            }
            return false
        }
        if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
            let _tuple28 = try self._parseCommandSubstitution()
            result0 = _tuple28.0
            result1 = _tuple28.1
            if result0 != nil {
                parts.append(result0!)
                chars.append(result1)
                return true
            }
            return false
        }
        let _tuple29 = try self._parseParamExpansion(inDquote)
        result0 = _tuple29.0
        result1 = _tuple29.1
        if result0 != nil {
            parts.append(result0!)
            chars.append(result1)
            return true
        }
        return false
    }

    func _parseWordInternal(_ ctx: Int, _ atCommandStart: Bool, _ inArrayLiteral: Bool) throws -> Word {
        self._wordContext = ctx
        return try self.parseWord(atCommandStart, inArrayLiteral, false)
    }

    func parseWord(_ atCommandStart: Bool, _ inArrayLiteral: Bool, _ inAssignBuiltin: Bool) throws -> Word? {
        self.skipWhitespace()
        if self.atEnd() {
            return nil
        }
        self._atCommandStart = atCommandStart
        self._inArrayLiteral = inArrayLiteral
        self._inAssignBuiltin = inAssignBuiltin
        var tok: Token = try self._lexPeekToken()
        if tok.type != tokentypeWord {
            self._atCommandStart = false
            self._inArrayLiteral = false
            self._inAssignBuiltin = false
            return nil
        }
        try self._lexNextToken()
        self._atCommandStart = false
        self._inArrayLiteral = false
        self._inAssignBuiltin = false
        return tok.word
    }

    func _parseCommandSubstitution() throws -> (Node?, String) {
        if self.atEnd() || self.peek() != "$" {
            return (nil, "")
        }
        var start: Int = self.pos
        self.advance()
        if self.atEnd() || self.peek() != "(" {
            self.pos = start
            return (nil, "")
        }
        self.advance()
        var saved: SavedParserState = self._saveParserState()
        self._setState(parserstateflagsPstCmdsubst | parserstateflagsPstEoftoken)
        self._eofToken = ")"
        var cmd: Node? = try self.parseList(true)
        if cmd == nil {
            cmd = Empty(kind: "empty")
        }
        self.skipWhitespaceAndNewlines()
        if self.atEnd() || self.peek() != ")" {
            self._restoreParserState(saved)
            self.pos = start
            return (nil, "")
        }
        self.advance()
        var textEnd: Int = self.pos
        var text: String = _substring(self.source, start, textEnd)
        self._restoreParserState(saved)
        return (CommandSubstitution(command: cmd!, brace: false, kind: "cmdsub"), text)
    }

    func _parseFunsub(_ start: Int) throws -> (Node?, String) {
        self._syncParser()
        if !self.atEnd() && self.peek() == "|" {
            self.advance()
        }
        var saved: SavedParserState = self._saveParserState()
        self._setState(parserstateflagsPstCmdsubst | parserstateflagsPstEoftoken)
        self._eofToken = "}"
        var cmd: Node? = try self.parseList(true)
        if cmd == nil {
            cmd = Empty(kind: "empty")
        }
        self.skipWhitespaceAndNewlines()
        if self.atEnd() || self.peek() != "}" {
            self._restoreParserState(saved)
            throw MatchedPairError(message: "unexpected EOF looking for `}'", pos: start)
        }
        self.advance()
        var text: String = _substring(self.source, start, self.pos)
        self._restoreParserState(saved)
        self._syncLexer()
        return (CommandSubstitution(command: cmd!, brace: true, kind: "cmdsub"), text)
    }

    func _isAssignmentWord(_ word: Word) -> Bool {
        return _assignment(word.value, 0) != -1
    }

    func _parseBacktickSubstitution() throws -> (Node?, String) {
        if self.atEnd() || self.peek() != "`" {
            return (nil, "")
        }
        var start: Int = self.pos
        self.advance()
        var contentChars: [String] = []
        var textChars: [String] = ["`"]
        var pendingHeredocs: [(String, Bool)] = []
        var inHeredocBody: Bool = false
        var currentHeredocDelim: String = ""
        var currentHeredocStrip: Bool = false
        var ch: String = ""
        while !self.atEnd() && inHeredocBody || self.peek() != "`" {
            if inHeredocBody {
                var lineStart: Int = self.pos
                var lineEnd: Int = lineStart
                while lineEnd < self.length && String(_charAt(self.source, lineEnd)) != "\n" {
                    lineEnd += 1
                }
                var line: String = _substring(self.source, lineStart, lineEnd)
                var checkLine: String = (currentHeredocStrip ? line.trimmingCharacters(in: CharacterSet(charactersIn: "\t")) : line)
                if checkLine == currentHeredocDelim {
                    for _c30 in line {
                        ch = String(_c30)
                        contentChars.append(ch)
                        textChars.append(ch)
                    }
                    self.pos = lineEnd
                    if self.pos < self.length && String(_charAt(self.source, self.pos)) == "\n" {
                        contentChars.append("\n")
                        textChars.append("\n")
                        self.advance()
                    }
                    inHeredocBody = false
                    if pendingHeredocs.count > 0 {
                        let _tuple31 = pendingHeredocs.removeFirst()
                        currentHeredocDelim = _tuple31.0
                        currentHeredocStrip = _tuple31.1
                        inHeredocBody = true
                    }
                } else {
                    if checkLine.hasPrefix(currentHeredocDelim) && checkLine.count > currentHeredocDelim.count {
                        var tabsStripped: Int = line.count - checkLine.count
                        var endPos: Int = tabsStripped + currentHeredocDelim.count
                        var i: Int = 0
                        while i < endPos {
                            contentChars.append(String(_charAt(line, i)))
                            textChars.append(String(_charAt(line, i)))
                            i += 1
                        }
                        self.pos = lineStart + endPos
                        inHeredocBody = false
                        if pendingHeredocs.count > 0 {
                            let _tuple32 = pendingHeredocs.removeFirst()
                            currentHeredocDelim = _tuple32.0
                            currentHeredocStrip = _tuple32.1
                            inHeredocBody = true
                        }
                    } else {
                        for _c33 in line {
                            ch = String(_c33)
                            contentChars.append(ch)
                            textChars.append(ch)
                        }
                        self.pos = lineEnd
                        if self.pos < self.length && String(_charAt(self.source, self.pos)) == "\n" {
                            contentChars.append("\n")
                            textChars.append("\n")
                            self.advance()
                        }
                    }
                }
                continue
            }
            var c: String = self.peek()
            if c == "\\" && self.pos + 1 < self.length {
                var nextC: String = String(_charAt(self.source, self.pos + 1))
                if nextC == "\n" {
                    self.advance()
                    self.advance()
                } else {
                    if _isEscapeCharInBacktick(nextC) {
                        self.advance()
                        var escaped: String = self.advance()
                        contentChars.append(escaped)
                        textChars.append("\\")
                        textChars.append(escaped)
                    } else {
                        ch = self.advance()
                        contentChars.append(ch)
                        textChars.append(ch)
                    }
                }
                continue
            }
            if c == "<" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "<" {
                var quote: String = ""
                if self.pos + 2 < self.length && String(_charAt(self.source, self.pos + 2)) == "<" {
                    contentChars.append(self.advance())
                    textChars.append("<")
                    contentChars.append(self.advance())
                    textChars.append("<")
                    contentChars.append(self.advance())
                    textChars.append("<")
                    while !self.atEnd() && _isWhitespaceNoNewline(self.peek()) {
                        ch = self.advance()
                        contentChars.append(ch)
                        textChars.append(ch)
                    }
                    while !self.atEnd() && !_isWhitespace(self.peek()) && !"()".contains(self.peek()) {
                        if self.peek() == "\\" && self.pos + 1 < self.length {
                            ch = self.advance()
                            contentChars.append(ch)
                            textChars.append(ch)
                            ch = self.advance()
                            contentChars.append(ch)
                            textChars.append(ch)
                        } else {
                            if "\"'".contains(self.peek()) {
                                quote = self.peek()
                                ch = self.advance()
                                contentChars.append(ch)
                                textChars.append(ch)
                                while !self.atEnd() && self.peek() != quote {
                                    if quote == "\"" && self.peek() == "\\" {
                                        ch = self.advance()
                                        contentChars.append(ch)
                                        textChars.append(ch)
                                    }
                                    ch = self.advance()
                                    contentChars.append(ch)
                                    textChars.append(ch)
                                }
                                if !self.atEnd() {
                                    ch = self.advance()
                                    contentChars.append(ch)
                                    textChars.append(ch)
                                }
                            } else {
                                ch = self.advance()
                                contentChars.append(ch)
                                textChars.append(ch)
                            }
                        }
                    }
                    continue
                }
                contentChars.append(self.advance())
                textChars.append("<")
                contentChars.append(self.advance())
                textChars.append("<")
                var stripTabs: Bool = false
                if !self.atEnd() && self.peek() == "-" {
                    stripTabs = true
                    contentChars.append(self.advance())
                    textChars.append("-")
                }
                while !self.atEnd() && _isWhitespaceNoNewline(self.peek()) {
                    ch = self.advance()
                    contentChars.append(ch)
                    textChars.append(ch)
                }
                var delimiterChars: [String] = []
                if !self.atEnd() {
                    ch = self.peek()
                    var dch: String = ""
                    var closing: String = ""
                    if _isQuote(ch) {
                        quote = self.advance()
                        contentChars.append(quote)
                        textChars.append(quote)
                        while !self.atEnd() && self.peek() != quote {
                            dch = self.advance()
                            contentChars.append(dch)
                            textChars.append(dch)
                            delimiterChars.append(dch)
                        }
                        if !self.atEnd() {
                            closing = self.advance()
                            contentChars.append(closing)
                            textChars.append(closing)
                        }
                    } else {
                        var esc: String = ""
                        if ch == "\\" {
                            esc = self.advance()
                            contentChars.append(esc)
                            textChars.append(esc)
                            if !self.atEnd() {
                                dch = self.advance()
                                contentChars.append(dch)
                                textChars.append(dch)
                                delimiterChars.append(dch)
                            }
                            while !self.atEnd() && !_isMetachar(self.peek()) {
                                dch = self.advance()
                                contentChars.append(dch)
                                textChars.append(dch)
                                delimiterChars.append(dch)
                            }
                        } else {
                            while !self.atEnd() && !_isMetachar(self.peek()) && self.peek() != "`" {
                                ch = self.peek()
                                if _isQuote(ch) {
                                    quote = self.advance()
                                    contentChars.append(quote)
                                    textChars.append(quote)
                                    while !self.atEnd() && self.peek() != quote {
                                        dch = self.advance()
                                        contentChars.append(dch)
                                        textChars.append(dch)
                                        delimiterChars.append(dch)
                                    }
                                    if !self.atEnd() {
                                        closing = self.advance()
                                        contentChars.append(closing)
                                        textChars.append(closing)
                                    }
                                } else {
                                    if ch == "\\" {
                                        esc = self.advance()
                                        contentChars.append(esc)
                                        textChars.append(esc)
                                        if !self.atEnd() {
                                            dch = self.advance()
                                            contentChars.append(dch)
                                            textChars.append(dch)
                                            delimiterChars.append(dch)
                                        }
                                    } else {
                                        dch = self.advance()
                                        contentChars.append(dch)
                                        textChars.append(dch)
                                        delimiterChars.append(dch)
                                    }
                                }
                            }
                        }
                    }
                }
                var delimiter: String = delimiterChars.joined(separator: "")
                if (!delimiter.isEmpty) {
                    pendingHeredocs.append((delimiter, stripTabs))
                }
                continue
            }
            if c == "\n" {
                ch = self.advance()
                contentChars.append(ch)
                textChars.append(ch)
                if pendingHeredocs.count > 0 {
                    let _tuple34 = pendingHeredocs.removeFirst()
                    currentHeredocDelim = _tuple34.0
                    currentHeredocStrip = _tuple34.1
                    inHeredocBody = true
                }
                continue
            }
            ch = self.advance()
            contentChars.append(ch)
            textChars.append(ch)
        }
        if self.atEnd() {
            throw ParseError(message: "Unterminated backtick", pos: start)
        }
        self.advance()
        textChars.append("`")
        var text: String = textChars.joined(separator: "")
        var content: String = contentChars.joined(separator: "")
        if pendingHeredocs.count > 0 {
            let _tuple35 = _findHeredocContentEnd(self.source, self.pos, pendingHeredocs)
            var heredocStart: Int = _tuple35.0
            var heredocEnd: Int = _tuple35.1
            if heredocEnd > heredocStart {
                content = content + _substring(self.source, heredocStart, heredocEnd)
                if self._cmdsubHeredocEnd == -1 {
                    self._cmdsubHeredocEnd = heredocEnd
                } else {
                    self._cmdsubHeredocEnd = (self._cmdsubHeredocEnd > heredocEnd ? self._cmdsubHeredocEnd : heredocEnd)
                }
            }
        }
        var subParser: Parser = newParser(content, false, self._extglob)
        var cmd: Node? = try subParser.parseList(true)
        if cmd == nil {
            cmd = Empty(kind: "empty")
        }
        return (CommandSubstitution(command: cmd!, brace: false, kind: "cmdsub"), text)
    }

    func _parseProcessSubstitution() throws -> (Node?, String) {
        if self.atEnd() || !_isRedirectChar(self.peek()) {
            return (nil, "")
        }
        var start: Int = self.pos
        var direction: String = self.advance()
        if self.atEnd() || self.peek() != "(" {
            self.pos = start
            return (nil, "")
        }
        self.advance()
        var saved: SavedParserState = self._saveParserState()
        var oldInProcessSub: Bool = self._inProcessSub
        self._inProcessSub = true
        self._setState(parserstateflagsPstEoftoken)
        self._eofToken = ")"
        do {
            var cmd: Node? = try self.parseList(true)
            if cmd == nil {
                cmd = Empty(kind: "empty")
            }
            self.skipWhitespaceAndNewlines()
            if self.atEnd() || self.peek() != ")" {
                throw ParseError(message: "Invalid process substitution", pos: start)
            }
            self.advance()
            var textEnd: Int = self.pos
            var text: String = _substring(self.source, start, textEnd)
            text = _stripLineContinuationsCommentAware(text)
            self._restoreParserState(saved)
            self._inProcessSub = oldInProcessSub
            return (ProcessSubstitution(direction: direction, command: cmd!, kind: "procsub"), text)
        } catch is ParseError {
            self._restoreParserState(saved)
            self._inProcessSub = oldInProcessSub
            var contentStartChar: String = (start + 2 < self.length ? String(_charAt(self.source, start + 2)) : "")
            if " \t\n".contains(contentStartChar) {
                throw e
            }
            self.pos = start + 2
            self._lexer.pos = self.pos
            try self._lexer._parseMatchedPair("(", ")", 0, false)
            self.pos = self._lexer.pos
            var text: String = _substring(self.source, start, self.pos)
            text = _stripLineContinuationsCommentAware(text)
            return (nil, text)
        }
    }

    func _parseArrayLiteral() throws -> (Node?, String) {
        if self.atEnd() || self.peek() != "(" {
            return (nil, "")
        }
        var start: Int = self.pos
        self.advance()
        self._setState(parserstateflagsPstCompassign)
        var elements: [Word] = []
        while true {
            self.skipWhitespaceAndNewlines()
            if self.atEnd() {
                self._clearState(parserstateflagsPstCompassign)
                throw ParseError(message: "Unterminated array literal", pos: start)
            }
            if self.peek() == ")" {
                break
            }
            var word: Word? = try self.parseWord(false, true, false)
            if word == nil {
                if self.peek() == ")" {
                    break
                }
                self._clearState(parserstateflagsPstCompassign)
                throw ParseError(message: "Expected word in array literal", pos: self.pos)
            }
            elements.append(word!)
        }
        if self.atEnd() || self.peek() != ")" {
            self._clearState(parserstateflagsPstCompassign)
            throw ParseError(message: "Expected ) to close array literal", pos: self.pos)
        }
        self.advance()
        var text: String = _substring(self.source, start, self.pos)
        self._clearState(parserstateflagsPstCompassign)
        return (`Array`(elements: elements, kind: "array"), text)
    }

    func _parseArithmeticExpansion() throws -> (Node?, String) {
        if self.atEnd() || self.peek() != "$" {
            return (nil, "")
        }
        var start: Int = self.pos
        if self.pos + 2 >= self.length || String(_charAt(self.source, self.pos + 1)) != "(" || String(_charAt(self.source, self.pos + 2)) != "(" {
            return (nil, "")
        }
        self.advance()
        self.advance()
        self.advance()
        var contentStart: Int = self.pos
        var depth: Int = 2
        var firstClosePos: Int = -1
        while !self.atEnd() && depth > 0 {
            var c: String = self.peek()
            if c == "'" {
                self.advance()
                while !self.atEnd() && self.peek() != "'" {
                    self.advance()
                }
                if !self.atEnd() {
                    self.advance()
                }
            } else {
                if c == "\"" {
                    self.advance()
                    while !self.atEnd() {
                        if self.peek() == "\\" && self.pos + 1 < self.length {
                            self.advance()
                            self.advance()
                        } else {
                            if self.peek() == "\"" {
                                self.advance()
                                break
                            } else {
                                self.advance()
                            }
                        }
                    }
                } else {
                    if c == "\\" && self.pos + 1 < self.length {
                        self.advance()
                        self.advance()
                    } else {
                        if c == "(" {
                            depth += 1
                            self.advance()
                        } else {
                            if c == ")" {
                                if depth == 2 {
                                    firstClosePos = self.pos
                                }
                                depth -= 1
                                if depth == 0 {
                                    break
                                }
                                self.advance()
                            } else {
                                if depth == 1 {
                                    firstClosePos = -1
                                }
                                self.advance()
                            }
                        }
                    }
                }
            }
        }
        if depth != 0 {
            if self.atEnd() {
                throw MatchedPairError(message: "unexpected EOF looking for `))'", pos: start)
            }
            self.pos = start
            return (nil, "")
        }
        var content: String = ""
        if firstClosePos != -1 {
            content = _substring(self.source, contentStart, firstClosePos)
        } else {
            content = _substring(self.source, contentStart, self.pos)
        }
        self.advance()
        var text: String = _substring(self.source, start, self.pos)
        var expr: Node? = nil
        do {
            expr = self._parseArithExpr(content)
        } catch is ParseError {
            self.pos = start
            return (nil, "")
        }
        return (ArithmeticExpansion(expression: expr!, kind: "arith"), text)
    }

    func _parseArithExpr(_ content: String) -> Node {
        var savedArithSrc: String = self._arithSrc
        var savedArithPos: Int = self._arithPos
        var savedArithLen: Int = self._arithLen
        var savedParserState: Int = self._parserState
        self._setState(parserstateflagsPstArith)
        self._arithSrc = content
        self._arithPos = 0
        self._arithLen = content.count
        self._arithSkipWs()
        var result: Node? = nil
        if self._arithAtEnd() {
            result = nil
        } else {
            result = self._arithParseComma()
        }
        self._parserState = savedParserState
        if savedArithSrc != "" {
            self._arithSrc = savedArithSrc
            self._arithPos = savedArithPos
            self._arithLen = savedArithLen
        }
        return result!
    }

    func _arithAtEnd() -> Bool {
        return self._arithPos >= self._arithLen
    }

    func _arithPeek(_ offset: Int) -> String {
        var pos: Int = self._arithPos + offset
        if pos >= self._arithLen {
            return ""
        }
        return String(_charAt(self._arithSrc, pos))
    }

    func _arithAdvance() -> String {
        if self._arithAtEnd() {
            return ""
        }
        var c: String = String(_charAt(self._arithSrc, self._arithPos))
        self._arithPos += 1
        return c
    }

    func _arithSkipWs() {
        while !self._arithAtEnd() {
            var c: String = String(_charAt(self._arithSrc, self._arithPos))
            if _isWhitespace(c) {
                self._arithPos += 1
            } else {
                if c == "\\" && self._arithPos + 1 < self._arithLen && String(_charAt(self._arithSrc, self._arithPos + 1)) == "\n" {
                    self._arithPos += 2
                } else {
                    break
                }
            }
        }
    }

    func _arithMatch(_ s: String) -> Bool {
        return _startsWithAt(self._arithSrc, self._arithPos, s)
    }

    func _arithConsume(_ s: String) -> Bool {
        if self._arithMatch(s) {
            self._arithPos += s.count
            return true
        }
        return false
    }

    func _arithParseComma() -> Node {
        var `left`: Node = self._arithParseAssign()
        while true {
            self._arithSkipWs()
            if self._arithConsume(",") {
                self._arithSkipWs()
                var `right`: Node = self._arithParseAssign()
                `left` = ArithComma(`left`: `left`, `right`: `right`, kind: "comma")
            } else {
                break
            }
        }
        return `left`
    }

    func _arithParseAssign() -> Node {
        var `left`: Node = self._arithParseTernary()
        self._arithSkipWs()
        var assignOps: [String] = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="]
        for op in assignOps {
            if self._arithMatch(op) {
                if op == "=" && self._arithPeek(1) == "=" {
                    break
                }
                self._arithConsume(op)
                self._arithSkipWs()
                var `right`: Node = self._arithParseAssign()
                return ArithAssign(op: op, target: `left`, value: `right`, kind: "assign")
            }
        }
        return `left`
    }

    func _arithParseTernary() -> Node {
        var cond: Node = self._arithParseLogicalOr()
        self._arithSkipWs()
        if self._arithConsume("?") {
            self._arithSkipWs()
            var ifTrue: Node? = nil
            if self._arithMatch(":") {
                ifTrue = nil
            } else {
                ifTrue = self._arithParseAssign()
            }
            self._arithSkipWs()
            var ifFalse: Node? = nil
            if self._arithConsume(":") {
                self._arithSkipWs()
                if self._arithAtEnd() || self._arithPeek(0) == ")" {
                    ifFalse = nil
                } else {
                    ifFalse = self._arithParseTernary()
                }
            } else {
                ifFalse = nil
            }
            return ArithTernary(condition: cond, ifTrue: ifTrue!, ifFalse: ifFalse!, kind: "ternary")
        }
        return cond
    }

    func _arithParseLeftAssoc(_ ops: [String], _ parsefn: () throws -> Node) -> Node {
        var `left`: Node = try parsefn()
        while true {
            self._arithSkipWs()
            var matched: Bool = false
            for op in ops {
                if self._arithMatch(op) {
                    self._arithConsume(op)
                    self._arithSkipWs()
                    `left` = try ArithBinaryOp(op: op, `left`: `left`, `right`: parsefn(), kind: "binary-op")
                    matched = true
                    break
                }
            }
            if !matched {
                break
            }
        }
        return `left`
    }

    func _arithParseLogicalOr() -> Node {
        return self._arithParseLeftAssoc(["||"], self._arithParseLogicalAnd)
    }

    func _arithParseLogicalAnd() -> Node {
        return self._arithParseLeftAssoc(["&&"], self._arithParseBitwiseOr)
    }

    func _arithParseBitwiseOr() -> Node {
        var `left`: Node = self._arithParseBitwiseXor()
        while true {
            self._arithSkipWs()
            if self._arithPeek(0) == "|" && self._arithPeek(1) != "|" && self._arithPeek(1) != "=" {
                self._arithAdvance()
                self._arithSkipWs()
                var `right`: Node = self._arithParseBitwiseXor()
                `left` = ArithBinaryOp(op: "|", `left`: `left`, `right`: `right`, kind: "binary-op")
            } else {
                break
            }
        }
        return `left`
    }

    func _arithParseBitwiseXor() -> Node {
        var `left`: Node = self._arithParseBitwiseAnd()
        while true {
            self._arithSkipWs()
            if self._arithPeek(0) == "^" && self._arithPeek(1) != "=" {
                self._arithAdvance()
                self._arithSkipWs()
                var `right`: Node = self._arithParseBitwiseAnd()
                `left` = ArithBinaryOp(op: "^", `left`: `left`, `right`: `right`, kind: "binary-op")
            } else {
                break
            }
        }
        return `left`
    }

    func _arithParseBitwiseAnd() -> Node {
        var `left`: Node = self._arithParseEquality()
        while true {
            self._arithSkipWs()
            if self._arithPeek(0) == "&" && self._arithPeek(1) != "&" && self._arithPeek(1) != "=" {
                self._arithAdvance()
                self._arithSkipWs()
                var `right`: Node = self._arithParseEquality()
                `left` = ArithBinaryOp(op: "&", `left`: `left`, `right`: `right`, kind: "binary-op")
            } else {
                break
            }
        }
        return `left`
    }

    func _arithParseEquality() -> Node {
        return self._arithParseLeftAssoc(["==", "!="], self._arithParseComparison)
    }

    func _arithParseComparison() throws -> Node {
        var `left`: Node = try self._arithParseShift()
        while true {
            self._arithSkipWs()
            var `right`: Node? = nil
            if self._arithMatch("<=") {
                self._arithConsume("<=")
                self._arithSkipWs()
                `right` = try self._arithParseShift()
                `left` = ArithBinaryOp(op: "<=", `left`: `left`, `right`: `right`!, kind: "binary-op")
            } else {
                if self._arithMatch(">=") {
                    self._arithConsume(">=")
                    self._arithSkipWs()
                    `right` = try self._arithParseShift()
                    `left` = ArithBinaryOp(op: ">=", `left`: `left`, `right`: `right`!, kind: "binary-op")
                } else {
                    if self._arithPeek(0) == "<" && self._arithPeek(1) != "<" && self._arithPeek(1) != "=" {
                        self._arithAdvance()
                        self._arithSkipWs()
                        `right` = try self._arithParseShift()
                        `left` = ArithBinaryOp(op: "<", `left`: `left`, `right`: `right`!, kind: "binary-op")
                    } else {
                        if self._arithPeek(0) == ">" && self._arithPeek(1) != ">" && self._arithPeek(1) != "=" {
                            self._arithAdvance()
                            self._arithSkipWs()
                            `right` = try self._arithParseShift()
                            `left` = ArithBinaryOp(op: ">", `left`: `left`, `right`: `right`!, kind: "binary-op")
                        } else {
                            break
                        }
                    }
                }
            }
        }
        return `left`
    }

    func _arithParseShift() throws -> Node {
        var `left`: Node = try self._arithParseAdditive()
        while true {
            self._arithSkipWs()
            if self._arithMatch("<<=") {
                break
            }
            if self._arithMatch(">>=") {
                break
            }
            var `right`: Node? = nil
            if self._arithMatch("<<") {
                self._arithConsume("<<")
                self._arithSkipWs()
                `right` = try self._arithParseAdditive()
                `left` = ArithBinaryOp(op: "<<", `left`: `left`, `right`: `right`!, kind: "binary-op")
            } else {
                if self._arithMatch(">>") {
                    self._arithConsume(">>")
                    self._arithSkipWs()
                    `right` = try self._arithParseAdditive()
                    `left` = ArithBinaryOp(op: ">>", `left`: `left`, `right`: `right`!, kind: "binary-op")
                } else {
                    break
                }
            }
        }
        return `left`
    }

    func _arithParseAdditive() throws -> Node {
        var `left`: Node = try self._arithParseMultiplicative()
        while true {
            self._arithSkipWs()
            var c: String = self._arithPeek(0)
            var c2: String = self._arithPeek(1)
            var `right`: Node? = nil
            if c == "+" && c2 != "+" && c2 != "=" {
                self._arithAdvance()
                self._arithSkipWs()
                `right` = try self._arithParseMultiplicative()
                `left` = ArithBinaryOp(op: "+", `left`: `left`, `right`: `right`!, kind: "binary-op")
            } else {
                if c == "-" && c2 != "-" && c2 != "=" {
                    self._arithAdvance()
                    self._arithSkipWs()
                    `right` = try self._arithParseMultiplicative()
                    `left` = ArithBinaryOp(op: "-", `left`: `left`, `right`: `right`!, kind: "binary-op")
                } else {
                    break
                }
            }
        }
        return `left`
    }

    func _arithParseMultiplicative() throws -> Node {
        var `left`: Node = try self._arithParseExponentiation()
        while true {
            self._arithSkipWs()
            var c: String = self._arithPeek(0)
            var c2: String = self._arithPeek(1)
            var `right`: Node? = nil
            if c == "*" && c2 != "*" && c2 != "=" {
                self._arithAdvance()
                self._arithSkipWs()
                `right` = try self._arithParseExponentiation()
                `left` = ArithBinaryOp(op: "*", `left`: `left`, `right`: `right`!, kind: "binary-op")
            } else {
                if c == "/" && c2 != "=" {
                    self._arithAdvance()
                    self._arithSkipWs()
                    `right` = try self._arithParseExponentiation()
                    `left` = ArithBinaryOp(op: "/", `left`: `left`, `right`: `right`!, kind: "binary-op")
                } else {
                    if c == "%" && c2 != "=" {
                        self._arithAdvance()
                        self._arithSkipWs()
                        `right` = try self._arithParseExponentiation()
                        `left` = ArithBinaryOp(op: "%", `left`: `left`, `right`: `right`!, kind: "binary-op")
                    } else {
                        break
                    }
                }
            }
        }
        return `left`
    }

    func _arithParseExponentiation() throws -> Node {
        var `left`: Node = try self._arithParseUnary()
        self._arithSkipWs()
        if self._arithMatch("**") {
            self._arithConsume("**")
            self._arithSkipWs()
            var `right`: Node = try self._arithParseExponentiation()
            return ArithBinaryOp(op: "**", `left`: `left`, `right`: `right`, kind: "binary-op")
        }
        return `left`
    }

    func _arithParseUnary() throws -> Node {
        self._arithSkipWs()
        var operand: Node? = nil
        if self._arithMatch("++") {
            self._arithConsume("++")
            self._arithSkipWs()
            operand = try self._arithParseUnary()
            return ArithPreIncr(operand: operand!, kind: "pre-incr")
        }
        if self._arithMatch("--") {
            self._arithConsume("--")
            self._arithSkipWs()
            operand = try self._arithParseUnary()
            return ArithPreDecr(operand: operand!, kind: "pre-decr")
        }
        var c: String = self._arithPeek(0)
        if c == "!" {
            self._arithAdvance()
            self._arithSkipWs()
            operand = try self._arithParseUnary()
            return ArithUnaryOp(op: "!", operand: operand!, kind: "unary-op")
        }
        if c == "~" {
            self._arithAdvance()
            self._arithSkipWs()
            operand = try self._arithParseUnary()
            return ArithUnaryOp(op: "~", operand: operand!, kind: "unary-op")
        }
        if c == "+" && self._arithPeek(1) != "+" {
            self._arithAdvance()
            self._arithSkipWs()
            operand = try self._arithParseUnary()
            return ArithUnaryOp(op: "+", operand: operand!, kind: "unary-op")
        }
        if c == "-" && self._arithPeek(1) != "-" {
            self._arithAdvance()
            self._arithSkipWs()
            operand = try self._arithParseUnary()
            return ArithUnaryOp(op: "-", operand: operand!, kind: "unary-op")
        }
        return try self._arithParsePostfix()
    }

    func _arithParsePostfix() throws -> Node {
        var `left`: Node = try self._arithParsePrimary()
        while true {
            self._arithSkipWs()
            if self._arithMatch("++") {
                self._arithConsume("++")
                `left` = ArithPostIncr(operand: `left`, kind: "post-incr")
            } else {
                if self._arithMatch("--") {
                    self._arithConsume("--")
                    `left` = ArithPostDecr(operand: `left`, kind: "post-decr")
                } else {
                    if self._arithPeek(0) == "[" {
                        switch `left` {
                        case let `left` as ArithVar:
                            self._arithAdvance()
                            self._arithSkipWs()
                            var index: Node = self._arithParseComma()
                            self._arithSkipWs()
                            if !self._arithConsume("]") {
                                throw ParseError(message: "Expected ']' in array subscript", pos: self._arithPos)
                            }
                            `left` = ArithSubscript(array: `left`.name, index: index, kind: "subscript")
                        default:
                            break
                        }
                    } else {
                        break
                    }
                }
            }
        }
        return `left`
    }

    func _arithParsePrimary() throws -> Node {
        self._arithSkipWs()
        var c: String = self._arithPeek(0)
        if c == "(" {
            self._arithAdvance()
            self._arithSkipWs()
            var expr: Node = self._arithParseComma()
            self._arithSkipWs()
            if !self._arithConsume(")") {
                throw ParseError(message: "Expected ')' in arithmetic expression", pos: self._arithPos)
            }
            return expr
        }
        if c == "#" && self._arithPeek(1) == "$" {
            self._arithAdvance()
            return try self._arithParseExpansion()
        }
        if c == "$" {
            return try self._arithParseExpansion()
        }
        if c == "'" {
            return try self._arithParseSingleQuote()
        }
        if c == "\"" {
            return try self._arithParseDoubleQuote()
        }
        if c == "`" {
            return try self._arithParseBacktick()
        }
        if c == "\\" {
            self._arithAdvance()
            if self._arithAtEnd() {
                throw ParseError(message: "Unexpected end after backslash in arithmetic", pos: self._arithPos)
            }
            var escapedChar: String = self._arithAdvance()
            return ArithEscape(char: escapedChar, kind: "escape")
        }
        if self._arithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".contains(c) {
            return ArithEmpty(kind: "empty")
        }
        return try self._arithParseNumberOrVar()
    }

    func _arithParseExpansion() throws -> Node {
        if !self._arithConsume("$") {
            throw ParseError(message: "Expected '$'", pos: self._arithPos)
        }
        var c: String = self._arithPeek(0)
        if c == "(" {
            return try self._arithParseCmdsub()
        }
        if c == "{" {
            return self._arithParseBracedParam()
        }
        var nameChars: [String] = []
        while !self._arithAtEnd() {
            var ch: String = self._arithPeek(0)
            if (ch.first?.isLetter ?? false || ch.first?.isNumber ?? false) || ch == "_" {
                nameChars.append(self._arithAdvance())
            } else {
                if _isSpecialParamOrDigit(ch) || ch == "#" && !(!nameChars.isEmpty) {
                    nameChars.append(self._arithAdvance())
                    break
                } else {
                    break
                }
            }
        }
        if !(!nameChars.isEmpty) {
            throw ParseError(message: "Expected variable name after $", pos: self._arithPos)
        }
        return ParamExpansion(param: nameChars.joined(separator: ""), op: "", arg: "", kind: "param")
    }

    func _arithParseCmdsub() throws -> Node {
        self._arithAdvance()
        var depth: Int = 0
        var contentStart: Int = 0
        var ch: String = ""
        var content: String = ""
        if self._arithPeek(0) == "(" {
            self._arithAdvance()
            depth = 1
            contentStart = self._arithPos
            while !self._arithAtEnd() && depth > 0 {
                ch = self._arithPeek(0)
                if ch == "(" {
                    depth += 1
                    self._arithAdvance()
                } else {
                    if ch == ")" {
                        if depth == 1 && self._arithPeek(1) == ")" {
                            break
                        }
                        depth -= 1
                        self._arithAdvance()
                    } else {
                        self._arithAdvance()
                    }
                }
            }
            content = _substring(self._arithSrc, contentStart, self._arithPos)
            self._arithAdvance()
            self._arithAdvance()
            var innerExpr: Node = self._parseArithExpr(content)
            return ArithmeticExpansion(expression: innerExpr, kind: "arith")
        }
        depth = 1
        contentStart = self._arithPos
        while !self._arithAtEnd() && depth > 0 {
            ch = self._arithPeek(0)
            if ch == "(" {
                depth += 1
                self._arithAdvance()
            } else {
                if ch == ")" {
                    depth -= 1
                    if depth == 0 {
                        break
                    }
                    self._arithAdvance()
                } else {
                    self._arithAdvance()
                }
            }
        }
        content = _substring(self._arithSrc, contentStart, self._arithPos)
        self._arithAdvance()
        var subParser: Parser = newParser(content, false, self._extglob)
        var cmd: Node? = try subParser.parseList(true)
        return CommandSubstitution(command: cmd!, brace: false, kind: "cmdsub")
    }

    func _arithParseBracedParam() -> Node {
        self._arithAdvance()
        var nameChars: [String] = []
        if self._arithPeek(0) == "!" {
            self._arithAdvance()
            nameChars = []
            while !self._arithAtEnd() && self._arithPeek(0) != "}" {
                nameChars.append(self._arithAdvance())
            }
            self._arithConsume("}")
            return ParamIndirect(param: nameChars.joined(separator: ""), op: "", arg: "", kind: "param-indirect")
        }
        if self._arithPeek(0) == "#" {
            self._arithAdvance()
            nameChars = []
            while !self._arithAtEnd() && self._arithPeek(0) != "}" {
                nameChars.append(self._arithAdvance())
            }
            self._arithConsume("}")
            return ParamLength(param: nameChars.joined(separator: ""), kind: "param-len")
        }
        nameChars = []
        var ch: String = ""
        while !self._arithAtEnd() {
            ch = self._arithPeek(0)
            if ch == "}" {
                self._arithAdvance()
                return ParamExpansion(param: nameChars.joined(separator: ""), op: "", arg: "", kind: "param")
            }
            if _isParamExpansionOp(ch) {
                break
            }
            nameChars.append(self._arithAdvance())
        }
        var name: String = nameChars.joined(separator: "")
        var opChars: [String] = []
        var depth: Int = 1
        while !self._arithAtEnd() && depth > 0 {
            ch = self._arithPeek(0)
            if ch == "{" {
                depth += 1
                opChars.append(self._arithAdvance())
            } else {
                if ch == "}" {
                    depth -= 1
                    if depth == 0 {
                        break
                    }
                    opChars.append(self._arithAdvance())
                } else {
                    opChars.append(self._arithAdvance())
                }
            }
        }
        self._arithConsume("}")
        var opStr: String = opChars.joined(separator: "")
        if opStr.hasPrefix(":-") {
            return ParamExpansion(param: name, op: ":-", arg: _substring(opStr, 2, opStr.count), kind: "param")
        }
        if opStr.hasPrefix(":=") {
            return ParamExpansion(param: name, op: ":=", arg: _substring(opStr, 2, opStr.count), kind: "param")
        }
        if opStr.hasPrefix(":+") {
            return ParamExpansion(param: name, op: ":+", arg: _substring(opStr, 2, opStr.count), kind: "param")
        }
        if opStr.hasPrefix(":?") {
            return ParamExpansion(param: name, op: ":?", arg: _substring(opStr, 2, opStr.count), kind: "param")
        }
        if opStr.hasPrefix(":") {
            return ParamExpansion(param: name, op: ":", arg: _substring(opStr, 1, opStr.count), kind: "param")
        }
        if opStr.hasPrefix("##") {
            return ParamExpansion(param: name, op: "##", arg: _substring(opStr, 2, opStr.count), kind: "param")
        }
        if opStr.hasPrefix("#") {
            return ParamExpansion(param: name, op: "#", arg: _substring(opStr, 1, opStr.count), kind: "param")
        }
        if opStr.hasPrefix("%%") {
            return ParamExpansion(param: name, op: "%%", arg: _substring(opStr, 2, opStr.count), kind: "param")
        }
        if opStr.hasPrefix("%") {
            return ParamExpansion(param: name, op: "%", arg: _substring(opStr, 1, opStr.count), kind: "param")
        }
        if opStr.hasPrefix("//") {
            return ParamExpansion(param: name, op: "//", arg: _substring(opStr, 2, opStr.count), kind: "param")
        }
        if opStr.hasPrefix("/") {
            return ParamExpansion(param: name, op: "/", arg: _substring(opStr, 1, opStr.count), kind: "param")
        }
        return ParamExpansion(param: name, op: "", arg: opStr, kind: "param")
    }

    func _arithParseSingleQuote() throws -> Node {
        self._arithAdvance()
        var contentStart: Int = self._arithPos
        while !self._arithAtEnd() && self._arithPeek(0) != "'" {
            self._arithAdvance()
        }
        var content: String = _substring(self._arithSrc, contentStart, self._arithPos)
        if !self._arithConsume("'") {
            throw ParseError(message: "Unterminated single quote in arithmetic", pos: self._arithPos)
        }
        return ArithNumber(value: content, kind: "number")
    }

    func _arithParseDoubleQuote() throws -> Node {
        self._arithAdvance()
        var contentStart: Int = self._arithPos
        while !self._arithAtEnd() && self._arithPeek(0) != "\"" {
            var c: String = self._arithPeek(0)
            if c == "\\" && !self._arithAtEnd() {
                self._arithAdvance()
                self._arithAdvance()
            } else {
                self._arithAdvance()
            }
        }
        var content: String = _substring(self._arithSrc, contentStart, self._arithPos)
        if !self._arithConsume("\"") {
            throw ParseError(message: "Unterminated double quote in arithmetic", pos: self._arithPos)
        }
        return ArithNumber(value: content, kind: "number")
    }

    func _arithParseBacktick() throws -> Node {
        self._arithAdvance()
        var contentStart: Int = self._arithPos
        while !self._arithAtEnd() && self._arithPeek(0) != "`" {
            var c: String = self._arithPeek(0)
            if c == "\\" && !self._arithAtEnd() {
                self._arithAdvance()
                self._arithAdvance()
            } else {
                self._arithAdvance()
            }
        }
        var content: String = _substring(self._arithSrc, contentStart, self._arithPos)
        if !self._arithConsume("`") {
            throw ParseError(message: "Unterminated backtick in arithmetic", pos: self._arithPos)
        }
        var subParser: Parser = newParser(content, false, self._extglob)
        var cmd: Node? = try subParser.parseList(true)
        return CommandSubstitution(command: cmd!, brace: false, kind: "cmdsub")
    }

    func _arithParseNumberOrVar() throws -> Node {
        self._arithSkipWs()
        var chars: [String] = []
        var c: String = self._arithPeek(0)
        var ch: String = ""
        if (c.first?.isNumber ?? false) {
            while !self._arithAtEnd() {
                ch = self._arithPeek(0)
                if (ch.first?.isLetter ?? false || ch.first?.isNumber ?? false) || ch == "#" || ch == "_" {
                    chars.append(self._arithAdvance())
                } else {
                    break
                }
            }
            var `prefix`: String = chars.joined(separator: "")
            if !self._arithAtEnd() && self._arithPeek(0) == "$" {
                var expansion: Node = try self._arithParseExpansion()
                return ArithConcat(parts: [ArithNumber(value: `prefix`, kind: "number"), expansion], kind: "arith-concat")
            }
            return ArithNumber(value: `prefix`, kind: "number")
        }
        if (c.first?.isLetter ?? false) || c == "_" {
            while !self._arithAtEnd() {
                ch = self._arithPeek(0)
                if (ch.first?.isLetter ?? false || ch.first?.isNumber ?? false) || ch == "_" {
                    chars.append(self._arithAdvance())
                } else {
                    break
                }
            }
            return ArithVar(name: chars.joined(separator: ""), kind: "var")
        }
        throw ParseError(message: "Unexpected character '" + c + "' in arithmetic expression", pos: self._arithPos)
    }

    func _parseDeprecatedArithmetic() throws -> (Node?, String) {
        if self.atEnd() || self.peek() != "$" {
            return (nil, "")
        }
        var start: Int = self.pos
        if self.pos + 1 >= self.length || String(_charAt(self.source, self.pos + 1)) != "[" {
            return (nil, "")
        }
        self.advance()
        self.advance()
        self._lexer.pos = self.pos
        var content: String = try self._lexer._parseMatchedPair("[", "]", matchedpairflagsArith, false)
        self.pos = self._lexer.pos
        var text: String = _substring(self.source, start, self.pos)
        return (ArithDeprecated(expression: content, kind: "arith-deprecated"), text)
    }

    func _parseParamExpansion(_ inDquote: Bool) throws -> (Node?, String) {
        self._syncLexer()
        let _tuple36 = try self._lexer._readParamExpansion(inDquote)
        var result0: Node? = _tuple36.0
        var result1: String = _tuple36.1
        self._syncParser()
        return (result0!, result1)
    }

    func parseRedirect() throws -> Node? {
        self.skipWhitespace()
        if self.atEnd() {
            return nil
        }
        var start: Int = self.pos
        var fd: Int = -1
        var varfd: String = ""
        var ch: String = ""
        if self.peek() == "{" {
            var saved: Int = self.pos
            self.advance()
            var varnameChars: [String] = []
            var inBracket: Bool = false
            while !self.atEnd() && !_isRedirectChar(self.peek()) {
                ch = self.peek()
                if ch == "}" && !inBracket {
                    break
                } else {
                    if ch == "[" {
                        inBracket = true
                        varnameChars.append(self.advance())
                    } else {
                        if ch == "]" {
                            inBracket = false
                            varnameChars.append(self.advance())
                        } else {
                            if (ch.first?.isLetter ?? false || ch.first?.isNumber ?? false) || ch == "_" {
                                varnameChars.append(self.advance())
                            } else {
                                if inBracket && !_isMetachar(ch) {
                                    varnameChars.append(self.advance())
                                } else {
                                    break
                                }
                            }
                        }
                    }
                }
            }
            var varname: String = varnameChars.joined(separator: "")
            var isValidVarfd: Bool = false
            if (!varname.isEmpty) {
                if (String(_charAt(varname, 0)).first?.isLetter ?? false) || String(_charAt(varname, 0)) == "_" {
                    if varname.contains("[") || varname.contains("]") {
                        var `left`: Int = (varname.range(of: "[").map { varname.distance(from: varname.startIndex, to: $0.lowerBound) } ?? -1)
                        var `right`: Int = (varname.range(of: "]", options: .backwards).map { varname.distance(from: varname.startIndex, to: $0.lowerBound) } ?? -1)
                        if `left` != -1 && `right` == varname.count - 1 && `right` > `left` + 1 {
                            var base: String = String(varname.prefix(`left`))
                            if (!base.isEmpty) && (String(_charAt(base, 0)).first?.isLetter ?? false) || String(_charAt(base, 0)) == "_" {
                                isValidVarfd = true
                                for _c37 in String(base.dropFirst(1)) {
                                    let c = String(_c37)
                                    if !((Character(UnicodeScalar(c)!).isLetter || Character(UnicodeScalar(c)!).isNumber) || c == "_") {
                                        isValidVarfd = false
                                        break
                                    }
                                }
                            }
                        }
                    } else {
                        isValidVarfd = true
                        for _c38 in String(varname.dropFirst(1)) {
                            let c = String(_c38)
                            if !((Character(UnicodeScalar(c)!).isLetter || Character(UnicodeScalar(c)!).isNumber) || c == "_") {
                                isValidVarfd = false
                                break
                            }
                        }
                    }
                }
            }
            if !self.atEnd() && self.peek() == "}" && isValidVarfd {
                self.advance()
                varfd = varname
            } else {
                self.pos = saved
            }
        }
        var fdChars: [String] = []
        if varfd == "" && (!self.peek().isEmpty) && (self.peek().first?.isNumber ?? false) {
            fdChars = []
            while !self.atEnd() && (self.peek().first?.isNumber ?? false) {
                fdChars.append(self.advance())
            }
            fd = Int(fdChars.joined(separator: ""), radix: 10)!
        }
        ch = self.peek()
        var op: String = ""
        var target: Word? = nil
        if ch == "&" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == ">" {
            if fd != -1 || varfd != "" {
                self.pos = start
                return nil
            }
            self.advance()
            self.advance()
            if !self.atEnd() && self.peek() == ">" {
                self.advance()
                op = "&>>"
            } else {
                op = "&>"
            }
            self.skipWhitespace()
            target = try self.parseWord(false, false, false)
            if target == nil {
                throw ParseError(message: "Expected target for redirect " + op, pos: self.pos)
            }
            return Redirect(op: op, target: target!, fd: 0, kind: "redirect")
        }
        if ch == "" || !_isRedirectChar(ch) {
            self.pos = start
            return nil
        }
        if fd == -1 && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
            self.pos = start
            return nil
        }
        op = self.advance()
        var stripTabs: Bool = false
        if !self.atEnd() {
            var nextCh: String = self.peek()
            if op == ">" && nextCh == ">" {
                self.advance()
                op = ">>"
            } else {
                if op == "<" && nextCh == "<" {
                    self.advance()
                    if !self.atEnd() && self.peek() == "<" {
                        self.advance()
                        op = "<<<"
                    } else {
                        if !self.atEnd() && self.peek() == "-" {
                            self.advance()
                            op = "<<"
                            stripTabs = true
                        } else {
                            op = "<<"
                        }
                    }
                } else {
                    if op == "<" && nextCh == ">" {
                        self.advance()
                        op = "<>"
                    } else {
                        if op == ">" && nextCh == "|" {
                            self.advance()
                            op = ">|"
                        } else {
                            if fd == -1 && varfd == "" && op == ">" && nextCh == "&" {
                                if self.pos + 1 >= self.length || !_isDigitOrDash(String(_charAt(self.source, self.pos + 1))) {
                                    self.advance()
                                    op = ">&"
                                }
                            } else {
                                if fd == -1 && varfd == "" && op == "<" && nextCh == "&" {
                                    if self.pos + 1 >= self.length || !_isDigitOrDash(String(_charAt(self.source, self.pos + 1))) {
                                        self.advance()
                                        op = "<&"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if op == "<<" {
            return self._parseHeredoc(fd, stripTabs)
        }
        if varfd != "" {
            op = "{" + varfd + "}" + op
        } else {
            if fd != -1 {
                op = String(fd) + op
            }
        }
        if !self.atEnd() && self.peek() == "&" {
            self.advance()
            self.skipWhitespace()
            if !self.atEnd() && self.peek() == "-" {
                if self.pos + 1 < self.length && !_isMetachar(String(_charAt(self.source, self.pos + 1))) {
                    self.advance()
                    target = Word(value: "&-", parts: [], kind: "word")
                } else {
                    target = nil
                }
            } else {
                target = nil
            }
            if target == nil {
                var innerWord: Word? = nil
                if !self.atEnd() && (self.peek().first?.isNumber ?? false) || self.peek() == "-" {
                    var wordStart: Int = self.pos
                    fdChars = []
                    while !self.atEnd() && (self.peek().first?.isNumber ?? false) {
                        fdChars.append(self.advance())
                    }
                    var fdTarget: String = ""
                    if (!fdChars.isEmpty) {
                        fdTarget = fdChars.joined(separator: "")
                    } else {
                        fdTarget = ""
                    }
                    if !self.atEnd() && self.peek() == "-" {
                        fdTarget += self.advance()
                    }
                    if fdTarget != "-" && !self.atEnd() && !_isMetachar(self.peek()) {
                        self.pos = wordStart
                        innerWord = try self.parseWord(false, false, false)
                        if innerWord != nil {
                            target = Word(value: "&" + innerWord!.value, parts: [], kind: "word")
                            target!!.parts = innerWord!.parts
                        } else {
                            throw ParseError(message: "Expected target for redirect " + op, pos: self.pos)
                        }
                    } else {
                        target = Word(value: "&" + fdTarget, parts: [], kind: "word")
                    }
                } else {
                    innerWord = try self.parseWord(false, false, false)
                    if innerWord != nil {
                        target = Word(value: "&" + innerWord!.value, parts: [], kind: "word")
                        target!!.parts = innerWord!.parts
                    } else {
                        throw ParseError(message: "Expected target for redirect " + op, pos: self.pos)
                    }
                }
            }
        } else {
            self.skipWhitespace()
            if op == ">&" || op == "<&" && !self.atEnd() && self.peek() == "-" {
                if self.pos + 1 < self.length && !_isMetachar(String(_charAt(self.source, self.pos + 1))) {
                    self.advance()
                    target = Word(value: "&-", parts: [], kind: "word")
                } else {
                    target = try self.parseWord(false, false, false)
                }
            } else {
                target = try self.parseWord(false, false, false)
            }
        }
        if target == nil {
            throw ParseError(message: "Expected target for redirect " + op, pos: self.pos)
        }
        return Redirect(op: op, target: target!, fd: 0, kind: "redirect")
    }

    func _parseHeredocDelimiter() -> (String, Bool) {
        self.skipWhitespace()
        var quoted: Bool = false
        var delimiterChars: [String] = []
        while true {
            var c: String = ""
            var depth: Int = 0
            while !self.atEnd() && !_isMetachar(self.peek()) {
                var ch: String = self.peek()
                if ch == "\"" {
                    quoted = true
                    self.advance()
                    while !self.atEnd() && self.peek() != "\"" {
                        delimiterChars.append(self.advance())
                    }
                    if !self.atEnd() {
                        self.advance()
                    }
                } else {
                    if ch == "'" {
                        quoted = true
                        self.advance()
                        while !self.atEnd() && self.peek() != "'" {
                            c = self.advance()
                            if c == "\n" {
                                self._sawNewlineInSingleQuote = true
                            }
                            delimiterChars.append(c)
                        }
                        if !self.atEnd() {
                            self.advance()
                        }
                    } else {
                        if ch == "\\" {
                            self.advance()
                            if !self.atEnd() {
                                var nextCh: String = self.peek()
                                if nextCh == "\n" {
                                    self.advance()
                                } else {
                                    quoted = true
                                    delimiterChars.append(self.advance())
                                }
                            }
                        } else {
                            if ch == "$" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "'" {
                                quoted = true
                                self.advance()
                                self.advance()
                                while !self.atEnd() && self.peek() != "'" {
                                    c = self.peek()
                                    if c == "\\" && self.pos + 1 < self.length {
                                        self.advance()
                                        var esc: String = self.peek()
                                        var escVal: Int = _getAnsiEscape(esc)
                                        if escVal >= 0 {
                                            delimiterChars.append(String(Character(UnicodeScalar(escVal)!)))
                                            self.advance()
                                        } else {
                                            if esc == "'" {
                                                delimiterChars.append(self.advance())
                                            } else {
                                                delimiterChars.append(self.advance())
                                            }
                                        }
                                    } else {
                                        delimiterChars.append(self.advance())
                                    }
                                }
                                if !self.atEnd() {
                                    self.advance()
                                }
                            } else {
                                if _isExpansionStart(self.source, self.pos, "$(") {
                                    delimiterChars.append(self.advance())
                                    delimiterChars.append(self.advance())
                                    depth = 1
                                    while !self.atEnd() && depth > 0 {
                                        c = self.peek()
                                        if c == "(" {
                                            depth += 1
                                        } else {
                                            if c == ")" {
                                                depth -= 1
                                            }
                                        }
                                        delimiterChars.append(self.advance())
                                    }
                                } else {
                                    var dollarCount: Int = 0
                                    var j: Int = 0
                                    if ch == "$" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "{" {
                                        dollarCount = 0
                                        j = self.pos - 1
                                        while j >= 0 && String(_charAt(self.source, j)) == "$" {
                                            dollarCount += 1
                                            j -= 1
                                        }
                                        if j >= 0 && String(_charAt(self.source, j)) == "\\" {
                                            dollarCount -= 1
                                        }
                                        if dollarCount % 2 == 1 {
                                            delimiterChars.append(self.advance())
                                        } else {
                                            delimiterChars.append(self.advance())
                                            delimiterChars.append(self.advance())
                                            depth = 0
                                            while !self.atEnd() {
                                                c = self.peek()
                                                if c == "{" {
                                                    depth += 1
                                                } else {
                                                    if c == "}" {
                                                        delimiterChars.append(self.advance())
                                                        if depth == 0 {
                                                            break
                                                        }
                                                        depth -= 1
                                                        if depth == 0 && !self.atEnd() && _isMetachar(self.peek()) {
                                                            break
                                                        }
                                                        continue
                                                    }
                                                }
                                                delimiterChars.append(self.advance())
                                            }
                                        }
                                    } else {
                                        if ch == "$" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "[" {
                                            dollarCount = 0
                                            j = self.pos - 1
                                            while j >= 0 && String(_charAt(self.source, j)) == "$" {
                                                dollarCount += 1
                                                j -= 1
                                            }
                                            if j >= 0 && String(_charAt(self.source, j)) == "\\" {
                                                dollarCount -= 1
                                            }
                                            if dollarCount % 2 == 1 {
                                                delimiterChars.append(self.advance())
                                            } else {
                                                delimiterChars.append(self.advance())
                                                delimiterChars.append(self.advance())
                                                depth = 1
                                                while !self.atEnd() && depth > 0 {
                                                    c = self.peek()
                                                    if c == "[" {
                                                        depth += 1
                                                    } else {
                                                        if c == "]" {
                                                            depth -= 1
                                                        }
                                                    }
                                                    delimiterChars.append(self.advance())
                                                }
                                            }
                                        } else {
                                            if ch == "`" {
                                                delimiterChars.append(self.advance())
                                                while !self.atEnd() && self.peek() != "`" {
                                                    c = self.peek()
                                                    if c == "'" {
                                                        delimiterChars.append(self.advance())
                                                        while !self.atEnd() && self.peek() != "'" && self.peek() != "`" {
                                                            delimiterChars.append(self.advance())
                                                        }
                                                        if !self.atEnd() && self.peek() == "'" {
                                                            delimiterChars.append(self.advance())
                                                        }
                                                    } else {
                                                        if c == "\"" {
                                                            delimiterChars.append(self.advance())
                                                            while !self.atEnd() && self.peek() != "\"" && self.peek() != "`" {
                                                                if self.peek() == "\\" && self.pos + 1 < self.length {
                                                                    delimiterChars.append(self.advance())
                                                                }
                                                                delimiterChars.append(self.advance())
                                                            }
                                                            if !self.atEnd() && self.peek() == "\"" {
                                                                delimiterChars.append(self.advance())
                                                            }
                                                        } else {
                                                            if c == "\\" && self.pos + 1 < self.length {
                                                                delimiterChars.append(self.advance())
                                                                delimiterChars.append(self.advance())
                                                            } else {
                                                                delimiterChars.append(self.advance())
                                                            }
                                                        }
                                                    }
                                                }
                                                if !self.atEnd() {
                                                    delimiterChars.append(self.advance())
                                                }
                                            } else {
                                                delimiterChars.append(self.advance())
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if !self.atEnd() && "<>".contains(self.peek()) && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                delimiterChars.append(self.advance())
                delimiterChars.append(self.advance())
                depth = 1
                while !self.atEnd() && depth > 0 {
                    c = self.peek()
                    if c == "(" {
                        depth += 1
                    } else {
                        if c == ")" {
                            depth -= 1
                        }
                    }
                    delimiterChars.append(self.advance())
                }
                continue
            }
            break
        }
        return (delimiterChars.joined(separator: ""), quoted)
    }

    func _readHeredocLine(_ quoted: Bool) -> (String, Int) {
        var lineStart: Int = self.pos
        var lineEnd: Int = self.pos
        while lineEnd < self.length && String(_charAt(self.source, lineEnd)) != "\n" {
            lineEnd += 1
        }
        var line: String = _substring(self.source, lineStart, lineEnd)
        if !quoted {
            while lineEnd < self.length {
                var trailingBs: Int = _countTrailingBackslashes(line)
                if trailingBs % 2 == 0 {
                    break
                }
                line = _substring(line, 0, line.count - 1)
                lineEnd += 1
                var nextLineStart: Int = lineEnd
                while lineEnd < self.length && String(_charAt(self.source, lineEnd)) != "\n" {
                    lineEnd += 1
                }
                line = line + _substring(self.source, nextLineStart, lineEnd)
            }
        }
        return (line, lineEnd)
    }

    func _lineMatchesDelimiter(_ line: String, _ delimiter: String, _ stripTabs: Bool) -> (Bool, String) {
        var checkLine: String = (stripTabs ? line.trimmingCharacters(in: CharacterSet(charactersIn: "\t")) : line)
        var normalizedCheck: String = _normalizeHeredocDelimiter(checkLine)
        var normalizedDelim: String = _normalizeHeredocDelimiter(delimiter)
        return (normalizedCheck == normalizedDelim, checkLine)
    }

    func _gatherHeredocBodies() {
        for heredoc in self._pendingHeredocs {
            var contentLines: [String] = []
            var lineStart: Int = self.pos
            while self.pos < self.length {
                lineStart = self.pos
                let _tuple39 = self._readHeredocLine(heredoc.quoted)
                var line: String = _tuple39.0
                var lineEnd: Int = _tuple39.1
                let _tuple40 = self._lineMatchesDelimiter(line, heredoc.delimiter, heredoc.stripTabs)
                var matches: Bool = _tuple40.0
                var checkLine: String = _tuple40.1
                if matches {
                    self.pos = (lineEnd < self.length ? lineEnd + 1 : lineEnd)
                    break
                }
                var normalizedCheck: String = _normalizeHeredocDelimiter(checkLine)
                var normalizedDelim: String = _normalizeHeredocDelimiter(heredoc.delimiter)
                var tabsStripped: Int = 0
                if self._eofToken == ")" && normalizedCheck.hasPrefix(normalizedDelim) {
                    tabsStripped = line.count - checkLine.count
                    self.pos = lineStart + tabsStripped + heredoc.delimiter.count
                    break
                }
                if lineEnd >= self.length && normalizedCheck.hasPrefix(normalizedDelim) && self._inProcessSub {
                    tabsStripped = line.count - checkLine.count
                    self.pos = lineStart + tabsStripped + heredoc.delimiter.count
                    break
                }
                if heredoc.stripTabs {
                    line = line.trimmingCharacters(in: CharacterSet(charactersIn: "\t"))
                }
                if lineEnd < self.length {
                    contentLines.append(line + "\n")
                    self.pos = lineEnd + 1
                } else {
                    var addNewline: Bool = true
                    if !heredoc.quoted && _countTrailingBackslashes(line) % 2 == 1 {
                        addNewline = false
                    }
                    contentLines.append(line + (addNewline ? "\n" : ""))
                    self.pos = self.length
                }
            }
            heredoc.content = contentLines.joined(separator: "")
        }
        self._pendingHeredocs = []
    }

    func _parseHeredoc(_ fd: Int, _ stripTabs: Bool) -> HereDoc {
        var startPos: Int = self.pos
        self._setState(parserstateflagsPstHeredoc)
        let _tuple41 = self._parseHeredocDelimiter()
        var delimiter: String = _tuple41.0
        var quoted: Bool = _tuple41.1
        for existing in self._pendingHeredocs {
            if existing._startPos == startPos && existing.delimiter == delimiter {
                self._clearState(parserstateflagsPstHeredoc)
                return existing
            }
        }
        var heredoc: HereDoc = HereDoc(delimiter: delimiter, content: "", stripTabs: stripTabs, quoted: quoted, fd: fd, complete: false, _startPos: 0, kind: "heredoc")
        heredoc._startPos = startPos
        self._pendingHeredocs.append(heredoc)
        self._clearState(parserstateflagsPstHeredoc)
        return heredoc
    }

    func parseCommand() throws -> Command? {
        var words: [Word] = []
        var redirects: [Node] = []
        while true {
            self.skipWhitespace()
            if try self._lexIsCommandTerminator() {
                break
            }
            if words.count == 0 {
                var reserved: String = try self._lexPeekReservedWord()
                if reserved == "}" || reserved == "]]" {
                    break
                }
            }
            var redirect: Node? = try self.parseRedirect()
            if redirect != nil {
                redirects.append(redirect!)
                continue
            }
            var allAssignments: Bool = true
            for w in words {
                if !self._isAssignmentWord(w) {
                    allAssignments = false
                    break
                }
            }
            var inAssignBuiltin: Bool = words.count > 0 && assignmentBuiltins.contains(words[0].value)
            var word: Word? = try self.parseWord(!(!words.isEmpty) || allAssignments && redirects.count == 0, false, inAssignBuiltin)
            if word == nil {
                break
            }
            words.append(word!)
        }
        if !(!words.isEmpty) && !(!redirects.isEmpty) {
            return nil
        }
        return Command(words: words, redirects: redirects, kind: "command")
    }

    func parseSubshell() throws -> Subshell? {
        self.skipWhitespace()
        if self.atEnd() || self.peek() != "(" {
            return nil
        }
        self.advance()
        self._setState(parserstateflagsPstSubshell)
        var body: Node? = try self.parseList(true)
        if body == nil {
            self._clearState(parserstateflagsPstSubshell)
            throw ParseError(message: "Expected command in subshell", pos: self.pos)
        }
        self.skipWhitespace()
        if self.atEnd() || self.peek() != ")" {
            self._clearState(parserstateflagsPstSubshell)
            throw ParseError(message: "Expected ) to close subshell", pos: self.pos)
        }
        self.advance()
        self._clearState(parserstateflagsPstSubshell)
        return try Subshell(body: body!, redirects: self._collectRedirects(), kind: "subshell")
    }

    func parseArithmeticCommand() throws -> ArithmeticCommand? {
        self.skipWhitespace()
        if self.atEnd() || self.peek() != "(" || self.pos + 1 >= self.length || String(_charAt(self.source, self.pos + 1)) != "(" {
            return nil
        }
        var savedPos: Int = self.pos
        self.advance()
        self.advance()
        var contentStart: Int = self.pos
        var depth: Int = 1
        while !self.atEnd() && depth > 0 {
            var c: String = self.peek()
            if c == "'" {
                self.advance()
                while !self.atEnd() && self.peek() != "'" {
                    self.advance()
                }
                if !self.atEnd() {
                    self.advance()
                }
            } else {
                if c == "\"" {
                    self.advance()
                    while !self.atEnd() {
                        if self.peek() == "\\" && self.pos + 1 < self.length {
                            self.advance()
                            self.advance()
                        } else {
                            if self.peek() == "\"" {
                                self.advance()
                                break
                            } else {
                                self.advance()
                            }
                        }
                    }
                } else {
                    if c == "\\" && self.pos + 1 < self.length {
                        self.advance()
                        self.advance()
                    } else {
                        if c == "(" {
                            depth += 1
                            self.advance()
                        } else {
                            if c == ")" {
                                if depth == 1 && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == ")" {
                                    break
                                }
                                depth -= 1
                                if depth == 0 {
                                    self.pos = savedPos
                                    return nil
                                }
                                self.advance()
                            } else {
                                self.advance()
                            }
                        }
                    }
                }
            }
        }
        if self.atEnd() {
            throw MatchedPairError(message: "unexpected EOF looking for `))'", pos: savedPos)
        }
        if depth != 1 {
            self.pos = savedPos
            return nil
        }
        var content: String = _substring(self.source, contentStart, self.pos)
        content = content.replacingOccurrences(of: "\\\n", with: "")
        self.advance()
        self.advance()
        var expr: Node = self._parseArithExpr(content)
        return try ArithmeticCommand(expression: expr, redirects: self._collectRedirects(), rawContent: content, kind: "arith-cmd")
    }

    func parseConditionalExpr() throws -> ConditionalExpr? {
        self.skipWhitespace()
        if self.atEnd() || self.peek() != "[" || self.pos + 1 >= self.length || String(_charAt(self.source, self.pos + 1)) != "[" {
            return nil
        }
        var nextPos: Int = self.pos + 2
        if nextPos < self.length && !(_isWhitespace(String(_charAt(self.source, nextPos))) || String(_charAt(self.source, nextPos)) == "\\" && nextPos + 1 < self.length && String(_charAt(self.source, nextPos + 1)) == "\n") {
            return nil
        }
        self.advance()
        self.advance()
        self._setState(parserstateflagsPstCondexpr)
        self._wordContext = wordCtxCond
        var body: Node = try self._parseCondOr()
        while !self.atEnd() && _isWhitespaceNoNewline(self.peek()) {
            self.advance()
        }
        if self.atEnd() || self.peek() != "]" || self.pos + 1 >= self.length || String(_charAt(self.source, self.pos + 1)) != "]" {
            self._clearState(parserstateflagsPstCondexpr)
            self._wordContext = wordCtxNormal
            throw ParseError(message: "Expected ]] to close conditional expression", pos: self.pos)
        }
        self.advance()
        self.advance()
        self._clearState(parserstateflagsPstCondexpr)
        self._wordContext = wordCtxNormal
        return try ConditionalExpr(body: body, redirects: self._collectRedirects(), kind: "cond-expr")
    }

    func _condSkipWhitespace() {
        while !self.atEnd() {
            if _isWhitespaceNoNewline(self.peek()) {
                self.advance()
            } else {
                if self.peek() == "\\" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "\n" {
                    self.advance()
                    self.advance()
                } else {
                    if self.peek() == "\n" {
                        self.advance()
                    } else {
                        break
                    }
                }
            }
        }
    }

    func _condAtEnd() -> Bool {
        return self.atEnd() || self.peek() == "]" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "]"
    }

    func _parseCondOr() throws -> Node {
        self._condSkipWhitespace()
        var `left`: Node = try self._parseCondAnd()
        self._condSkipWhitespace()
        if !self._condAtEnd() && self.peek() == "|" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "|" {
            self.advance()
            self.advance()
            var `right`: Node = try self._parseCondOr()
            return CondOr(`left`: `left`, `right`: `right`, kind: "cond-or")
        }
        return `left`
    }

    func _parseCondAnd() throws -> Node {
        self._condSkipWhitespace()
        var `left`: Node = try self._parseCondTerm()
        self._condSkipWhitespace()
        if !self._condAtEnd() && self.peek() == "&" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "&" {
            self.advance()
            self.advance()
            var `right`: Node = try self._parseCondAnd()
            return CondAnd(`left`: `left`, `right`: `right`, kind: "cond-and")
        }
        return `left`
    }

    func _parseCondTerm() throws -> Node {
        self._condSkipWhitespace()
        if self._condAtEnd() {
            throw ParseError(message: "Unexpected end of conditional expression", pos: self.pos)
        }
        if self.peek() == "!" {
            if self.pos + 1 < self.length && !_isWhitespaceNoNewline(String(_charAt(self.source, self.pos + 1))) {
            } else {
                self.advance()
                var operand: Node = try self._parseCondTerm()
                return CondNot(operand: operand, kind: "cond-not")
            }
        }
        if self.peek() == "(" {
            self.advance()
            var inner: Node = try self._parseCondOr()
            self._condSkipWhitespace()
            if self.atEnd() || self.peek() != ")" {
                throw ParseError(message: "Expected ) in conditional expression", pos: self.pos)
            }
            self.advance()
            return CondParen(inner: inner, kind: "cond-paren")
        }
        var word1: Word? = try self._parseCondWord()
        if word1 == nil {
            throw ParseError(message: "Expected word in conditional expression", pos: self.pos)
        }
        self._condSkipWhitespace()
        if condUnaryOps.contains(word1!.value) {
            var unaryOperand: Word? = try self._parseCondWord()
            if unaryOperand == nil {
                throw ParseError(message: "Expected operand after " + word1!.value, pos: self.pos)
            }
            return UnaryTest(op: word1!.value, operand: unaryOperand!, kind: "unary-test")
        }
        if !self._condAtEnd() && self.peek() != "&" && self.peek() != "|" && self.peek() != ")" {
            var word2: Word? = nil
            if _isRedirectChar(self.peek()) && !(self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(") {
                var op: String = self.advance()
                self._condSkipWhitespace()
                word2 = try self._parseCondWord()
                if word2 == nil {
                    throw ParseError(message: "Expected operand after " + op, pos: self.pos)
                }
                return BinaryTest(op: op, `left`: word1!, `right`: word2!, kind: "binary-test")
            }
            var savedPos: Int = self.pos
            var opWord: Word? = try self._parseCondWord()
            if opWord != nil && condBinaryOps.contains(opWord!.value) {
                self._condSkipWhitespace()
                if opWord!.value == "=~" {
                    word2 = try self._parseCondRegexWord()
                } else {
                    word2 = try self._parseCondWord()
                }
                if word2 == nil {
                    throw ParseError(message: "Expected operand after " + opWord!.value, pos: self.pos)
                }
                return BinaryTest(op: opWord!.value, `left`: word1!, `right`: word2!, kind: "binary-test")
            } else {
                self.pos = savedPos
            }
        }
        return UnaryTest(op: "-n", operand: word1!, kind: "unary-test")
    }

    func _parseCondWord() throws -> Word? {
        self._condSkipWhitespace()
        if self._condAtEnd() {
            return nil
        }
        var c: String = self.peek()
        if _isParen(c) {
            return nil
        }
        if c == "&" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "&" {
            return nil
        }
        if c == "|" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "|" {
            return nil
        }
        return try self._parseWordInternal(wordCtxCond, false, false)
    }

    func _parseCondRegexWord() throws -> Word? {
        self._condSkipWhitespace()
        if self._condAtEnd() {
            return nil
        }
        self._setState(parserstateflagsPstRegexp)
        var result: Word = try self._parseWordInternal(wordCtxRegex, false, false)
        self._clearState(parserstateflagsPstRegexp)
        self._wordContext = wordCtxCond
        return result
    }

    func parseBraceGroup() throws -> BraceGroup? {
        self.skipWhitespace()
        if try !self._lexConsumeWord("{") {
            return nil
        }
        self.skipWhitespaceAndNewlines()
        var body: Node? = try self.parseList(true)
        if body == nil {
            throw try ParseError(message: "Expected command in brace group", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespace()
        if try !self._lexConsumeWord("}") {
            throw try ParseError(message: "Expected } to close brace group", pos: self._lexPeekToken().pos)
        }
        return try BraceGroup(body: body!, redirects: self._collectRedirects(), kind: "brace-group")
    }

    func parseIf() throws -> If? {
        self.skipWhitespace()
        if try !self._lexConsumeWord("if") {
            return nil
        }
        var condition: Node? = try self.parseListUntil(Set(["then"]))
        if condition == nil {
            throw try ParseError(message: "Expected condition after 'if'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("then") {
            throw try ParseError(message: "Expected 'then' after if condition", pos: self._lexPeekToken().pos)
        }
        var thenBody: Node? = try self.parseListUntil(Set(["elif", "else", "fi"]))
        if thenBody == nil {
            throw try ParseError(message: "Expected commands after 'then'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        var elseBody: Node? = nil
        if try self._lexIsAtReservedWord("elif") {
            try self._lexConsumeWord("elif")
            var elifCondition: Node? = try self.parseListUntil(Set(["then"]))
            if elifCondition == nil {
                throw try ParseError(message: "Expected condition after 'elif'", pos: self._lexPeekToken().pos)
            }
            self.skipWhitespaceAndNewlines()
            if try !self._lexConsumeWord("then") {
                throw try ParseError(message: "Expected 'then' after elif condition", pos: self._lexPeekToken().pos)
            }
            var elifThenBody: Node? = try self.parseListUntil(Set(["elif", "else", "fi"]))
            if elifThenBody == nil {
                throw try ParseError(message: "Expected commands after 'then'", pos: self._lexPeekToken().pos)
            }
            self.skipWhitespaceAndNewlines()
            var innerElse: Node? = nil
            if try self._lexIsAtReservedWord("elif") {
                innerElse = try self._parseElifChain()
            } else {
                if try self._lexIsAtReservedWord("else") {
                    try self._lexConsumeWord("else")
                    innerElse = try self.parseListUntil(Set(["fi"]))
                    if innerElse == nil {
                        throw try ParseError(message: "Expected commands after 'else'", pos: self._lexPeekToken().pos)
                    }
                }
            }
            elseBody = If(condition: elifCondition!, thenBody: elifThenBody!, elseBody: innerElse!, redirects: [], kind: "if")
        } else {
            if try self._lexIsAtReservedWord("else") {
                try self._lexConsumeWord("else")
                elseBody = try self.parseListUntil(Set(["fi"]))
                if elseBody == nil {
                    throw try ParseError(message: "Expected commands after 'else'", pos: self._lexPeekToken().pos)
                }
            }
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("fi") {
            throw try ParseError(message: "Expected 'fi' to close if statement", pos: self._lexPeekToken().pos)
        }
        return try If(condition: condition!, thenBody: thenBody!, elseBody: elseBody!, redirects: self._collectRedirects(), kind: "if")
    }

    func _parseElifChain() throws -> If {
        try self._lexConsumeWord("elif")
        var condition: Node? = try self.parseListUntil(Set(["then"]))
        if condition == nil {
            throw try ParseError(message: "Expected condition after 'elif'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("then") {
            throw try ParseError(message: "Expected 'then' after elif condition", pos: self._lexPeekToken().pos)
        }
        var thenBody: Node? = try self.parseListUntil(Set(["elif", "else", "fi"]))
        if thenBody == nil {
            throw try ParseError(message: "Expected commands after 'then'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        var elseBody: Node? = nil
        if try self._lexIsAtReservedWord("elif") {
            elseBody = try self._parseElifChain()
        } else {
            if try self._lexIsAtReservedWord("else") {
                try self._lexConsumeWord("else")
                elseBody = try self.parseListUntil(Set(["fi"]))
                if elseBody == nil {
                    throw try ParseError(message: "Expected commands after 'else'", pos: self._lexPeekToken().pos)
                }
            }
        }
        return If(condition: condition!, thenBody: thenBody!, elseBody: elseBody!, redirects: [], kind: "if")
    }

    func parseWhile() throws -> While? {
        self.skipWhitespace()
        if try !self._lexConsumeWord("while") {
            return nil
        }
        var condition: Node? = try self.parseListUntil(Set(["do"]))
        if condition == nil {
            throw try ParseError(message: "Expected condition after 'while'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("do") {
            throw try ParseError(message: "Expected 'do' after while condition", pos: self._lexPeekToken().pos)
        }
        var body: Node? = try self.parseListUntil(Set(["done"]))
        if body == nil {
            throw try ParseError(message: "Expected commands after 'do'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("done") {
            throw try ParseError(message: "Expected 'done' to close while loop", pos: self._lexPeekToken().pos)
        }
        return try While(condition: condition!, body: body!, redirects: self._collectRedirects(), kind: "while")
    }

    func parseUntil() throws -> Until? {
        self.skipWhitespace()
        if try !self._lexConsumeWord("until") {
            return nil
        }
        var condition: Node? = try self.parseListUntil(Set(["do"]))
        if condition == nil {
            throw try ParseError(message: "Expected condition after 'until'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("do") {
            throw try ParseError(message: "Expected 'do' after until condition", pos: self._lexPeekToken().pos)
        }
        var body: Node? = try self.parseListUntil(Set(["done"]))
        if body == nil {
            throw try ParseError(message: "Expected commands after 'do'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("done") {
            throw try ParseError(message: "Expected 'done' to close until loop", pos: self._lexPeekToken().pos)
        }
        return try Until(condition: condition!, body: body!, redirects: self._collectRedirects(), kind: "until")
    }

    func parseFor() throws -> Node? {
        self.skipWhitespace()
        if try !self._lexConsumeWord("for") {
            return nil
        }
        self.skipWhitespace()
        if self.peek() == "(" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
            return try self._parseForArith()
        }
        var varName: String = ""
        if self.peek() == "$" {
            var varWord: Word? = try self.parseWord(false, false, false)
            if varWord == nil {
                throw try ParseError(message: "Expected variable name after 'for'", pos: self._lexPeekToken().pos)
            }
            varName = varWord!.value
        } else {
            varName = self.peekWord()
            if varName == "" {
                throw try ParseError(message: "Expected variable name after 'for'", pos: self._lexPeekToken().pos)
            }
            self.consumeWord(varName)
        }
        self.skipWhitespace()
        if self.peek() == ";" {
            self.advance()
        }
        self.skipWhitespaceAndNewlines()
        var words: [Word]? = nil
        if try self._lexIsAtReservedWord("in") {
            try self._lexConsumeWord("in")
            self.skipWhitespace()
            var sawDelimiter: Bool = _isSemicolonOrNewline(self.peek())
            if self.peek() == ";" {
                self.advance()
            }
            self.skipWhitespaceAndNewlines()
            words = []
            while true {
                self.skipWhitespace()
                if self.atEnd() {
                    break
                }
                if _isSemicolonOrNewline(self.peek()) {
                    sawDelimiter = true
                    if self.peek() == ";" {
                        self.advance()
                    }
                    break
                }
                if try self._lexIsAtReservedWord("do") {
                    if sawDelimiter {
                        break
                    }
                    throw try ParseError(message: "Expected ';' or newline before 'do'", pos: self._lexPeekToken().pos)
                }
                var word: Word? = try self.parseWord(false, false, false)
                if word == nil {
                    break
                }
                words!.append(word!)
            }
        }
        self.skipWhitespaceAndNewlines()
        if self.peek() == "{" {
            var braceGroup: BraceGroup? = try self.parseBraceGroup()
            if braceGroup == nil {
                throw try ParseError(message: "Expected brace group in for loop", pos: self._lexPeekToken().pos)
            }
            return try For(`var`: varName, words: words!, body: braceGroup!.body, redirects: self._collectRedirects(), kind: "for")
        }
        if try !self._lexConsumeWord("do") {
            throw try ParseError(message: "Expected 'do' in for loop", pos: self._lexPeekToken().pos)
        }
        var body: Node? = try self.parseListUntil(Set(["done"]))
        if body == nil {
            throw try ParseError(message: "Expected commands after 'do'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("done") {
            throw try ParseError(message: "Expected 'done' to close for loop", pos: self._lexPeekToken().pos)
        }
        return try For(`var`: varName, words: words!, body: body!, redirects: self._collectRedirects(), kind: "for")
    }

    func _parseForArith() throws -> ForArith {
        self.advance()
        self.advance()
        var parts: [String] = []
        var current: [String] = []
        var parenDepth: Int = 0
        while !self.atEnd() {
            var ch: String = self.peek()
            if ch == "(" {
                parenDepth += 1
                current.append(self.advance())
            } else {
                if ch == ")" {
                    if parenDepth > 0 {
                        parenDepth -= 1
                        current.append(self.advance())
                    } else {
                        if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == ")" {
                            parts.append(current.joined(separator: "").trimmingCharacters(in: CharacterSet(charactersIn: " \t")))
                            self.advance()
                            self.advance()
                            break
                        } else {
                            current.append(self.advance())
                        }
                    }
                } else {
                    if ch == ";" && parenDepth == 0 {
                        parts.append(current.joined(separator: "").trimmingCharacters(in: CharacterSet(charactersIn: " \t")))
                        current = []
                        self.advance()
                    } else {
                        current.append(self.advance())
                    }
                }
            }
        }
        if parts.count != 3 {
            throw ParseError(message: "Expected three expressions in for ((;;))", pos: self.pos)
        }
        var `init`: String = parts[0]
        var cond: String = parts[1]
        var incr: String = parts[2]
        self.skipWhitespace()
        if !self.atEnd() && self.peek() == ";" {
            self.advance()
        }
        self.skipWhitespaceAndNewlines()
        var body: Node = try self._parseLoopBody("for loop")
        return try ForArith(`init`: `init`, cond: cond, incr: incr, body: body, redirects: self._collectRedirects(), kind: "for-arith")
    }

    func parseSelect() throws -> Select? {
        self.skipWhitespace()
        if try !self._lexConsumeWord("select") {
            return nil
        }
        self.skipWhitespace()
        var varName: String = self.peekWord()
        if varName == "" {
            throw try ParseError(message: "Expected variable name after 'select'", pos: self._lexPeekToken().pos)
        }
        self.consumeWord(varName)
        self.skipWhitespace()
        if self.peek() == ";" {
            self.advance()
        }
        self.skipWhitespaceAndNewlines()
        var words: [Word]? = nil
        if try self._lexIsAtReservedWord("in") {
            try self._lexConsumeWord("in")
            self.skipWhitespaceAndNewlines()
            words = []
            while true {
                self.skipWhitespace()
                if self.atEnd() {
                    break
                }
                if _isSemicolonNewlineBrace(self.peek()) {
                    if self.peek() == ";" {
                        self.advance()
                    }
                    break
                }
                if try self._lexIsAtReservedWord("do") {
                    break
                }
                var word: Word? = try self.parseWord(false, false, false)
                if word == nil {
                    break
                }
                words!.append(word!)
            }
        }
        self.skipWhitespaceAndNewlines()
        var body: Node = try self._parseLoopBody("select")
        return try Select(`var`: varName, words: words!, body: body, redirects: self._collectRedirects(), kind: "select")
    }

    func _consumeCaseTerminator() throws -> String {
        var term: String = try self._lexPeekCaseTerminator()
        if term != "" {
            try self._lexNextToken()
            return term
        }
        return ";;"
    }

    func parseCase() throws -> Case? {
        if !self.consumeWord("case") {
            return nil
        }
        self._setState(parserstateflagsPstCasestmt)
        self.skipWhitespace()
        var word: Word? = try self.parseWord(false, false, false)
        if word == nil {
            throw try ParseError(message: "Expected word after 'case'", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("in") {
            throw try ParseError(message: "Expected 'in' after case word", pos: self._lexPeekToken().pos)
        }
        self.skipWhitespaceAndNewlines()
        var patterns: [CasePattern] = []
        self._setState(parserstateflagsPstCasepat)
        while true {
            self.skipWhitespaceAndNewlines()
            if try self._lexIsAtReservedWord("esac") {
                var saved: Int = self.pos
                self.skipWhitespace()
                while !self.atEnd() && !_isMetachar(self.peek()) && !_isQuote(self.peek()) {
                    self.advance()
                }
                self.skipWhitespace()
                var isPattern: Bool = false
                if !self.atEnd() && self.peek() == ")" {
                    if self._eofToken == ")" {
                        isPattern = false
                    } else {
                        self.advance()
                        self.skipWhitespace()
                        if !self.atEnd() {
                            var nextCh: String = self.peek()
                            if nextCh == ";" {
                                isPattern = true
                            } else {
                                if !_isNewlineOrRightParen(nextCh) {
                                    isPattern = true
                                }
                            }
                        }
                    }
                }
                self.pos = saved
                if !isPattern {
                    break
                }
            }
            self.skipWhitespaceAndNewlines()
            if !self.atEnd() && self.peek() == "(" {
                self.advance()
                self.skipWhitespaceAndNewlines()
            }
            var patternChars: [String] = []
            var extglobDepth: Int = 0
            while !self.atEnd() {
                var ch: String = self.peek()
                if ch == ")" {
                    if extglobDepth > 0 {
                        patternChars.append(self.advance())
                        extglobDepth -= 1
                    } else {
                        self.advance()
                        break
                    }
                } else {
                    if ch == "\\" {
                        if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "\n" {
                            self.advance()
                            self.advance()
                        } else {
                            patternChars.append(self.advance())
                            if !self.atEnd() {
                                patternChars.append(self.advance())
                            }
                        }
                    } else {
                        if _isExpansionStart(self.source, self.pos, "$(") {
                            patternChars.append(self.advance())
                            patternChars.append(self.advance())
                            if !self.atEnd() && self.peek() == "(" {
                                patternChars.append(self.advance())
                                var parenDepth: Int = 2
                                while !self.atEnd() && parenDepth > 0 {
                                    var c: String = self.peek()
                                    if c == "(" {
                                        parenDepth += 1
                                    } else {
                                        if c == ")" {
                                            parenDepth -= 1
                                        }
                                    }
                                    patternChars.append(self.advance())
                                }
                            } else {
                                extglobDepth += 1
                            }
                        } else {
                            if ch == "(" && extglobDepth > 0 {
                                patternChars.append(self.advance())
                                extglobDepth += 1
                            } else {
                                if self._extglob && _isExtglobPrefix(ch) && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                                    patternChars.append(self.advance())
                                    patternChars.append(self.advance())
                                    extglobDepth += 1
                                } else {
                                    if ch == "[" {
                                        var isCharClass: Bool = false
                                        var scanPos: Int = self.pos + 1
                                        var scanDepth: Int = 0
                                        var hasFirstBracketLiteral: Bool = false
                                        if scanPos < self.length && _isCaretOrBang(String(_charAt(self.source, scanPos))) {
                                            scanPos += 1
                                        }
                                        if scanPos < self.length && String(_charAt(self.source, scanPos)) == "]" {
                                            if (self.source.range(of: "]").map { self.source.distance(from: self.source.startIndex, to: $0.lowerBound) } ?? -1) != -1 {
                                                scanPos += 1
                                                hasFirstBracketLiteral = true
                                            }
                                        }
                                        while scanPos < self.length {
                                            var sc: String = String(_charAt(self.source, scanPos))
                                            if sc == "]" && scanDepth == 0 {
                                                isCharClass = true
                                                break
                                            } else {
                                                if sc == "[" {
                                                    scanDepth += 1
                                                } else {
                                                    if sc == ")" && scanDepth == 0 {
                                                        break
                                                    } else {
                                                        if sc == "|" && scanDepth == 0 {
                                                            break
                                                        }
                                                    }
                                                }
                                            }
                                            scanPos += 1
                                        }
                                        if isCharClass {
                                            patternChars.append(self.advance())
                                            if !self.atEnd() && _isCaretOrBang(self.peek()) {
                                                patternChars.append(self.advance())
                                            }
                                            if hasFirstBracketLiteral && !self.atEnd() && self.peek() == "]" {
                                                patternChars.append(self.advance())
                                            }
                                            while !self.atEnd() && self.peek() != "]" {
                                                patternChars.append(self.advance())
                                            }
                                            if !self.atEnd() {
                                                patternChars.append(self.advance())
                                            }
                                        } else {
                                            patternChars.append(self.advance())
                                        }
                                    } else {
                                        if ch == "'" {
                                            patternChars.append(self.advance())
                                            while !self.atEnd() && self.peek() != "'" {
                                                patternChars.append(self.advance())
                                            }
                                            if !self.atEnd() {
                                                patternChars.append(self.advance())
                                            }
                                        } else {
                                            if ch == "\"" {
                                                patternChars.append(self.advance())
                                                while !self.atEnd() && self.peek() != "\"" {
                                                    if self.peek() == "\\" && self.pos + 1 < self.length {
                                                        patternChars.append(self.advance())
                                                    }
                                                    patternChars.append(self.advance())
                                                }
                                                if !self.atEnd() {
                                                    patternChars.append(self.advance())
                                                }
                                            } else {
                                                if _isWhitespace(ch) {
                                                    if extglobDepth > 0 {
                                                        patternChars.append(self.advance())
                                                    } else {
                                                        self.advance()
                                                    }
                                                } else {
                                                    patternChars.append(self.advance())
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
            var pattern: String = patternChars.joined(separator: "")
            if !(!pattern.isEmpty) {
                throw try ParseError(message: "Expected pattern in case statement", pos: self._lexPeekToken().pos)
            }
            self.skipWhitespace()
            var body: Node? = nil
            var isEmptyBody: Bool = try self._lexPeekCaseTerminator() != ""
            if !isEmptyBody {
                self.skipWhitespaceAndNewlines()
                if try !self.atEnd() && !self._lexIsAtReservedWord("esac") {
                    var isAtTerminator: Bool = try self._lexPeekCaseTerminator() != ""
                    if !isAtTerminator {
                        body = try self.parseListUntil(Set(["esac"]))
                        self.skipWhitespace()
                    }
                }
            }
            var terminator: String = try self._consumeCaseTerminator()
            self.skipWhitespaceAndNewlines()
            patterns.append(CasePattern(pattern: pattern, body: body!, terminator: terminator, kind: "pattern"))
        }
        self._clearState(parserstateflagsPstCasepat)
        self.skipWhitespaceAndNewlines()
        if try !self._lexConsumeWord("esac") {
            self._clearState(parserstateflagsPstCasestmt)
            throw try ParseError(message: "Expected 'esac' to close case statement", pos: self._lexPeekToken().pos)
        }
        self._clearState(parserstateflagsPstCasestmt)
        return try Case(word: word!, patterns: patterns, redirects: self._collectRedirects(), kind: "case")
    }

    func parseCoproc() throws -> Coproc? {
        self.skipWhitespace()
        if try !self._lexConsumeWord("coproc") {
            return nil
        }
        self.skipWhitespace()
        var name: String = ""
        var ch: String = ""
        if !self.atEnd() {
            ch = self.peek()
        }
        var body: Node? = nil
        if ch == "{" {
            body = try self.parseBraceGroup()
            if body != nil {
                return Coproc(command: body!, name: name, kind: "coproc")
            }
        }
        if ch == "(" {
            if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                body = try self.parseArithmeticCommand()
                if body != nil {
                    return Coproc(command: body!, name: name, kind: "coproc")
                }
            }
            body = try self.parseSubshell()
            if body != nil {
                return Coproc(command: body!, name: name, kind: "coproc")
            }
        }
        var nextWord: String = try self._lexPeekReservedWord()
        if nextWord != "" && compoundKeywords.contains(nextWord) {
            body = try self.parseCompoundCommand()
            if body != nil {
                return Coproc(command: body!, name: name, kind: "coproc")
            }
        }
        var wordStart: Int = self.pos
        var potentialName: String = self.peekWord()
        if (!potentialName.isEmpty) {
            while !self.atEnd() && !_isMetachar(self.peek()) && !_isQuote(self.peek()) {
                self.advance()
            }
            self.skipWhitespace()
            ch = ""
            if !self.atEnd() {
                ch = self.peek()
            }
            nextWord = try self._lexPeekReservedWord()
            if _isValidIdentifier(potentialName) {
                if ch == "{" {
                    name = potentialName
                    body = try self.parseBraceGroup()
                    if body != nil {
                        return Coproc(command: body!, name: name, kind: "coproc")
                    }
                } else {
                    if ch == "(" {
                        name = potentialName
                        if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
                            body = try self.parseArithmeticCommand()
                        } else {
                            body = try self.parseSubshell()
                        }
                        if body != nil {
                            return Coproc(command: body!, name: name, kind: "coproc")
                        }
                    } else {
                        if nextWord != "" && compoundKeywords.contains(nextWord) {
                            name = potentialName
                            body = try self.parseCompoundCommand()
                            if body != nil {
                                return Coproc(command: body!, name: name, kind: "coproc")
                            }
                        }
                    }
                }
            }
            self.pos = wordStart
        }
        body = try self.parseCommand()
        if body != nil {
            return Coproc(command: body!, name: name, kind: "coproc")
        }
        throw ParseError(message: "Expected command after coproc", pos: self.pos)
    }

    func parseFunction() throws -> Function? {
        self.skipWhitespace()
        if self.atEnd() {
            return nil
        }
        var savedPos: Int = self.pos
        var name: String = ""
        var body: Node? = nil
        if try self._lexIsAtReservedWord("function") {
            try self._lexConsumeWord("function")
            self.skipWhitespace()
            name = self.peekWord()
            if name == "" {
                self.pos = savedPos
                return nil
            }
            self.consumeWord(name)
            self.skipWhitespace()
            if !self.atEnd() && self.peek() == "(" {
                if self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == ")" {
                    self.advance()
                    self.advance()
                }
            }
            self.skipWhitespaceAndNewlines()
            body = try self._parseCompoundCommand()
            if body == nil {
                throw ParseError(message: "Expected function body", pos: self.pos)
            }
            return Function(name: name, body: body!, kind: "function")
        }
        name = self.peekWord()
        if name == "" || reservedWords.contains(name) {
            return nil
        }
        if _looksLikeAssignment(name) {
            return nil
        }
        self.skipWhitespace()
        var nameStart: Int = self.pos
        while !self.atEnd() && !_isMetachar(self.peek()) && !_isQuote(self.peek()) && !_isParen(self.peek()) {
            self.advance()
        }
        name = _substring(self.source, nameStart, self.pos)
        if !(!name.isEmpty) {
            self.pos = savedPos
            return nil
        }
        var braceDepth: Int = 0
        var i: Int = 0
        while i < name.count {
            if _isExpansionStart(name, i, "${") {
                braceDepth += 1
                i += 2
                continue
            }
            if String(_charAt(name, i)) == "}" {
                braceDepth -= 1
            }
            i += 1
        }
        if braceDepth > 0 {
            self.pos = savedPos
            return nil
        }
        var posAfterName: Int = self.pos
        self.skipWhitespace()
        var hasWhitespace: Bool = self.pos > posAfterName
        if !hasWhitespace && (!name.isEmpty) && "*?@+!$".contains(String(_charAt(name, name.count - 1))) {
            self.pos = savedPos
            return nil
        }
        if self.atEnd() || self.peek() != "(" {
            self.pos = savedPos
            return nil
        }
        self.advance()
        self.skipWhitespace()
        if self.atEnd() || self.peek() != ")" {
            self.pos = savedPos
            return nil
        }
        self.advance()
        self.skipWhitespaceAndNewlines()
        body = try self._parseCompoundCommand()
        if body == nil {
            throw ParseError(message: "Expected function body", pos: self.pos)
        }
        return Function(name: name, body: body!, kind: "function")
    }

    func _parseCompoundCommand() throws -> Node? {
        var result: Node? = try self.parseBraceGroup()
        if result != nil {
            return result!
        }
        if !self.atEnd() && self.peek() == "(" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
            result = try self.parseArithmeticCommand()
            if result != nil {
                return result!
            }
        }
        result = try self.parseSubshell()
        if result != nil {
            return result!
        }
        result = try self.parseConditionalExpr()
        if result != nil {
            return result!
        }
        result = try self.parseIf()
        if result != nil {
            return result!
        }
        result = try self.parseWhile()
        if result != nil {
            return result!
        }
        result = try self.parseUntil()
        if result != nil {
            return result!
        }
        result = try self.parseFor()
        if result != nil {
            return result!
        }
        result = try self.parseCase()
        if result != nil {
            return result!
        }
        result = try self.parseSelect()
        if result != nil {
            return result!
        }
        return nil
    }

    func _atListUntilTerminator(_ stopWords: Set<String>) throws -> Bool {
        if self.atEnd() {
            return true
        }
        if self.peek() == ")" {
            return true
        }
        if self.peek() == "}" {
            var nextPos: Int = self.pos + 1
            if nextPos >= self.length || _isWordEndContext(String(_charAt(self.source, nextPos))) {
                return true
            }
        }
        var reserved: String = try self._lexPeekReservedWord()
        if reserved != "" && stopWords.contains(reserved) {
            return true
        }
        if try self._lexPeekCaseTerminator() != "" {
            return true
        }
        return false
    }

    func parseListUntil(_ stopWords: Set<String>) throws -> Node? {
        self.skipWhitespaceAndNewlines()
        var reserved: String = try self._lexPeekReservedWord()
        if reserved != "" && stopWords.contains(reserved) {
            return nil
        }
        var pipeline: Node? = try self.parsePipeline()
        if pipeline == nil {
            return nil
        }
        var parts: [Node] = [pipeline!]
        while true {
            self.skipWhitespace()
            var op: String = try self.parseListOperator()
            if op == "" {
                if !self.atEnd() && self.peek() == "\n" {
                    self.advance()
                    self._gatherHeredocBodies()
                    if self._cmdsubHeredocEnd != -1 && self._cmdsubHeredocEnd > self.pos {
                        self.pos = self._cmdsubHeredocEnd
                        self._cmdsubHeredocEnd = -1
                    }
                    self.skipWhitespaceAndNewlines()
                    if try self._atListUntilTerminator(stopWords) {
                        break
                    }
                    var nextOp: String = try self._peekListOperator()
                    if nextOp == "&" || nextOp == ";" {
                        break
                    }
                    op = "\n"
                } else {
                    break
                }
            }
            if op == "" {
                break
            }
            if op == ";" {
                self.skipWhitespaceAndNewlines()
                if try self._atListUntilTerminator(stopWords) {
                    break
                }
                parts.append(Operator(op: op, kind: "operator"))
            } else {
                if op == "&" {
                    parts.append(Operator(op: op, kind: "operator"))
                    self.skipWhitespaceAndNewlines()
                    if try self._atListUntilTerminator(stopWords) {
                        break
                    }
                } else {
                    if op == "&&" || op == "||" {
                        parts.append(Operator(op: op, kind: "operator"))
                        self.skipWhitespaceAndNewlines()
                    } else {
                        parts.append(Operator(op: op, kind: "operator"))
                    }
                }
            }
            if try self._atListUntilTerminator(stopWords) {
                break
            }
            pipeline = try self.parsePipeline()
            if pipeline == nil {
                throw ParseError(message: "Expected command after " + op, pos: self.pos)
            }
            parts.append(pipeline!)
        }
        if parts.count == 1 {
            return parts[0]
        }
        return List(parts: parts, kind: "list")
    }

    func parseCompoundCommand() throws -> Node? {
        self.skipWhitespace()
        if self.atEnd() {
            return nil
        }
        var ch: String = self.peek()
        var result: Node? = nil
        if ch == "(" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "(" {
            result = try self.parseArithmeticCommand()
            if result != nil {
                return result!
            }
        }
        if ch == "(" {
            return try self.parseSubshell()
        }
        if ch == "{" {
            result = try self.parseBraceGroup()
            if result != nil {
                return result!
            }
        }
        if ch == "[" && self.pos + 1 < self.length && String(_charAt(self.source, self.pos + 1)) == "[" {
            result = try self.parseConditionalExpr()
            if result != nil {
                return result!
            }
        }
        var reserved: String = try self._lexPeekReservedWord()
        if reserved == "" && self._inProcessSub {
            var word: String = self.peekWord()
            if word != "" && word.count > 1 && String(_charAt(word, 0)) == "}" {
                var keywordWord: String = String(word.dropFirst(1))
                if reservedWords.contains(keywordWord) || keywordWord == "{" || keywordWord == "}" || keywordWord == "[[" || keywordWord == "]]" || keywordWord == "!" || keywordWord == "time" {
                    reserved = keywordWord
                }
            }
        }
        if reserved == "fi" || reserved == "then" || reserved == "elif" || reserved == "else" || reserved == "done" || reserved == "esac" || reserved == "do" || reserved == "in" {
            throw try ParseError(message: "Unexpected reserved word '\\(reserved)'", pos: self._lexPeekToken().pos)
        }
        if reserved == "if" {
            return try self.parseIf()
        }
        if reserved == "while" {
            return try self.parseWhile()
        }
        if reserved == "until" {
            return try self.parseUntil()
        }
        if reserved == "for" {
            return try self.parseFor()
        }
        if reserved == "select" {
            return try self.parseSelect()
        }
        if reserved == "case" {
            return try self.parseCase()
        }
        if reserved == "function" {
            return try self.parseFunction()
        }
        if reserved == "coproc" {
            return try self.parseCoproc()
        }
        var `func`: Function? = try self.parseFunction()
        if `func` != nil {
            return `func`!
        }
        return try self.parseCommand()
    }

    func parsePipeline() throws -> Node? {
        self.skipWhitespace()
        var prefixOrder: String = ""
        var timePosix: Bool = false
        if try self._lexIsAtReservedWord("time") {
            try self._lexConsumeWord("time")
            prefixOrder = "time"
            self.skipWhitespace()
            var saved: Int = 0
            if !self.atEnd() && self.peek() == "-" {
                saved = self.pos
                self.advance()
                if !self.atEnd() && self.peek() == "p" {
                    self.advance()
                    if self.atEnd() || _isMetachar(self.peek()) {
                        timePosix = true
                    } else {
                        self.pos = saved
                    }
                } else {
                    self.pos = saved
                }
            }
            self.skipWhitespace()
            if !self.atEnd() && _startsWithAt(self.source, self.pos, "--") {
                if self.pos + 2 >= self.length || _isWhitespace(String(_charAt(self.source, self.pos + 2))) {
                    self.advance()
                    self.advance()
                    timePosix = true
                    self.skipWhitespace()
                }
            }
            while try self._lexIsAtReservedWord("time") {
                try self._lexConsumeWord("time")
                self.skipWhitespace()
                if !self.atEnd() && self.peek() == "-" {
                    saved = self.pos
                    self.advance()
                    if !self.atEnd() && self.peek() == "p" {
                        self.advance()
                        if self.atEnd() || _isMetachar(self.peek()) {
                            timePosix = true
                        } else {
                            self.pos = saved
                        }
                    } else {
                        self.pos = saved
                    }
                }
            }
            self.skipWhitespace()
            if !self.atEnd() && self.peek() == "!" {
                if self.pos + 1 >= self.length || _isNegationBoundary(String(_charAt(self.source, self.pos + 1))) && !self._isBangFollowedByProcsub() {
                    self.advance()
                    prefixOrder = "time_negation"
                    self.skipWhitespace()
                }
            }
        } else {
            if !self.atEnd() && self.peek() == "!" {
                if self.pos + 1 >= self.length || _isNegationBoundary(String(_charAt(self.source, self.pos + 1))) && !self._isBangFollowedByProcsub() {
                    self.advance()
                    self.skipWhitespace()
                    var inner: Node? = try self.parsePipeline()
                    if inner != nil && inner!.kind == "negation" {
                        if (inner! as! Negation).pipeline != nil {
                            return (inner! as! Negation).pipeline
                        } else {
                            return Command(words: [], redirects: [], kind: "command")
                        }
                    }
                    return Negation(pipeline: inner!, kind: "negation")
                }
            }
        }
        var result: Node? = try self._parseSimplePipeline()
        if prefixOrder == "time" {
            result = Time(pipeline: result!, posix: timePosix, kind: "time")
        } else {
            if prefixOrder == "negation" {
                result = Negation(pipeline: result!, kind: "negation")
            } else {
                if prefixOrder == "time_negation" {
                    result = Time(pipeline: result!, posix: timePosix, kind: "time")
                    result = Negation(pipeline: result!, kind: "negation")
                } else {
                    if prefixOrder == "negation_time" {
                        result = Time(pipeline: result!, posix: timePosix, kind: "time")
                        result = Negation(pipeline: result!, kind: "negation")
                    } else {
                        if result == nil {
                            return nil
                        }
                    }
                }
            }
        }
        return result!
    }

    func _parseSimplePipeline() throws -> Node? {
        var cmd: Node? = try self.parseCompoundCommand()
        if cmd == nil {
            return nil
        }
        var commands: [Node] = [cmd!]
        while true {
            self.skipWhitespace()
            let _tuple42 = try self._lexPeekOperator()
            var tokenType: Int = _tuple42.0
            var value: String = _tuple42.1
            if tokenType == 0 {
                break
            }
            if tokenType != tokentypePipe && tokenType != tokentypePipeAmp {
                break
            }
            try self._lexNextToken()
            var isPipeBoth: Bool = tokenType == tokentypePipeAmp
            self.skipWhitespaceAndNewlines()
            if isPipeBoth {
                commands.append(PipeBoth(kind: "pipe-both"))
            }
            cmd = try self.parseCompoundCommand()
            if cmd == nil {
                throw ParseError(message: "Expected command after |", pos: self.pos)
            }
            commands.append(cmd!)
        }
        if commands.count == 1 {
            return commands[0]
        }
        return Pipeline(commands: commands, kind: "pipeline")
    }

    func parseListOperator() throws -> String {
        self.skipWhitespace()
        let _tuple43 = try self._lexPeekOperator()
        var tokenType: Int = _tuple43.0
        var _: String = _tuple43.1
        if tokenType == 0 {
            return ""
        }
        if tokenType == tokentypeAndAnd {
            try self._lexNextToken()
            return "&&"
        }
        if tokenType == tokentypeOrOr {
            try self._lexNextToken()
            return "||"
        }
        if tokenType == tokentypeSemi {
            try self._lexNextToken()
            return ";"
        }
        if tokenType == tokentypeAmp {
            try self._lexNextToken()
            return "&"
        }
        return ""
    }

    func _peekListOperator() throws -> String {
        var savedPos: Int = self.pos
        var op: String = try self.parseListOperator()
        self.pos = savedPos
        return op
    }

    func parseList(_ newlineAsSeparator: Bool) throws -> Node? {
        if newlineAsSeparator {
            self.skipWhitespaceAndNewlines()
        } else {
            self.skipWhitespace()
        }
        var pipeline: Node? = try self.parsePipeline()
        if pipeline == nil {
            return nil
        }
        var parts: [Node] = [pipeline!]
        if try self._inState(parserstateflagsPstEoftoken) && self._atEofToken() {
            return (parts.count == 1 ? parts[0] : List(parts: parts, kind: "list"))
        }
        while true {
            self.skipWhitespace()
            var op: String = try self.parseListOperator()
            if op == "" {
                if !self.atEnd() && self.peek() == "\n" {
                    if !newlineAsSeparator {
                        break
                    }
                    self.advance()
                    self._gatherHeredocBodies()
                    if self._cmdsubHeredocEnd != -1 && self._cmdsubHeredocEnd > self.pos {
                        self.pos = self._cmdsubHeredocEnd
                        self._cmdsubHeredocEnd = -1
                    }
                    self.skipWhitespaceAndNewlines()
                    if self.atEnd() || self._atListTerminatingBracket() {
                        break
                    }
                    var nextOp: String = try self._peekListOperator()
                    if nextOp == "&" || nextOp == ";" {
                        break
                    }
                    op = "\n"
                } else {
                    break
                }
            }
            if op == "" {
                break
            }
            parts.append(Operator(op: op, kind: "operator"))
            if op == "&&" || op == "||" {
                self.skipWhitespaceAndNewlines()
            } else {
                if op == "&" {
                    self.skipWhitespace()
                    if self.atEnd() || self._atListTerminatingBracket() {
                        break
                    }
                    if self.peek() == "\n" {
                        if newlineAsSeparator {
                            self.skipWhitespaceAndNewlines()
                            if self.atEnd() || self._atListTerminatingBracket() {
                                break
                            }
                        } else {
                            break
                        }
                    }
                } else {
                    if op == ";" {
                        self.skipWhitespace()
                        if self.atEnd() || self._atListTerminatingBracket() {
                            break
                        }
                        if self.peek() == "\n" {
                            if newlineAsSeparator {
                                self.skipWhitespaceAndNewlines()
                                if self.atEnd() || self._atListTerminatingBracket() {
                                    break
                                }
                            } else {
                                break
                            }
                        }
                    }
                }
            }
            pipeline = try self.parsePipeline()
            if pipeline == nil {
                throw ParseError(message: "Expected command after " + op, pos: self.pos)
            }
            parts.append(pipeline!)
            if try self._inState(parserstateflagsPstEoftoken) && self._atEofToken() {
                break
            }
        }
        if parts.count == 1 {
            return parts[0]
        }
        return List(parts: parts, kind: "list")
    }

    func parseComment() -> Node? {
        if self.atEnd() || self.peek() != "#" {
            return nil
        }
        var start: Int = self.pos
        while !self.atEnd() && self.peek() != "\n" {
            self.advance()
        }
        var text: String = _substring(self.source, start, self.pos)
        return Comment(text: text, kind: "comment")
    }

    func parse() throws -> [Node] {
        var source: String = self.source.trimmingCharacters(in: .whitespacesAndNewlines)
        if !(!source.isEmpty) {
            return [Empty(kind: "empty")]
        }
        var results: [Node] = []
        while true {
            self.skipWhitespace()
            while !self.atEnd() && self.peek() == "\n" {
                self.advance()
            }
            if self.atEnd() {
                break
            }
            var comment: Node? = self.parseComment()
            if !comment != nil {
                break
            }
        }
        while !self.atEnd() {
            var result: Node? = try self.parseList(false)
            if result != nil {
                results.append(result!)
            }
            self.skipWhitespace()
            var foundNewline: Bool = false
            while !self.atEnd() && self.peek() == "\n" {
                foundNewline = true
                self.advance()
                self._gatherHeredocBodies()
                if self._cmdsubHeredocEnd != -1 && self._cmdsubHeredocEnd > self.pos {
                    self.pos = self._cmdsubHeredocEnd
                    self._cmdsubHeredocEnd = -1
                }
                self.skipWhitespace()
            }
            if !foundNewline && !self.atEnd() {
                throw ParseError(message: "Syntax error", pos: self.pos)
            }
        }
        if !(!results.isEmpty) {
            return [Empty(kind: "empty")]
        }
        if self._sawNewlineInSingleQuote && (!self.source.isEmpty) && String(_charAt(self.source, self.source.count - 1)) == "\\" && !(self.source.count >= 3 && String(self.source[self.source.index(self.source.startIndex, offsetBy: self.source.count - 3)..<self.source.index(self.source.startIndex, offsetBy: min(self.source.count - 1, self.source.count))]) == "\\\n") {
            if !self._lastWordOnOwnLine(results) {
                self._stripTrailingBackslashFromLastWord(results)
            }
        }
        return results
    }

    func _lastWordOnOwnLine(_ nodes: [Node]) -> Bool {
        return nodes.count >= 2
    }

    func _stripTrailingBackslashFromLastWord(_ nodes: [Node]) {
        if !(!nodes.isEmpty) {
            return
        }
        var lastNode: Node = nodes[nodes.count - 1]
        var lastWord: Word? = self._findLastWord(lastNode)
        if lastWord != nil && lastWord!.value.hasSuffix("\\") {
            lastWord!.value = _substring(lastWord!.value, 0, lastWord!.value.count - 1)
            if !(!lastWord!.value.isEmpty) && (lastNode is Command) && (!(lastNode as! Command).words.isEmpty) {
                (lastNode as! Command).words.removeLast()
            }
        }
    }

    func _findLastWord(_ node: Node) -> Word? {
        switch node {
        case let node as Word:
            return node
        default:
            break
        }
        switch node {
        case let node as Command:
            if (!node.words.isEmpty) {
                var lastWord: Word = node.words[node.words.count - 1]
                if lastWord.value.hasSuffix("\\") {
                    return lastWord
                }
            }
            if (!node.redirects.isEmpty) {
                var lastRedirect: Node = node.redirects[node.redirects.count - 1]
                switch lastRedirect {
                case let lastRedirect as Redirect:
                    return lastRedirect.target
                default:
                    break
                }
            }
            if (!node.words.isEmpty) {
                return node.words[node.words.count - 1]
            }
        default:
            break
        }
        switch node {
        case let node as Pipeline:
            if (!node.commands.isEmpty) {
                return self._findLastWord(node.commands[node.commands.count - 1])
            }
        default:
            break
        }
        switch node {
        case let node as List:
            if (!node.parts.isEmpty) {
                return self._findLastWord(node.parts[node.parts.count - 1])
            }
        default:
            break
        }
        return nil
    }
}

func _isHexDigit(_ c: String) -> Bool {
    return c >= "0" && c <= "9" || c >= "a" && c <= "f" || c >= "A" && c <= "F"
}

func _isOctalDigit(_ c: String) -> Bool {
    return c >= "0" && c <= "7"
}

func _getAnsiEscape(_ c: String) -> Int {
    return (ansiCEscapes[c] ?? -1)
}

func _isWhitespace(_ c: String) -> Bool {
    return c == " " || c == "\t" || c == "\n"
}

func _stringToBytes(_ s: String) -> [UInt8] {
    return Swift.Array(Swift.Array(s.utf8))
}

func _isWhitespaceNoNewline(_ c: String) -> Bool {
    return c == " " || c == "\t"
}

func _substring(_ s: String, _ start: Int, _ end: Int) -> String {
    return String(s[s.index(s.startIndex, offsetBy: start)..<s.index(s.startIndex, offsetBy: min(end, s.count))])
}

func _startsWithAt(_ s: String, _ pos: Int, _ `prefix`: String) -> Bool {
    return String(s.dropFirst(pos)).hasPrefix(`prefix`)
}

func _countConsecutiveDollarsBefore(_ s: String, _ pos: Int) -> Int {
    var count: Int = 0
    var k: Int = pos - 1
    while k >= 0 && String(_charAt(s, k)) == "$" {
        var bsCount: Int = 0
        var j: Int = k - 1
        while j >= 0 && String(_charAt(s, j)) == "\\" {
            bsCount += 1
            j -= 1
        }
        if bsCount % 2 == 1 {
            break
        }
        count += 1
        k -= 1
    }
    return count
}

func _isExpansionStart(_ s: String, _ pos: Int, _ delimiter: String) -> Bool {
    if !_startsWithAt(s, pos, delimiter) {
        return false
    }
    return _countConsecutiveDollarsBefore(s, pos) % 2 == 0
}

func _sublist(_ lst: [Node], _ start: Int, _ end: Int) -> [Node] {
    return Swift.Array(lst[(start)..<(end)])
}

func _repeatStr(_ s: String, _ n: Int) -> String {
    var result: [String] = []
    var i: Int = 0
    while i < n {
        result.append(s)
        i += 1
    }
    return result.joined(separator: "")
}

func _stripLineContinuationsCommentAware(_ text: String) -> String {
    var result: [String] = []
    var i: Int = 0
    var inComment: Bool = false
    var quote: QuoteState = newQuoteState()
    while i < text.count {
        var c: String = String(_charAt(text, i))
        if c == "\\" && i + 1 < text.count && String(_charAt(text, i + 1)) == "\n" {
            var numPrecedingBackslashes: Int = 0
            var j: Int = i - 1
            while j >= 0 && String(_charAt(text, j)) == "\\" {
                numPrecedingBackslashes += 1
                j -= 1
            }
            if numPrecedingBackslashes % 2 == 0 {
                if inComment {
                    result.append("\n")
                }
                i += 2
                inComment = false
                continue
            }
        }
        if c == "\n" {
            inComment = false
            result.append(c)
            i += 1
            continue
        }
        if c == "'" && !quote.double && !inComment {
            quote.single = !quote.single
        } else {
            if c == "\"" && !quote.single && !inComment {
                quote.double = !quote.double
            } else {
                if c == "#" && !quote.single && !inComment {
                    inComment = true
                }
            }
        }
        result.append(c)
        i += 1
    }
    return result.joined(separator: "")
}

func _appendRedirects(_ base: String, _ redirects: [Node]?) -> String {
    if (redirects != nil && !redirects!.isEmpty) {
        var parts: [String] = []
        for r in redirects! {
            parts.append(r.toSexp())
        }
        return base + " " + parts.joined(separator: " ")
    }
    return base
}

func _formatArithVal(_ s: String) -> String {
    var w: Word = Word(value: s, parts: [], kind: "word")
    var val: String = w._expandAllAnsiCQuotes(s)
    val = w._stripLocaleStringDollars(val)
    val = w._formatCommandSubstitutions(val, false)
    val = val.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
    val = val.replacingOccurrences(of: "\n", with: "\\n").replacingOccurrences(of: "\t", with: "\\t")
    return val
}

func _consumeSingleQuote(_ s: String, _ start: Int) -> (Int, [String]) {
    var chars: [String] = ["'"]
    var i: Int = start + 1
    while i < s.count && String(_charAt(s, i)) != "'" {
        chars.append(String(_charAt(s, i)))
        i += 1
    }
    if i < s.count {
        chars.append(String(_charAt(s, i)))
        i += 1
    }
    return (i, chars)
}

func _consumeDoubleQuote(_ s: String, _ start: Int) -> (Int, [String]) {
    var chars: [String] = ["\""]
    var i: Int = start + 1
    while i < s.count && String(_charAt(s, i)) != "\"" {
        if String(_charAt(s, i)) == "\\" && i + 1 < s.count {
            chars.append(String(_charAt(s, i)))
            i += 1
        }
        chars.append(String(_charAt(s, i)))
        i += 1
    }
    if i < s.count {
        chars.append(String(_charAt(s, i)))
        i += 1
    }
    return (i, chars)
}

func _hasBracketClose(_ s: String, _ start: Int, _ depth: Int) -> Bool {
    var i: Int = start
    while i < s.count {
        if String(_charAt(s, i)) == "]" {
            return true
        }
        if String(_charAt(s, i)) == "|" || String(_charAt(s, i)) == ")" && depth == 0 {
            return false
        }
        i += 1
    }
    return false
}

func _consumeBracketClass(_ s: String, _ start: Int, _ depth: Int) -> (Int, [String], Bool) {
    var scanPos: Int = start + 1
    if scanPos < s.count && String(_charAt(s, scanPos)) == "!" || String(_charAt(s, scanPos)) == "^" {
        scanPos += 1
    }
    if scanPos < s.count && String(_charAt(s, scanPos)) == "]" {
        if _hasBracketClose(s, scanPos + 1, depth) {
            scanPos += 1
        }
    }
    var isBracket: Bool = false
    while scanPos < s.count {
        if String(_charAt(s, scanPos)) == "]" {
            isBracket = true
            break
        }
        if String(_charAt(s, scanPos)) == ")" && depth == 0 {
            break
        }
        if String(_charAt(s, scanPos)) == "|" && depth == 0 {
            break
        }
        scanPos += 1
    }
    if !isBracket {
        return (start + 1, ["["], false)
    }
    var chars: [String] = ["["]
    var i: Int = start + 1
    if i < s.count && String(_charAt(s, i)) == "!" || String(_charAt(s, i)) == "^" {
        chars.append(String(_charAt(s, i)))
        i += 1
    }
    if i < s.count && String(_charAt(s, i)) == "]" {
        if _hasBracketClose(s, i + 1, depth) {
            chars.append(String(_charAt(s, i)))
            i += 1
        }
    }
    while i < s.count && String(_charAt(s, i)) != "]" {
        chars.append(String(_charAt(s, i)))
        i += 1
    }
    if i < s.count {
        chars.append(String(_charAt(s, i)))
        i += 1
    }
    return (i, chars, true)
}

func _formatCondBody(_ node: Node) -> String {
    var kind: String = node.kind
    if kind == "unary-test" {
        var operandVal: String = (node as! UnaryTest).operand.getCondFormattedValue()
        return (node as! UnaryTest).op + " " + operandVal
    }
    if kind == "binary-test" {
        var leftVal: String = (node as! BinaryTest).`left`.getCondFormattedValue()
        var rightVal: String = (node as! BinaryTest).`right`.getCondFormattedValue()
        return leftVal + " " + (node as! BinaryTest).op + " " + rightVal
    }
    if kind == "cond-and" {
        return _formatCondBody((node as! CondAnd).`left`) + " && " + _formatCondBody((node as! CondAnd).`right`)
    }
    if kind == "cond-or" {
        return _formatCondBody((node as! CondOr).`left`) + " || " + _formatCondBody((node as! CondOr).`right`)
    }
    if kind == "cond-not" {
        return "! " + _formatCondBody((node as! CondNot).operand)
    }
    if kind == "cond-paren" {
        return "( " + _formatCondBody((node as! CondParen).inner) + " )"
    }
    return ""
}

func _startsWithSubshell(_ node: Node) -> Bool {
    switch node {
    case let node as Subshell:
        return true
    default:
        break
    }
    switch node {
    case let node as List:
        for p in node.parts {
            if p.kind != "operator" {
                return _startsWithSubshell(p)
            }
        }
        return false
    default:
        break
    }
    switch node {
    case let node as Pipeline:
        if (!node.commands.isEmpty) {
            return _startsWithSubshell(node.commands[0])
        }
        return false
    default:
        break
    }
    return false
}

func _formatCmdsubNode(_ node: Node, _ indent: Int, _ inProcsub: Bool, _ compactRedirects: Bool, _ procsubFirst: Bool) -> String {
    if node == nil {
        return ""
    }
    var sp: String = _repeatStr(" ", indent)
    var innerSp: String = _repeatStr(" ", indent + 4)
    switch node {
    case let node as ArithEmpty:
        return ""
    default:
        break
    }
    switch node {
    case let node as Command:
        var parts: [String] = []
        for w in node.words {
            var val: String = w._expandAllAnsiCQuotes(w.value)
            val = w._stripLocaleStringDollars(val)
            val = w._normalizeArrayWhitespace(val)
            val = w._formatCommandSubstitutions(val, false)
            parts.append(val)
        }
        var heredocs: [HereDoc] = []
        for r in node.redirects {
            switch r {
            case let r as HereDoc:
                heredocs.append(r)
            default:
                break
            }
        }
        for r in node.redirects {
            parts.append(_formatRedirect(r, compactRedirects, true))
        }
        var result: String = ""
        if compactRedirects && (!node.words.isEmpty) && (!node.redirects.isEmpty) {
            var wordParts: [String] = Swift.Array(parts[..<(node.words.count)])
            var redirectParts: [String] = Swift.Array(parts[(node.words.count)...])
            result = wordParts.joined(separator: " ") + redirectParts.joined(separator: "")
        } else {
            result = parts.joined(separator: " ")
        }
        for h in heredocs {
            result = result + _formatHeredocBody(h)
        }
        return result
    default:
        break
    }
    switch node {
    case let node as Pipeline:
        var cmds: [(Node, Bool)] = []
        var i: Int = 0
        var cmd: Node? = nil
        var needsRedirect: Bool = false
        while i < node.commands.count {
            cmd = node.commands[i]
            switch cmd! {
            case let cmd as PipeBoth:
                i += 1
                continue
            default:
                break
            }
            needsRedirect = i + 1 < node.commands.count && node.commands[i + 1].kind == "pipe-both"
            cmds.append((cmd!, needsRedirect))
            i += 1
        }
        var resultParts: [String] = []
        var idx: Int = 0
        while idx < cmds.count {
            do {
                let _entry: (Node, Bool) = cmds[idx]
                cmd = _entry.0
                needsRedirect = _entry.1
            }
            var formatted: String = _formatCmdsubNode(cmd!, indent, inProcsub, false, procsubFirst && idx == 0)
            var isLast: Bool = idx == cmds.count - 1
            var hasHeredoc: Bool = false
            if cmd!.kind == "command" && (!(cmd! as! Command).redirects.isEmpty) {
                for r in (cmd! as! Command).redirects {
                    switch r {
                    case let r as HereDoc:
                        hasHeredoc = true
                        break
                    default:
                        break
                    }
                }
            }
            var firstNl: Int = 0
            if needsRedirect {
                if hasHeredoc {
                    firstNl = (formatted.range(of: "\n").map { formatted.distance(from: formatted.startIndex, to: $0.lowerBound) } ?? -1)
                    if firstNl != -1 {
                        formatted = String(formatted.prefix(firstNl)) + " 2>&1" + String(formatted.dropFirst(firstNl))
                    } else {
                        formatted = formatted + " 2>&1"
                    }
                } else {
                    formatted = formatted + " 2>&1"
                }
            }
            if !isLast && hasHeredoc {
                firstNl = (formatted.range(of: "\n").map { formatted.distance(from: formatted.startIndex, to: $0.lowerBound) } ?? -1)
                if firstNl != -1 {
                    formatted = String(formatted.prefix(firstNl)) + " |" + String(formatted.dropFirst(firstNl))
                }
                resultParts.append(formatted)
            } else {
                resultParts.append(formatted)
            }
            idx += 1
        }
        var compactPipe: Bool = inProcsub && (!cmds.isEmpty) && cmds[0].0.kind == "subshell"
        var result: String = ""
        idx = 0
        while idx < resultParts.count {
            var part: String = resultParts[idx]
            if idx > 0 {
                if result.hasSuffix("\n") {
                    result = result + "  " + part
                } else {
                    if compactPipe {
                        result = result + "|" + part
                    } else {
                        result = result + " | " + part
                    }
                }
            } else {
                result = part
            }
            idx += 1
        }
        return result
    default:
        break
    }
    switch node {
    case let node as List:
        var hasHeredoc: Bool = false
        for p in node.parts {
            if p.kind == "command" && (!(p as! Command).redirects.isEmpty) {
                for r in (p as! Command).redirects {
                    switch r {
                    case let r as HereDoc:
                        hasHeredoc = true
                        break
                    default:
                        break
                    }
                }
            } else {
                switch p {
                case let p as Pipeline:
                    for cmd in p.commands {
                        if cmd.kind == "command" && (!(cmd as! Command).redirects.isEmpty) {
                            for r in (cmd as! Command).redirects {
                                switch r {
                                case let r as HereDoc:
                                    hasHeredoc = true
                                    break
                                default:
                                    break
                                }
                            }
                        }
                        if hasHeredoc {
                            break
                        }
                    }
                default:
                    break
                }
            }
        }
        var result: [String] = []
        var skippedSemi: Bool = false
        var cmdCount: Int = 0
        for p in node.parts {
            switch p {
            case let p as Operator:
                if p.op == ";" {
                    if (!result.isEmpty) && result[result.count - 1].hasSuffix("\n") {
                        skippedSemi = true
                        continue
                    }
                    if result.count >= 3 && result[result.count - 2] == "\n" && result[result.count - 3].hasSuffix("\n") {
                        skippedSemi = true
                        continue
                    }
                    result.append(";")
                    skippedSemi = false
                } else {
                    if p.op == "\n" {
                        if (!result.isEmpty) && result[result.count - 1] == ";" {
                            skippedSemi = false
                            continue
                        }
                        if (!result.isEmpty) && result[result.count - 1].hasSuffix("\n") {
                            result.append((skippedSemi ? " " : "\n"))
                            skippedSemi = false
                            continue
                        }
                        result.append("\n")
                        skippedSemi = false
                    } else {
                        var last: String = ""
                        var firstNl: Int = 0
                        if p.op == "&" {
                            if (!result.isEmpty) && result[result.count - 1].contains("<<") && result[result.count - 1].contains("\n") {
                                last = result[result.count - 1]
                                if last.contains(" |") || last.hasPrefix("|") {
                                    result[result.count - 1] = last + " &"
                                } else {
                                    firstNl = (last.range(of: "\n").map { last.distance(from: last.startIndex, to: $0.lowerBound) } ?? -1)
                                    result[result.count - 1] = String(last.prefix(firstNl)) + " &" + String(last.dropFirst(firstNl))
                                }
                            } else {
                                result.append(" &")
                            }
                        } else {
                            if (!result.isEmpty) && result[result.count - 1].contains("<<") && result[result.count - 1].contains("\n") {
                                last = result[result.count - 1]
                                firstNl = (last.range(of: "\n").map { last.distance(from: last.startIndex, to: $0.lowerBound) } ?? -1)
                                result[result.count - 1] = String(last.prefix(firstNl)) + " " + p.op + " " + String(last.dropFirst(firstNl))
                            } else {
                                result.append(" " + p.op)
                            }
                        }
                    }
                }
            default:
                if (!result.isEmpty) && !(result[result.count - 1].hasSuffix(" ") || result[result.count - 1].hasSuffix("\n")) {
                    result.append(" ")
                }
                var formattedCmd: String = _formatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0)
                if result.count > 0 {
                    var last: String = result[result.count - 1]
                    if last.contains(" || \n") || last.contains(" && \n") {
                        formattedCmd = " " + formattedCmd
                    }
                }
                if skippedSemi {
                    formattedCmd = " " + formattedCmd
                    skippedSemi = false
                }
                result.append(formattedCmd)
                cmdCount += 1
            }
        }
        var s: String = result.joined(separator: "")
        if s.contains(" &\n") && s.hasSuffix("\n") {
            return s + " "
        }
        while s.hasSuffix(";") {
            s = _substring(s, 0, s.count - 1)
        }
        if !hasHeredoc {
            while s.hasSuffix("\n") {
                s = _substring(s, 0, s.count - 1)
            }
        }
        return s
    default:
        break
    }
    switch node {
    case let node as If:
        var cond: String = _formatCmdsubNode(node.condition, indent, false, false, false)
        var thenBody: String = _formatCmdsubNode(node.thenBody, indent + 4, false, false, false)
        var result: String = "if " + cond + "; then\n" + innerSp + thenBody + ";"
        if node.elseBody != nil {
            var elseBody: String = _formatCmdsubNode(node.elseBody, indent + 4, false, false, false)
            result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";"
        }
        result = result + "\n" + sp + "fi"
        return result
    default:
        break
    }
    switch node {
    case let node as While:
        var cond: String = _formatCmdsubNode(node.condition, indent, false, false, false)
        var body: String = _formatCmdsubNode(node.body, indent + 4, false, false, false)
        var result: String = "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"
        if (!node.redirects.isEmpty) {
            for r in node.redirects {
                result = result + " " + _formatRedirect(r, false, false)
            }
        }
        return result
    default:
        break
    }
    switch node {
    case let node as Until:
        var cond: String = _formatCmdsubNode(node.condition, indent, false, false, false)
        var body: String = _formatCmdsubNode(node.body, indent + 4, false, false, false)
        var result: String = "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"
        if (!node.redirects.isEmpty) {
            for r in node.redirects {
                result = result + " " + _formatRedirect(r, false, false)
            }
        }
        return result
    default:
        break
    }
    switch node {
    case let node as For:
        var `var`: String = node.`var`
        var body: String = _formatCmdsubNode(node.body, indent + 4, false, false, false)
        var result: String = ""
        if node.words != nil {
            var wordVals: [String] = []
            for w in node.words! {
                wordVals.append(w.value)
            }
            var words: String = wordVals.joined(separator: " ")
            if (!words.isEmpty) {
                result = "for " + `var` + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
            } else {
                result = "for " + `var` + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
            }
        } else {
            result = "for " + `var` + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
        }
        if (!node.redirects.isEmpty) {
            for r in node.redirects {
                result = result + " " + _formatRedirect(r, false, false)
            }
        }
        return result
    default:
        break
    }
    switch node {
    case let node as ForArith:
        var body: String = _formatCmdsubNode(node.body, indent + 4, false, false, false)
        var result: String = "for ((" + node.`init` + "; " + node.cond + "; " + node.incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done"
        if (!node.redirects.isEmpty) {
            for r in node.redirects {
                result = result + " " + _formatRedirect(r, false, false)
            }
        }
        return result
    default:
        break
    }
    switch node {
    case let node as Case:
        var word: String = node.word.value
        var patterns: [String] = []
        var i: Int = 0
        while i < node.patterns.count {
            var p: CasePattern = node.patterns[i]
            var pat: String = p.pattern.replacingOccurrences(of: "|", with: " | ")
            var body: String = ""
            if p.body != nil {
                body = _formatCmdsubNode(p.body, indent + 8, false, false, false)
            } else {
                body = ""
            }
            var term: String = p.terminator
            var patIndent: String = _repeatStr(" ", indent + 8)
            var termIndent: String = _repeatStr(" ", indent + 4)
            var bodyPart: String = ((!body.isEmpty) ? patIndent + body + "\n" : "\n")
            if i == 0 {
                patterns.append(" " + pat + ")\n" + bodyPart + termIndent + term)
            } else {
                patterns.append(pat + ")\n" + bodyPart + termIndent + term)
            }
            i += 1
        }
        var patternStr: Any = patterns.joined(separator: "\n" + _repeatStr(" ", indent + 4))
        var redirects: String = ""
        if (!node.redirects.isEmpty) {
            var redirectParts: [String] = []
            for r in node.redirects {
                redirectParts.append(_formatRedirect(r, false, false))
            }
            redirects = " " + redirectParts.joined(separator: " ")
        }
        return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects
    default:
        break
    }
    switch node {
    case let node as Function:
        var name: String = node.name
        var innerBody: Node = (node.body.kind == "brace-group" ? (node.body as! BraceGroup).body : node.body)
        var body: String = _formatCmdsubNode(innerBody, indent + 4, false, false, false).trimmingCharacters(in: CharacterSet(charactersIn: ";"))
        return "function \\(name) () \n{ \n\\(innerSp)\\(body)\n}"
    default:
        break
    }
    switch node {
    case let node as Subshell:
        var body: String = _formatCmdsubNode(node.body, indent, inProcsub, compactRedirects, false)
        var redirects: String = ""
        if (node.redirects != nil && !node.redirects!.isEmpty) {
            var redirectParts: [String] = []
            for r in node.redirects! {
                redirectParts.append(_formatRedirect(r, false, false))
            }
            redirects = redirectParts.joined(separator: " ")
        }
        if procsubFirst {
            if (!redirects.isEmpty) {
                return "(" + body + ") " + redirects
            }
            return "(" + body + ")"
        }
        if (!redirects.isEmpty) {
            return "( " + body + " ) " + redirects
        }
        return "( " + body + " )"
    default:
        break
    }
    switch node {
    case let node as BraceGroup:
        var body: String = _formatCmdsubNode(node.body, indent, false, false, false)
        body = body.trimmingCharacters(in: CharacterSet(charactersIn: ";"))
        var terminator: String = (body.hasSuffix(" &") ? " }" : "; }")
        var redirects: String = ""
        if (node.redirects != nil && !node.redirects!.isEmpty) {
            var redirectParts: [String] = []
            for r in node.redirects! {
                redirectParts.append(_formatRedirect(r, false, false))
            }
            redirects = redirectParts.joined(separator: " ")
        }
        if (!redirects.isEmpty) {
            return "{ " + body + terminator + " " + redirects
        }
        return "{ " + body + terminator
    default:
        break
    }
    switch node {
    case let node as ArithmeticCommand:
        return "((" + node.rawContent + "))"
    default:
        break
    }
    switch node {
    case let node as ConditionalExpr:
        var body: String = _formatCondBody((node.body as! Node))
        return "[[ " + body + " ]]"
    default:
        break
    }
    switch node {
    case let node as Negation:
        if node.pipeline != nil {
            return "! " + _formatCmdsubNode(node.pipeline, indent, false, false, false)
        }
        return "! "
    default:
        break
    }
    switch node {
    case let node as Time:
        var `prefix`: String = (node.posix ? "time -p " : "time ")
        if node.pipeline != nil {
            return `prefix` + _formatCmdsubNode(node.pipeline, indent, false, false, false)
        }
        return `prefix`
    default:
        break
    }
    return ""
}

func _formatRedirect(_ r: Node, _ compact: Bool, _ heredocOpOnly: Bool) -> String {
    var op: String = ""
    switch r {
    case let r as HereDoc:
        if r.stripTabs {
            op = "<<-"
        } else {
            op = "<<"
        }
        if r.fd > 0 {
            op = String(r.fd) + op
        }
        var delim: String = ""
        if r.quoted {
            delim = "'" + r.delimiter + "'"
        } else {
            delim = r.delimiter
        }
        if heredocOpOnly {
            return op + delim
        }
        return op + delim + "\n" + r.content + r.delimiter + "\n"
    default:
        break
    }
    op = (r as! Redirect).op
    if op == "1>" {
        op = ">"
    } else {
        if op == "0<" {
            op = "<"
        }
    }
    var target: String = (r as! Redirect).target.value
    target = (r as! Redirect).target._expandAllAnsiCQuotes(target)
    target = (r as! Redirect).target._stripLocaleStringDollars(target)
    target = (r as! Redirect).target._formatCommandSubstitutions(target, false)
    if target.hasPrefix("&") {
        var wasInputClose: Bool = false
        if target == "&-" && op.hasSuffix("<") {
            wasInputClose = true
            op = _substring(op, 0, op.count - 1) + ">"
        }
        var afterAmp: String = _substring(target, 1, target.count)
        var isLiteralFd: Bool = afterAmp == "-" || afterAmp.count > 0 && (String(_charAt(afterAmp, 0)).first?.isNumber ?? false)
        if isLiteralFd {
            if op == ">" || op == ">&" {
                op = (wasInputClose ? "0>" : "1>")
            } else {
                if op == "<" || op == "<&" {
                    op = "0<"
                }
            }
        } else {
            if op == "1>" {
                op = ">"
            } else {
                if op == "0<" {
                    op = "<"
                }
            }
        }
        return op + target
    }
    if op.hasSuffix("&") {
        return op + target
    }
    if compact {
        return op + target
    }
    return op + " " + target
}

func _formatHeredocBody(_ r: HereDoc) -> String {
    return "\n" + r.content + r.delimiter + "\n"
}

func _lookaheadForEsac(_ value: String, _ start: Int, _ caseDepth: Int) -> Bool {
    var i: Int = start
    var depth: Int = caseDepth
    var quote: QuoteState = newQuoteState()
    while i < value.count {
        var c: String = String(_charAt(value, i))
        if c == "\\" && i + 1 < value.count && quote.double {
            i += 2
            continue
        }
        if c == "'" && !quote.double {
            quote.single = !quote.single
            i += 1
            continue
        }
        if c == "\"" && !quote.single {
            quote.double = !quote.double
            i += 1
            continue
        }
        if quote.single || quote.double {
            i += 1
            continue
        }
        if _startsWithAt(value, i, "case") && _isWordBoundary(value, i, 4) {
            depth += 1
            i += 4
        } else {
            if _startsWithAt(value, i, "esac") && _isWordBoundary(value, i, 4) {
                depth -= 1
                if depth == 0 {
                    return true
                }
                i += 4
            } else {
                if c == "(" {
                    i += 1
                } else {
                    if c == ")" {
                        if depth > 0 {
                            i += 1
                        } else {
                            break
                        }
                    } else {
                        i += 1
                    }
                }
            }
        }
    }
    return false
}

func _skipBacktick(_ value: String, _ start: Int) -> Int {
    var i: Int = start + 1
    while i < value.count && String(_charAt(value, i)) != "`" {
        if String(_charAt(value, i)) == "\\" && i + 1 < value.count {
            i += 2
        } else {
            i += 1
        }
    }
    if i < value.count {
        i += 1
    }
    return i
}

func _skipSingleQuoted(_ s: String, _ start: Int) -> Int {
    var i: Int = start
    while i < s.count && String(_charAt(s, i)) != "'" {
        i += 1
    }
    return (i < s.count ? i + 1 : i)
}

func _skipDoubleQuoted(_ s: String, _ start: Int) -> Int {
    var i: Int = start
    var n: Int = s.count
    var passNext: Bool = false
    var backq: Bool = false
    while i < n {
        var c: String = String(_charAt(s, i))
        if passNext {
            passNext = false
            i += 1
            continue
        }
        if c == "\\" {
            passNext = true
            i += 1
            continue
        }
        if backq {
            if c == "`" {
                backq = false
            }
            i += 1
            continue
        }
        if c == "`" {
            backq = true
            i += 1
            continue
        }
        if c == "$" && i + 1 < n {
            if String(_charAt(s, i + 1)) == "(" {
                i = _findCmdsubEnd(s, i + 2)
                continue
            }
            if String(_charAt(s, i + 1)) == "{" {
                i = _findBracedParamEnd(s, i + 2)
                continue
            }
        }
        if c == "\"" {
            return i + 1
        }
        i += 1
    }
    return i
}

func _isValidArithmeticStart(_ value: String, _ start: Int) -> Bool {
    var scanParen: Int = 0
    var scanI: Int = start + 3
    while scanI < value.count {
        var scanC: String = String(_charAt(value, scanI))
        if _isExpansionStart(value, scanI, "$(") {
            scanI = _findCmdsubEnd(value, scanI + 2)
            continue
        }
        if scanC == "(" {
            scanParen += 1
        } else {
            if scanC == ")" {
                if scanParen > 0 {
                    scanParen -= 1
                } else {
                    if scanI + 1 < value.count && String(_charAt(value, scanI + 1)) == ")" {
                        return true
                    } else {
                        return false
                    }
                }
            }
        }
        scanI += 1
    }
    return false
}

func _findFunsubEnd(_ value: String, _ start: Int) -> Int {
    var depth: Int = 1
    var i: Int = start
    var quote: QuoteState = newQuoteState()
    while i < value.count && depth > 0 {
        var c: String = String(_charAt(value, i))
        if c == "\\" && i + 1 < value.count && !quote.single {
            i += 2
            continue
        }
        if c == "'" && !quote.double {
            quote.single = !quote.single
            i += 1
            continue
        }
        if c == "\"" && !quote.single {
            quote.double = !quote.double
            i += 1
            continue
        }
        if quote.single || quote.double {
            i += 1
            continue
        }
        if c == "{" {
            depth += 1
        } else {
            if c == "}" {
                depth -= 1
                if depth == 0 {
                    return i + 1
                }
            }
        }
        i += 1
    }
    return value.count
}

func _findCmdsubEnd(_ value: String, _ start: Int) -> Int {
    var depth: Int = 1
    var i: Int = start
    var caseDepth: Int = 0
    var inCasePatterns: Bool = false
    var arithDepth: Int = 0
    var arithParenDepth: Int = 0
    while i < value.count && depth > 0 {
        var c: String = String(_charAt(value, i))
        if c == "\\" && i + 1 < value.count {
            i += 2
            continue
        }
        if c == "'" {
            i = _skipSingleQuoted(value, i + 1)
            continue
        }
        if c == "\"" {
            i = _skipDoubleQuoted(value, i + 1)
            continue
        }
        if c == "#" && arithDepth == 0 && i == start || String(_charAt(value, i - 1)) == " " || String(_charAt(value, i - 1)) == "\t" || String(_charAt(value, i - 1)) == "\n" || String(_charAt(value, i - 1)) == ";" || String(_charAt(value, i - 1)) == "|" || String(_charAt(value, i - 1)) == "&" || String(_charAt(value, i - 1)) == "(" || String(_charAt(value, i - 1)) == ")" {
            while i < value.count && String(_charAt(value, i)) != "\n" {
                i += 1
            }
            continue
        }
        if _startsWithAt(value, i, "<<<") {
            i += 3
            while i < value.count && String(_charAt(value, i)) == " " || String(_charAt(value, i)) == "\t" {
                i += 1
            }
            if i < value.count && String(_charAt(value, i)) == "\"" {
                i += 1
                while i < value.count && String(_charAt(value, i)) != "\"" {
                    if String(_charAt(value, i)) == "\\" && i + 1 < value.count {
                        i += 2
                    } else {
                        i += 1
                    }
                }
                if i < value.count {
                    i += 1
                }
            } else {
                if i < value.count && String(_charAt(value, i)) == "'" {
                    i += 1
                    while i < value.count && String(_charAt(value, i)) != "'" {
                        i += 1
                    }
                    if i < value.count {
                        i += 1
                    }
                } else {
                    while i < value.count && !" \t\n;|&<>()".contains(String(_charAt(value, i))) {
                        i += 1
                    }
                }
            }
            continue
        }
        if _isExpansionStart(value, i, "$((") {
            if _isValidArithmeticStart(value, i) {
                arithDepth += 1
                i += 3
                continue
            }
            var j: Int = _findCmdsubEnd(value, i + 2)
            i = j
            continue
        }
        if arithDepth > 0 && arithParenDepth == 0 && _startsWithAt(value, i, "))") {
            arithDepth -= 1
            i += 2
            continue
        }
        if c == "`" {
            i = _skipBacktick(value, i)
            continue
        }
        if arithDepth == 0 && _startsWithAt(value, i, "<<") {
            i = _skipHeredoc(value, i)
            continue
        }
        if _startsWithAt(value, i, "case") && _isWordBoundary(value, i, 4) {
            caseDepth += 1
            inCasePatterns = false
            i += 4
            continue
        }
        if caseDepth > 0 && _startsWithAt(value, i, "in") && _isWordBoundary(value, i, 2) {
            inCasePatterns = true
            i += 2
            continue
        }
        if _startsWithAt(value, i, "esac") && _isWordBoundary(value, i, 4) {
            if caseDepth > 0 {
                caseDepth -= 1
                inCasePatterns = false
            }
            i += 4
            continue
        }
        if _startsWithAt(value, i, ";;") {
            i += 2
            continue
        }
        if c == "(" {
            if !(inCasePatterns && caseDepth > 0) {
                if arithDepth > 0 {
                    arithParenDepth += 1
                } else {
                    depth += 1
                }
            }
        } else {
            if c == ")" {
                if inCasePatterns && caseDepth > 0 {
                    if !_lookaheadForEsac(value, i + 1, caseDepth) {
                        depth -= 1
                    }
                } else {
                    if arithDepth > 0 {
                        if arithParenDepth > 0 {
                            arithParenDepth -= 1
                        }
                    } else {
                        depth -= 1
                    }
                }
            }
        }
        i += 1
    }
    return i
}

func _findBracedParamEnd(_ value: String, _ start: Int) -> Int {
    var depth: Int = 1
    var i: Int = start
    var inDouble: Bool = false
    var dolbraceState: Int = dolbracestateParam
    while i < value.count && depth > 0 {
        var c: String = String(_charAt(value, i))
        if c == "\\" && i + 1 < value.count {
            i += 2
            continue
        }
        if c == "'" && dolbraceState == dolbracestateQuote && !inDouble {
            i = _skipSingleQuoted(value, i + 1)
            continue
        }
        if c == "\"" {
            inDouble = !inDouble
            i += 1
            continue
        }
        if inDouble {
            i += 1
            continue
        }
        if dolbraceState == dolbracestateParam && "%#^,".contains(c) {
            dolbraceState = dolbracestateQuote
        } else {
            if dolbraceState == dolbracestateParam && ":-=?+/".contains(c) {
                dolbraceState = dolbracestateWord
            }
        }
        if c == "[" && dolbraceState == dolbracestateParam && !inDouble {
            var end: Int = _skipSubscript(value, i, 0)
            if end != -1 {
                i = end
                continue
            }
        }
        if c == "<" || c == ">" && i + 1 < value.count && String(_charAt(value, i + 1)) == "(" {
            i = _findCmdsubEnd(value, i + 2)
            continue
        }
        if c == "{" {
            depth += 1
        } else {
            if c == "}" {
                depth -= 1
                if depth == 0 {
                    return i + 1
                }
            }
        }
        if _isExpansionStart(value, i, "$(") {
            i = _findCmdsubEnd(value, i + 2)
            continue
        }
        if _isExpansionStart(value, i, "${") {
            i = _findBracedParamEnd(value, i + 2)
            continue
        }
        i += 1
    }
    return i
}

func _skipHeredoc(_ value: String, _ start: Int) -> Int {
    var i: Int = start + 2
    if i < value.count && String(_charAt(value, i)) == "-" {
        i += 1
    }
    while i < value.count && _isWhitespaceNoNewline(String(_charAt(value, i))) {
        i += 1
    }
    var delimStart: Int = i
    var quoteChar: Any? = nil
    var delimiter: String = ""
    if i < value.count && String(_charAt(value, i)) == "\"" || String(_charAt(value, i)) == "'" {
        quoteChar = String(_charAt(value, i))
        i += 1
        delimStart = i
        while i < value.count && String(_charAt(value, i)) != quoteChar! {
            i += 1
        }
        delimiter = _substring(value, delimStart, i)
        if i < value.count {
            i += 1
        }
    } else {
        if i < value.count && String(_charAt(value, i)) == "\\" {
            i += 1
            delimStart = i
            if i < value.count {
                i += 1
            }
            while i < value.count && !_isMetachar(String(_charAt(value, i))) {
                i += 1
            }
            delimiter = _substring(value, delimStart, i)
        } else {
            while i < value.count && !_isMetachar(String(_charAt(value, i))) {
                i += 1
            }
            delimiter = _substring(value, delimStart, i)
        }
    }
    var parenDepth: Int = 0
    var quote: QuoteState = newQuoteState()
    var inBacktick: Bool = false
    while i < value.count && String(_charAt(value, i)) != "\n" {
        var c: String = String(_charAt(value, i))
        if c == "\\" && i + 1 < value.count && quote.double || inBacktick {
            i += 2
            continue
        }
        if c == "'" && !quote.double && !inBacktick {
            quote.single = !quote.single
            i += 1
            continue
        }
        if c == "\"" && !quote.single && !inBacktick {
            quote.double = !quote.double
            i += 1
            continue
        }
        if c == "`" && !quote.single {
            inBacktick = !inBacktick
            i += 1
            continue
        }
        if quote.single || quote.double || inBacktick {
            i += 1
            continue
        }
        if c == "(" {
            parenDepth += 1
        } else {
            if c == ")" {
                if parenDepth == 0 {
                    break
                }
                parenDepth -= 1
            }
        }
        i += 1
    }
    if i < value.count && String(_charAt(value, i)) == ")" {
        return i
    }
    if i < value.count && String(_charAt(value, i)) == "\n" {
        i += 1
    }
    while i < value.count {
        var lineStart: Int = i
        var lineEnd: Int = i
        while lineEnd < value.count && String(_charAt(value, lineEnd)) != "\n" {
            lineEnd += 1
        }
        var line: String = _substring(value, lineStart, lineEnd)
        while lineEnd < value.count {
            var trailingBs: Int = 0
            var j: Int = line.count - 1
            while j > -1 {
                if String(_charAt(line, j)) == "\\" {
                    trailingBs += 1
                } else {
                    break
                }
                j += -1
            }
            if trailingBs % 2 == 0 {
                break
            }
            line = String(line.prefix(line.count - 1))
            lineEnd += 1
            var nextLineStart: Int = lineEnd
            while lineEnd < value.count && String(_charAt(value, lineEnd)) != "\n" {
                lineEnd += 1
            }
            line = line + _substring(value, nextLineStart, lineEnd)
        }
        var stripped: String = ""
        if start + 2 < value.count && String(_charAt(value, start + 2)) == "-" {
            stripped = line.trimmingCharacters(in: CharacterSet(charactersIn: "\t"))
        } else {
            stripped = line
        }
        if stripped == delimiter {
            if lineEnd < value.count {
                return lineEnd + 1
            } else {
                return lineEnd
            }
        }
        if stripped.hasPrefix(delimiter) && stripped.count > delimiter.count {
            var tabsStripped: Int = line.count - stripped.count
            return lineStart + tabsStripped + delimiter.count
        }
        if lineEnd < value.count {
            i = lineEnd + 1
        } else {
            i = lineEnd
        }
    }
    return i
}

func _findHeredocContentEnd(_ source: String, _ start: Int, _ delimiters: [(String, Bool)]) -> (Int, Int) {
    if !(!delimiters.isEmpty) {
        return (start, start)
    }
    var pos: Int = start
    while pos < source.count && String(_charAt(source, pos)) != "\n" {
        pos += 1
    }
    if pos >= source.count {
        return (start, start)
    }
    var contentStart: Int = pos
    pos += 1
    for _item in delimiters {
        var delimiter: String = _item.0
        var stripTabs: Bool = _item.1
        while pos < source.count {
            var lineStart: Int = pos
            var lineEnd: Int = pos
            while lineEnd < source.count && String(_charAt(source, lineEnd)) != "\n" {
                lineEnd += 1
            }
            var line: String = _substring(source, lineStart, lineEnd)
            while lineEnd < source.count {
                var trailingBs: Int = 0
                var j: Int = line.count - 1
                while j > -1 {
                    if String(_charAt(line, j)) == "\\" {
                        trailingBs += 1
                    } else {
                        break
                    }
                    j += -1
                }
                if trailingBs % 2 == 0 {
                    break
                }
                line = String(line.prefix(line.count - 1))
                lineEnd += 1
                var nextLineStart: Int = lineEnd
                while lineEnd < source.count && String(_charAt(source, lineEnd)) != "\n" {
                    lineEnd += 1
                }
                line = line + _substring(source, nextLineStart, lineEnd)
            }
            var lineStripped: String = ""
            if stripTabs {
                lineStripped = line.trimmingCharacters(in: CharacterSet(charactersIn: "\t"))
            } else {
                lineStripped = line
            }
            if lineStripped == delimiter {
                pos = (lineEnd < source.count ? lineEnd + 1 : lineEnd)
                break
            }
            if lineStripped.hasPrefix(delimiter) && lineStripped.count > delimiter.count {
                var tabsStripped: Int = line.count - lineStripped.count
                pos = lineStart + tabsStripped + delimiter.count
                break
            }
            pos = (lineEnd < source.count ? lineEnd + 1 : lineEnd)
        }
    }
    return (contentStart, pos)
}

func _isWordBoundary(_ s: String, _ pos: Int, _ wordLen: Int) -> Bool {
    if pos > 0 {
        var prev: String = String(_charAt(s, pos - 1))
        if (prev.first?.isLetter ?? false || prev.first?.isNumber ?? false) || prev == "_" {
            return false
        }
        if "{}!".contains(prev) {
            return false
        }
    }
    var end: Int = pos + wordLen
    if end < s.count && (String(_charAt(s, end)).first?.isLetter ?? false || String(_charAt(s, end)).first?.isNumber ?? false) || String(_charAt(s, end)) == "_" {
        return false
    }
    return true
}

func _isQuote(_ c: String) -> Bool {
    return c == "'" || c == "\""
}

func _collapseWhitespace(_ s: String) -> String {
    var result: [String] = []
    var prevWasWs: Bool = false
    for _c44 in s {
        let c = String(_c44)
        if c == " " || c == "\t" {
            if !prevWasWs {
                result.append(" ")
            }
            prevWasWs = true
        } else {
            result.append(c)
            prevWasWs = false
        }
    }
    var joined: String = result.joined(separator: "")
    return joined.trimmingCharacters(in: CharacterSet(charactersIn: " \t"))
}

func _countTrailingBackslashes(_ s: String) -> Int {
    var count: Int = 0
    var i: Int = s.count - 1
    while i > -1 {
        if String(_charAt(s, i)) == "\\" {
            count += 1
        } else {
            break
        }
        i += -1
    }
    return count
}

func _normalizeHeredocDelimiter(_ delimiter: String) -> String {
    var result: [String] = []
    var i: Int = 0
    while i < delimiter.count {
        var depth: Int = 0
        var inner: [String] = []
        var innerStr: String = ""
        if i + 1 < delimiter.count && String(delimiter[delimiter.index(delimiter.startIndex, offsetBy: i)..<delimiter.index(delimiter.startIndex, offsetBy: min(i + 2, delimiter.count))]) == "$(" {
            result.append("$(")
            i += 2
            depth = 1
            inner = []
            while i < delimiter.count && depth > 0 {
                if String(_charAt(delimiter, i)) == "(" {
                    depth += 1
                    inner.append(String(_charAt(delimiter, i)))
                } else {
                    if String(_charAt(delimiter, i)) == ")" {
                        depth -= 1
                        if depth == 0 {
                            innerStr = inner.joined(separator: "")
                            innerStr = _collapseWhitespace(innerStr)
                            result.append(innerStr)
                            result.append(")")
                        } else {
                            inner.append(String(_charAt(delimiter, i)))
                        }
                    } else {
                        inner.append(String(_charAt(delimiter, i)))
                    }
                }
                i += 1
            }
        } else {
            if i + 1 < delimiter.count && String(delimiter[delimiter.index(delimiter.startIndex, offsetBy: i)..<delimiter.index(delimiter.startIndex, offsetBy: min(i + 2, delimiter.count))]) == "${" {
                result.append("${")
                i += 2
                depth = 1
                inner = []
                while i < delimiter.count && depth > 0 {
                    if String(_charAt(delimiter, i)) == "{" {
                        depth += 1
                        inner.append(String(_charAt(delimiter, i)))
                    } else {
                        if String(_charAt(delimiter, i)) == "}" {
                            depth -= 1
                            if depth == 0 {
                                innerStr = inner.joined(separator: "")
                                innerStr = _collapseWhitespace(innerStr)
                                result.append(innerStr)
                                result.append("}")
                            } else {
                                inner.append(String(_charAt(delimiter, i)))
                            }
                        } else {
                            inner.append(String(_charAt(delimiter, i)))
                        }
                    }
                    i += 1
                }
            } else {
                if i + 1 < delimiter.count && "<>".contains(String(_charAt(delimiter, i))) && String(_charAt(delimiter, i + 1)) == "(" {
                    result.append(String(_charAt(delimiter, i)))
                    result.append("(")
                    i += 2
                    depth = 1
                    inner = []
                    while i < delimiter.count && depth > 0 {
                        if String(_charAt(delimiter, i)) == "(" {
                            depth += 1
                            inner.append(String(_charAt(delimiter, i)))
                        } else {
                            if String(_charAt(delimiter, i)) == ")" {
                                depth -= 1
                                if depth == 0 {
                                    innerStr = inner.joined(separator: "")
                                    innerStr = _collapseWhitespace(innerStr)
                                    result.append(innerStr)
                                    result.append(")")
                                } else {
                                    inner.append(String(_charAt(delimiter, i)))
                                }
                            } else {
                                inner.append(String(_charAt(delimiter, i)))
                            }
                        }
                        i += 1
                    }
                } else {
                    result.append(String(_charAt(delimiter, i)))
                    i += 1
                }
            }
        }
    }
    return result.joined(separator: "")
}

func _isMetachar(_ c: String) -> Bool {
    return c == " " || c == "\t" || c == "\n" || c == "|" || c == "&" || c == ";" || c == "(" || c == ")" || c == "<" || c == ">"
}

func _isFunsubChar(_ c: String) -> Bool {
    return c == " " || c == "\t" || c == "\n" || c == "|"
}

func _isExtglobPrefix(_ c: String) -> Bool {
    return c == "@" || c == "?" || c == "*" || c == "+" || c == "!"
}

func _isRedirectChar(_ c: String) -> Bool {
    return c == "<" || c == ">"
}

func _isSpecialParam(_ c: String) -> Bool {
    return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-" || c == "&"
}

func _isSpecialParamUnbraced(_ c: String) -> Bool {
    return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-"
}

func _isDigit(_ c: String) -> Bool {
    return c >= "0" && c <= "9"
}

func _isSemicolonOrNewline(_ c: String) -> Bool {
    return c == ";" || c == "\n"
}

func _isWordEndContext(_ c: String) -> Bool {
    return c == " " || c == "\t" || c == "\n" || c == ";" || c == "|" || c == "&" || c == "<" || c == ">" || c == "(" || c == ")"
}

func _skipMatchedPair(_ s: String, _ start: Int, _ `open`: String, _ close: String, _ flags: Int) -> Int {
    var n: Int = s.count
    var i: Int = 0
    if (flags & _smpPastOpen != 0) {
        i = start
    } else {
        if start >= n || String(_charAt(s, start)) != `open` {
            return -1
        }
        i = start + 1
    }
    var depth: Int = 1
    var passNext: Bool = false
    var backq: Bool = false
    while i < n && depth > 0 {
        var c: String = String(_charAt(s, i))
        if passNext {
            passNext = false
            i += 1
            continue
        }
        var literal: Int = flags & _smpLiteral
        if !(literal != 0) && c == "\\" {
            passNext = true
            i += 1
            continue
        }
        if backq {
            if c == "`" {
                backq = false
            }
            i += 1
            continue
        }
        if !(literal != 0) && c == "`" {
            backq = true
            i += 1
            continue
        }
        if !(literal != 0) && c == "'" {
            i = _skipSingleQuoted(s, i + 1)
            continue
        }
        if !(literal != 0) && c == "\"" {
            i = _skipDoubleQuoted(s, i + 1)
            continue
        }
        if !(literal != 0) && _isExpansionStart(s, i, "$(") {
            i = _findCmdsubEnd(s, i + 2)
            continue
        }
        if !(literal != 0) && _isExpansionStart(s, i, "${") {
            i = _findBracedParamEnd(s, i + 2)
            continue
        }
        if !(literal != 0) && c == `open` {
            depth += 1
        } else {
            if c == close {
                depth -= 1
            }
        }
        i += 1
    }
    return (depth == 0 ? i : -1)
}

func _skipSubscript(_ s: String, _ start: Int, _ flags: Int) -> Int {
    return _skipMatchedPair(s, start, "[", "]", flags)
}

func _assignment(_ s: String, _ flags: Int) -> Int {
    if !(!s.isEmpty) {
        return -1
    }
    if !((String(_charAt(s, 0)).first?.isLetter ?? false) || String(_charAt(s, 0)) == "_") {
        return -1
    }
    var i: Int = 1
    while i < s.count {
        var c: String = String(_charAt(s, i))
        if c == "=" {
            return i
        }
        if c == "[" {
            var subFlags: Int = ((flags & 2 != 0) ? _smpLiteral : 0)
            var end: Int = _skipSubscript(s, i, subFlags)
            if end == -1 {
                return -1
            }
            i = end
            if i < s.count && String(_charAt(s, i)) == "+" {
                i += 1
            }
            if i < s.count && String(_charAt(s, i)) == "=" {
                return i
            }
            return -1
        }
        if c == "+" {
            if i + 1 < s.count && String(_charAt(s, i + 1)) == "=" {
                return i + 1
            }
            return -1
        }
        if !((c.first?.isLetter ?? false || c.first?.isNumber ?? false) || c == "_") {
            return -1
        }
        i += 1
    }
    return -1
}

func _isArrayAssignmentPrefix(_ chars: [String]) -> Bool {
    if !(!chars.isEmpty) {
        return false
    }
    if !((chars[0].first?.isLetter ?? false) || chars[0] == "_") {
        return false
    }
    var s: String = chars.joined(separator: "")
    var i: Int = 1
    while i < s.count && (String(_charAt(s, i)).first?.isLetter ?? false || String(_charAt(s, i)).first?.isNumber ?? false) || String(_charAt(s, i)) == "_" {
        i += 1
    }
    while i < s.count {
        if String(_charAt(s, i)) != "[" {
            return false
        }
        var end: Int = _skipSubscript(s, i, _smpLiteral)
        if end == -1 {
            return false
        }
        i = end
    }
    return true
}

func _isSpecialParamOrDigit(_ c: String) -> Bool {
    return _isSpecialParam(c) || _isDigit(c)
}

func _isParamExpansionOp(_ c: String) -> Bool {
    return c == ":" || c == "-" || c == "=" || c == "+" || c == "?" || c == "#" || c == "%" || c == "/" || c == "^" || c == "," || c == "@" || c == "*" || c == "["
}

func _isSimpleParamOp(_ c: String) -> Bool {
    return c == "-" || c == "=" || c == "?" || c == "+"
}

func _isEscapeCharInBacktick(_ c: String) -> Bool {
    return c == "$" || c == "`" || c == "\\"
}

func _isNegationBoundary(_ c: String) -> Bool {
    return _isWhitespace(c) || c == ";" || c == "|" || c == ")" || c == "&" || c == ">" || c == "<"
}

func _isBackslashEscaped(_ value: String, _ idx: Int) -> Bool {
    var bsCount: Int = 0
    var j: Int = idx - 1
    while j >= 0 && String(_charAt(value, j)) == "\\" {
        bsCount += 1
        j -= 1
    }
    return bsCount % 2 == 1
}

func _isDollarDollarParen(_ value: String, _ idx: Int) -> Bool {
    var dollarCount: Int = 0
    var j: Int = idx - 1
    while j >= 0 && String(_charAt(value, j)) == "$" {
        dollarCount += 1
        j -= 1
    }
    return dollarCount % 2 == 1
}

func _isParen(_ c: String) -> Bool {
    return c == "(" || c == ")"
}

func _isCaretOrBang(_ c: String) -> Bool {
    return c == "!" || c == "^"
}

func _isAtOrStar(_ c: String) -> Bool {
    return c == "@" || c == "*"
}

func _isDigitOrDash(_ c: String) -> Bool {
    return _isDigit(c) || c == "-"
}

func _isNewlineOrRightParen(_ c: String) -> Bool {
    return c == "\n" || c == ")"
}

func _isSemicolonNewlineBrace(_ c: String) -> Bool {
    return c == ";" || c == "\n" || c == "{"
}

func _looksLikeAssignment(_ s: String) -> Bool {
    return _assignment(s, 0) != -1
}

func _isValidIdentifier(_ name: String) -> Bool {
    if !(!name.isEmpty) {
        return false
    }
    if !((String(_charAt(name, 0)).first?.isLetter ?? false) || String(_charAt(name, 0)) == "_") {
        return false
    }
    for _c45 in String(name.dropFirst(1)) {
        let c = String(_c45)
        if !((Character(UnicodeScalar(c)!).isLetter || Character(UnicodeScalar(c)!).isNumber) || c == "_") {
            return false
        }
    }
    return true
}

func parse(_ source: String, _ extglob: Bool) throws -> [Node] {
    var parser: Parser = newParser(source, false, extglob)
    return try parser.parse()
}

func newParseError(_ message: String, _ pos: Int, _ line: Int) -> ParseError {
    var `self`: ParseError = ParseError(message: "", pos: 0, line: 0)
    `self`.message = message
    `self`.pos = pos
    `self`.line = line
    return `self`
}

func newMatchedPairError(_ message: String, _ pos: Int, _ line: Int) -> MatchedPairError {
    return MatchedPairError(message: message, pos: pos, line: line)
}

func newQuoteState() -> QuoteState {
    var `self`: QuoteState = QuoteState(single: false, double: false, _stack: [])
    `self`.single = false
    `self`.double = false
    `self`._stack = []
    return `self`
}

func newParseContext(_ kind: Int) -> ParseContext {
    var `self`: ParseContext = ParseContext(kind: 0, parenDepth: 0, braceDepth: 0, bracketDepth: 0, caseDepth: 0, arithDepth: 0, arithParenDepth: 0, quote: nil)
    `self`.kind = kind
    `self`.parenDepth = 0
    `self`.braceDepth = 0
    `self`.bracketDepth = 0
    `self`.caseDepth = 0
    `self`.arithDepth = 0
    `self`.arithParenDepth = 0
    `self`.quote = newQuoteState()
    return `self`
}

func newContextStack() -> ContextStack {
    var `self`: ContextStack = ContextStack(_stack: [])
    `self`._stack = [newParseContext(0)]
    return `self`
}

func newLexer(_ source: String, _ extglob: Bool) -> Lexer {
    var `self`: Lexer = Lexer(reservedWords: [:], source: "", pos: 0, length: 0, quote: nil, _tokenCache: nil, _parserState: 0, _dolbraceState: 0, _pendingHeredocs: [], _extglob: false, _parser: nil, _eofToken: "", _lastReadToken: nil, _wordContext: 0, _atCommandStart: false, _inArrayLiteral: false, _inAssignBuiltin: false, _postReadPos: 0, _cachedWordContext: 0, _cachedAtCommandStart: false, _cachedInArrayLiteral: false, _cachedInAssignBuiltin: false)
    `self`.source = source
    `self`.pos = 0
    `self`.length = source.count
    `self`.quote = newQuoteState()
    `self`._tokenCache = nil
    `self`._parserState = parserstateflagsNone
    `self`._dolbraceState = dolbracestateNone
    `self`._pendingHeredocs = []
    `self`._extglob = extglob
    `self`._parser = nil
    `self`._eofToken = ""
    `self`._lastReadToken = nil
    `self`._wordContext = wordCtxNormal
    `self`._atCommandStart = false
    `self`._inArrayLiteral = false
    `self`._inAssignBuiltin = false
    `self`._postReadPos = 0
    `self`._cachedWordContext = wordCtxNormal
    `self`._cachedAtCommandStart = false
    `self`._cachedInArrayLiteral = false
    `self`._cachedInAssignBuiltin = false
    return `self`
}

func newParser(_ source: String, _ inProcessSub: Bool, _ extglob: Bool) -> Parser {
    var `self`: Parser = Parser(source: "", pos: 0, length: 0, _pendingHeredocs: [], _cmdsubHeredocEnd: 0, _sawNewlineInSingleQuote: false, _inProcessSub: false, _extglob: false, _ctx: nil, _lexer: nil, _tokenHistory: [], _parserState: 0, _dolbraceState: 0, _eofToken: "", _wordContext: 0, _atCommandStart: false, _inArrayLiteral: false, _inAssignBuiltin: false, _arithSrc: "", _arithPos: 0, _arithLen: 0)
    `self`.source = source
    `self`.pos = 0
    `self`.length = source.count
    `self`._pendingHeredocs = []
    `self`._cmdsubHeredocEnd = -1
    `self`._sawNewlineInSingleQuote = false
    `self`._inProcessSub = inProcessSub
    `self`._extglob = extglob
    `self`._ctx = newContextStack()
    `self`._lexer = newLexer(source, extglob)
    `self`._lexer._parser = `self`
    `self`._tokenHistory = [nil, nil, nil, nil]
    `self`._parserState = parserstateflagsNone
    `self`._dolbraceState = dolbracestateNone
    `self`._eofToken = ""
    `self`._wordContext = wordCtxNormal
    `self`._atCommandStart = false
    `self`._inArrayLiteral = false
    `self`._inAssignBuiltin = false
    `self`._arithSrc = ""
    `self`._arithPos = 0
    `self`._arithLen = 0
    return `self`
}

