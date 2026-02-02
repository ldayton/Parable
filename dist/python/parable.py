"""Generated Python code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


def _intPtr(val: int) -> int | None:
    return None if val == -1 else val

ANSI_C_ESCAPES: dict[str, int] = {"a": 7, "b": 8, "e": 27, "E": 27, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11, "\\": 92, "\"": 34, "?": 63}
TokenType_EOF: int = 0
TokenType_WORD: int = 1
TokenType_NEWLINE: int = 2
TokenType_SEMI: int = 10
TokenType_PIPE: int = 11
TokenType_AMP: int = 12
TokenType_LPAREN: int = 13
TokenType_RPAREN: int = 14
TokenType_LBRACE: int = 15
TokenType_RBRACE: int = 16
TokenType_LESS: int = 17
TokenType_GREATER: int = 18
TokenType_AND_AND: int = 30
TokenType_OR_OR: int = 31
TokenType_SEMI_SEMI: int = 32
TokenType_SEMI_AMP: int = 33
TokenType_SEMI_SEMI_AMP: int = 34
TokenType_LESS_LESS: int = 35
TokenType_GREATER_GREATER: int = 36
TokenType_LESS_AMP: int = 37
TokenType_GREATER_AMP: int = 38
TokenType_LESS_GREATER: int = 39
TokenType_GREATER_PIPE: int = 40
TokenType_LESS_LESS_MINUS: int = 41
TokenType_LESS_LESS_LESS: int = 42
TokenType_AMP_GREATER: int = 43
TokenType_AMP_GREATER_GREATER: int = 44
TokenType_PIPE_AMP: int = 45
TokenType_IF: int = 50
TokenType_THEN: int = 51
TokenType_ELSE: int = 52
TokenType_ELIF: int = 53
TokenType_FI: int = 54
TokenType_CASE: int = 55
TokenType_ESAC: int = 56
TokenType_FOR: int = 57
TokenType_WHILE: int = 58
TokenType_UNTIL: int = 59
TokenType_DO: int = 60
TokenType_DONE: int = 61
TokenType_IN: int = 62
TokenType_FUNCTION: int = 63
TokenType_SELECT: int = 64
TokenType_COPROC: int = 65
TokenType_TIME: int = 66
TokenType_BANG: int = 67
TokenType_LBRACKET_LBRACKET: int = 68
TokenType_RBRACKET_RBRACKET: int = 69
TokenType_ASSIGNMENT_WORD: int = 80
TokenType_NUMBER: int = 81
ParserStateFlags_NONE: int = 0
ParserStateFlags_PST_CASEPAT: int = 1
ParserStateFlags_PST_CMDSUBST: int = 2
ParserStateFlags_PST_CASESTMT: int = 4
ParserStateFlags_PST_CONDEXPR: int = 8
ParserStateFlags_PST_COMPASSIGN: int = 16
ParserStateFlags_PST_ARITH: int = 32
ParserStateFlags_PST_HEREDOC: int = 64
ParserStateFlags_PST_REGEXP: int = 128
ParserStateFlags_PST_EXTPAT: int = 256
ParserStateFlags_PST_SUBSHELL: int = 512
ParserStateFlags_PST_REDIRLIST: int = 1024
ParserStateFlags_PST_COMMENT: int = 2048
ParserStateFlags_PST_EOFTOKEN: int = 4096
DolbraceState_NONE: int = 0
DolbraceState_PARAM: int = 1
DolbraceState_OP: int = 2
DolbraceState_WORD: int = 4
DolbraceState_QUOTE: int = 64
DolbraceState_QUOTE2: int = 128
MatchedPairFlags_NONE: int = 0
MatchedPairFlags_DQUOTE: int = 1
MatchedPairFlags_DOLBRACE: int = 2
MatchedPairFlags_COMMAND: int = 4
MatchedPairFlags_ARITH: int = 8
MatchedPairFlags_ALLOWESC: int = 16
MatchedPairFlags_EXTGLOB: int = 32
MatchedPairFlags_FIRSTCLOSE: int = 64
MatchedPairFlags_ARRAYSUB: int = 128
MatchedPairFlags_BACKQUOTE: int = 256
ParseContext_NORMAL: int = 0
ParseContext_COMMAND_SUB: int = 1
ParseContext_ARITHMETIC: int = 2
ParseContext_CASE_PATTERN: int = 3
ParseContext_BRACE_EXPANSION: int = 4
RESERVED_WORDS: set[str] = {"if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"}
COND_UNARY_OPS: set[str] = {"-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"}
COND_BINARY_OPS: set[str] = {"==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"}
COMPOUND_KEYWORDS: set[str] = {"while", "until", "for", "if", "case", "select"}
ASSIGNMENT_BUILTINS: set[str] = {"alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"}
_SMP_LITERAL: int = 1
_SMP_PAST_OPEN: int = 2
WORD_CTX_NORMAL: int = 0
WORD_CTX_COND: int = 1
WORD_CTX_REGEX: int = 2


class Node(Protocol):
    def GetKind(self) -> str: ...
    def ToSexp(self) -> str: ...


class ParseError(Exception):
    message: str = ""
    pos: int = 0
    line: int = 0

    def _format_message(self) -> str:
        if self.line != 0 and self.pos != 0:
            return f"Parse error at line {self.line}, position {self.pos}: {self.message}"
        elif self.pos != 0:
            return f"Parse error at position {self.pos}: {self.message}"
        return f"Parse error: {self.message}"


class MatchedPairError(ParseError):
    pass




@dataclass
class Token:
    type: int = 0
    value: str = ""
    pos: int = 0
    parts: list[Node] = field(default_factory=list)
    word: Word | None = None

    def __repr__(self) -> str:
        if self.word is not None:
            return f"Token({self.type}, {self.value}, {self.pos}, word={self.word})"
        if self.parts:
            return f"Token({self.type}, {self.value}, {self.pos}, parts={len(self.parts)})"
        return f"Token({self.type}, {self.value}, {self.pos})"








@dataclass
class SavedParserState:
    parser_state: int = 0
    dolbrace_state: int = 0
    pending_heredocs: list[Node] = field(default_factory=list)
    ctx_stack: list[ParseContext] = field(default_factory=list)
    eof_token: str = ""


@dataclass
class QuoteState:
    single: bool = False
    double: bool = False
    _stack: list[tuple[bool, bool]] = field(default_factory=list)

    def push(self) -> None:
        self._stack.append((self.single, self.double))
        self.single = False
        self.double = False

    def pop(self) -> None:
        if self._stack:
            self.single, self.double = self._stack.pop()

    def in_quotes(self) -> bool:
        return self.single or self.double

    def copy(self) -> QuoteState:
        qs = NewQuoteState()
        qs.single = self.single
        qs.double = self.double
        qs._stack = self._stack.copy()
        return qs

    def outer_double(self) -> bool:
        if len(self._stack) == 0:
            return False
        return self._stack[-1][1]


@dataclass
class ParseContext:
    kind: int = 0
    paren_depth: int = 0
    brace_depth: int = 0
    bracket_depth: int = 0
    case_depth: int = 0
    arith_depth: int = 0
    arith_paren_depth: int = 0
    quote: QuoteState = None

    def copy(self) -> ParseContext:
        ctx = NewParseContext(self.kind)
        ctx.paren_depth = self.paren_depth
        ctx.brace_depth = self.brace_depth
        ctx.bracket_depth = self.bracket_depth
        ctx.case_depth = self.case_depth
        ctx.arith_depth = self.arith_depth
        ctx.arith_paren_depth = self.arith_paren_depth
        ctx.quote = self.quote.copy()
        return ctx


@dataclass
class ContextStack:
    _stack: list[ParseContext] = field(default_factory=list)

    def get_current(self) -> ParseContext:
        return self._stack[-1]

    def push(self, kind: int) -> None:
        self._stack.append(NewParseContext(kind))

    def pop(self) -> ParseContext:
        if len(self._stack) > 1:
            return self._stack.pop()
        return self._stack[0]

    def copy_stack(self) -> list[ParseContext]:
        result = []
        for ctx in (self._stack or []):
            result.append(ctx.copy())
        return result

    def restore_from(self, saved_stack: list[ParseContext]) -> None:
        result = []
        for ctx in saved_stack:
            result.append(ctx.copy())
        self._stack = result


@dataclass
class Lexer:
    RESERVED_WORDS: dict[str, int] = field(default_factory=dict)
    source: str = ""
    pos: int = 0
    length: int = 0
    quote: QuoteState = None
    _token_cache: Token | None = None
    _parser_state: int = 0
    _dolbrace_state: int = 0
    _pending_heredocs: list[Node] = field(default_factory=list)
    _extglob: bool = False
    _parser: Parser | None = None
    _eof_token: str = ""
    _last_read_token: Token | None = None
    _word_context: int = 0
    _at_command_start: bool = False
    _in_array_literal: bool = False
    _in_assign_builtin: bool = False
    _post_read_pos: int = 0
    _cached_word_context: int = 0
    _cached_at_command_start: bool = False
    _cached_in_array_literal: bool = False
    _cached_in_assign_builtin: bool = False

    def peek(self) -> str:
        if self.pos >= self.length:
            return ""
        return self.source[self.pos]

    def advance(self) -> str:
        if self.pos >= self.length:
            return ""
        c = self.source[self.pos]
        self.pos += 1
        return c

    def at_end(self) -> bool:
        return self.pos >= self.length

    def lookahead(self, n: int) -> str:
        return _substring(self.source, self.pos, self.pos + n)

    def is_metachar(self, c: str) -> bool:
        return c in "|&;()<> \t\n"

    def _read_operator(self) -> Token:
        start = self.pos
        c = self.peek()
        if c == "":
            return None
        two = self.lookahead(2)
        three = self.lookahead(3)
        if three == ";;&":
            self.pos += 3
            return Token(type=TokenType_SEMI_SEMI_AMP, value=three, pos=start)
        if three == "<<-":
            self.pos += 3
            return Token(type=TokenType_LESS_LESS_MINUS, value=three, pos=start)
        if three == "<<<":
            self.pos += 3
            return Token(type=TokenType_LESS_LESS_LESS, value=three, pos=start)
        if three == "&>>":
            self.pos += 3
            return Token(type=TokenType_AMP_GREATER_GREATER, value=three, pos=start)
        if two == "&&":
            self.pos += 2
            return Token(type=TokenType_AND_AND, value=two, pos=start)
        if two == "||":
            self.pos += 2
            return Token(type=TokenType_OR_OR, value=two, pos=start)
        if two == ";;":
            self.pos += 2
            return Token(type=TokenType_SEMI_SEMI, value=two, pos=start)
        if two == ";&":
            self.pos += 2
            return Token(type=TokenType_SEMI_AMP, value=two, pos=start)
        if two == "<<":
            self.pos += 2
            return Token(type=TokenType_LESS_LESS, value=two, pos=start)
        if two == ">>":
            self.pos += 2
            return Token(type=TokenType_GREATER_GREATER, value=two, pos=start)
        if two == "<&":
            self.pos += 2
            return Token(type=TokenType_LESS_AMP, value=two, pos=start)
        if two == ">&":
            self.pos += 2
            return Token(type=TokenType_GREATER_AMP, value=two, pos=start)
        if two == "<>":
            self.pos += 2
            return Token(type=TokenType_LESS_GREATER, value=two, pos=start)
        if two == ">|":
            self.pos += 2
            return Token(type=TokenType_GREATER_PIPE, value=two, pos=start)
        if two == "&>":
            self.pos += 2
            return Token(type=TokenType_AMP_GREATER, value=two, pos=start)
        if two == "|&":
            self.pos += 2
            return Token(type=TokenType_PIPE_AMP, value=two, pos=start)
        if c == ";":
            self.pos += 1
            return Token(type=TokenType_SEMI, value=c, pos=start)
        if c == "|":
            self.pos += 1
            return Token(type=TokenType_PIPE, value=c, pos=start)
        if c == "&":
            self.pos += 1
            return Token(type=TokenType_AMP, value=c, pos=start)
        if c == "(":
            if self._word_context == WORD_CTX_REGEX:
                return None
            self.pos += 1
            return Token(type=TokenType_LPAREN, value=c, pos=start)
        if c == ")":
            if self._word_context == WORD_CTX_REGEX:
                return None
            self.pos += 1
            return Token(type=TokenType_RPAREN, value=c, pos=start)
        if c == "<":
            if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                return None
            self.pos += 1
            return Token(type=TokenType_LESS, value=c, pos=start)
        if c == ">":
            if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                return None
            self.pos += 1
            return Token(type=TokenType_GREATER, value=c, pos=start)
        if c == "\n":
            self.pos += 1
            return Token(type=TokenType_NEWLINE, value=c, pos=start)
        return None

    def skip_blanks(self) -> None:
        while self.pos < self.length:
            c = self.source[self.pos]
            if c != " " and c != "\t":
                break
            self.pos += 1

    def _skip_comment(self) -> bool:
        if self.pos >= self.length:
            return False
        if self.source[self.pos] != "#":
            return False
        if self.quote.in_quotes():
            return False
        if self.pos > 0:
            prev = self.source[self.pos - 1]
            if prev not in " \t\n;|&(){}":
                return False
        while self.pos < self.length and self.source[self.pos] != "\n":
            self.pos += 1
        return True

    def _read_single_quote(self, start: int) -> tuple[str, bool]:
        chars = ["'"]
        saw_newline = False
        while self.pos < self.length:
            c = self.source[self.pos]
            if c == "\n":
                saw_newline = True
            chars.append(c)
            self.pos += 1
            if c == "'":
                return ("".join(chars), saw_newline)
        raise ParseError("Unterminated single quote", start)

    def _is_word_terminator(self, ctx: int, ch: str, bracket_depth: int, paren_depth: int) -> bool:
        if ctx == WORD_CTX_REGEX:
            if ch == "]" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]":
                return True
            if ch == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == "&":
                return True
            if ch == ")" and paren_depth == 0:
                return True
            return _is_whitespace(ch) and paren_depth == 0
        if ctx == WORD_CTX_COND:
            if ch == "]" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]":
                return True
            if ch == ")":
                return True
            if ch == "&":
                return True
            if ch == "|":
                return True
            if ch == ";":
                return True
            if _is_redirect_char(ch) and not (self.pos + 1 < self.length and self.source[self.pos + 1] == "("):
                return True
            return _is_whitespace(ch)
        if self._parser_state & ParserStateFlags_PST_EOFTOKEN and self._eof_token != "" and ch == self._eof_token and bracket_depth == 0:
            return True
        if _is_redirect_char(ch) and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            return False
        return _is_metachar(ch) and bracket_depth == 0

    def _read_bracket_expression(self, chars: list[str], parts: list[Node], for_regex: bool, paren_depth: int) -> bool:
        if for_regex:
            scan = self.pos + 1
            if scan < self.length and self.source[scan] == "^":
                scan += 1
            if scan < self.length and self.source[scan] == "]":
                scan += 1
            bracket_will_close = False
            while scan < self.length:
                sc = self.source[scan]
                if sc == "]" and scan + 1 < self.length and self.source[scan + 1] == "]":
                    break
                if sc == ")" and paren_depth > 0:
                    break
                if sc == "&" and scan + 1 < self.length and self.source[scan + 1] == "&":
                    break
                if sc == "]":
                    bracket_will_close = True
                    break
                if sc == "[" and scan + 1 < self.length and self.source[scan + 1] == ":":
                    scan += 2
                    while scan < self.length and not (self.source[scan] == ":" and scan + 1 < self.length and self.source[scan + 1] == "]"):
                        scan += 1
                    if scan < self.length:
                        scan += 2
                    continue
                scan += 1
            if not bracket_will_close:
                return False
        else:
            if self.pos + 1 >= self.length:
                return False
            next_ch = self.source[self.pos + 1]
            if _is_whitespace_no_newline(next_ch) or next_ch == "&" or next_ch == "|":
                return False
        chars.append(self.advance())
        if not self.at_end() and self.peek() == "^":
            chars.append(self.advance())
        if not self.at_end() and self.peek() == "]":
            chars.append(self.advance())
        while not self.at_end():
            c = self.peek()
            if c == "]":
                chars.append(self.advance())
                break
            if c == "[" and self.pos + 1 < self.length and self.source[self.pos + 1] == ":":
                chars.append(self.advance())
                chars.append(self.advance())
                while not self.at_end() and not (self.peek() == ":" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]"):
                    chars.append(self.advance())
                if not self.at_end():
                    chars.append(self.advance())
                    chars.append(self.advance())
            elif not for_regex and c == "[" and self.pos + 1 < self.length and self.source[self.pos + 1] == "=":
                chars.append(self.advance())
                chars.append(self.advance())
                while not self.at_end() and not (self.peek() == "=" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]"):
                    chars.append(self.advance())
                if not self.at_end():
                    chars.append(self.advance())
                    chars.append(self.advance())
            elif not for_regex and c == "[" and self.pos + 1 < self.length and self.source[self.pos + 1] == ".":
                chars.append(self.advance())
                chars.append(self.advance())
                while not self.at_end() and not (self.peek() == "." and self.pos + 1 < self.length and self.source[self.pos + 1] == "]"):
                    chars.append(self.advance())
                if not self.at_end():
                    chars.append(self.advance())
                    chars.append(self.advance())
            elif for_regex and c == "$":
                self._sync_to_parser()
                if not self._parser._parse_dollar_expansion(chars, parts, False):
                    self._sync_from_parser()
                    chars.append(self.advance())
                else:
                    self._sync_from_parser()
            else:
                chars.append(self.advance())
        return True

    def _parse_matched_pair(self, open_char: str, close_char: str, flags: int, initial_was_dollar: bool) -> str:
        start = self.pos
        count = 1
        chars: list[str] = []
        pass_next = False
        was_dollar = initial_was_dollar
        was_gtlt = False
        while count > 0:
            if self.at_end():
                raise MatchedPairError(f"unexpected EOF while looking for matching `{close_char}'", start)
            ch = self.advance()
            if flags & MatchedPairFlags_DOLBRACE and self._dolbrace_state == DolbraceState_OP:
                if ch not in "#%^,~:-=?+/":
                    self._dolbrace_state = DolbraceState_WORD
            if pass_next:
                pass_next = False
                chars.append(ch)
                was_dollar = ch == "$"
                was_gtlt = ch in "<>"
                continue
            if open_char == "'":
                if ch == close_char:
                    count -= 1
                    if count == 0:
                        break
                if ch == "\\" and flags & MatchedPairFlags_ALLOWESC:
                    pass_next = True
                chars.append(ch)
                was_dollar = False
                was_gtlt = False
                continue
            if ch == "\\":
                if not self.at_end() and self.peek() == "\n":
                    self.advance()
                    was_dollar = False
                    was_gtlt = False
                    continue
                pass_next = True
                chars.append(ch)
                was_dollar = False
                was_gtlt = False
                continue
            if ch == close_char:
                count -= 1
                if count == 0:
                    break
                chars.append(ch)
                was_dollar = False
                was_gtlt = ch in "<>"
                continue
            if ch == open_char and open_char != close_char:
                if not (flags & MatchedPairFlags_DOLBRACE and open_char == "{"):
                    count += 1
                chars.append(ch)
                was_dollar = False
                was_gtlt = ch in "<>"
                continue
            if (ch in "'\"`") and open_char != close_char:
                if ch == "'":
                    chars.append(ch)
                    quote_flags = flags | MatchedPairFlags_ALLOWESC if was_dollar else flags
                    nested = self._parse_matched_pair("'", "'", quote_flags, False)
                    chars.append(nested)
                    chars.append("'")
                    was_dollar = False
                    was_gtlt = False
                    continue
                elif ch == "\"":
                    chars.append(ch)
                    nested = self._parse_matched_pair("\"", "\"", flags | MatchedPairFlags_DQUOTE, False)
                    chars.append(nested)
                    chars.append("\"")
                    was_dollar = False
                    was_gtlt = False
                    continue
                elif ch == "`":
                    chars.append(ch)
                    nested = self._parse_matched_pair("`", "`", flags, False)
                    chars.append(nested)
                    chars.append("`")
                    was_dollar = False
                    was_gtlt = False
                    continue
            if ch == "$" and not self.at_end() and not flags & MatchedPairFlags_EXTGLOB:
                next_ch = self.peek()
                if was_dollar:
                    chars.append(ch)
                    was_dollar = False
                    was_gtlt = False
                    continue
                if next_ch == "{":
                    if flags & MatchedPairFlags_ARITH:
                        after_brace_pos = self.pos + 1
                        if after_brace_pos >= self.length or not _is_funsub_char(self.source[after_brace_pos]):
                            chars.append(ch)
                            was_dollar = True
                            was_gtlt = False
                            continue
                    self.pos -= 1
                    self._sync_to_parser()
                    in_dquote = (flags & MatchedPairFlags_DQUOTE) != 0
                    param_node, param_text = self._parser._parse_param_expansion(in_dquote)
                    self._sync_from_parser()
                    if param_node is not None:
                        chars.append(param_text)
                        was_dollar = False
                        was_gtlt = False
                    else:
                        chars.append(self.advance())
                        was_dollar = True
                        was_gtlt = False
                    continue
                elif next_ch == "(":
                    self.pos -= 1
                    self._sync_to_parser()
                    if self.pos + 2 < self.length and self.source[self.pos + 2] == "(":
                        arith_node, arith_text = self._parser._parse_arithmetic_expansion()
                        self._sync_from_parser()
                        if arith_node is not None:
                            chars.append(arith_text)
                            was_dollar = False
                            was_gtlt = False
                        else:
                            self._sync_to_parser()
                            cmd_node, cmd_text = self._parser._parse_command_substitution()
                            self._sync_from_parser()
                            if cmd_node is not None:
                                chars.append(cmd_text)
                                was_dollar = False
                                was_gtlt = False
                            else:
                                chars.append(self.advance())
                                chars.append(self.advance())
                                was_dollar = False
                                was_gtlt = False
                    else:
                        cmd_node, cmd_text = self._parser._parse_command_substitution()
                        self._sync_from_parser()
                        if cmd_node is not None:
                            chars.append(cmd_text)
                            was_dollar = False
                            was_gtlt = False
                        else:
                            chars.append(self.advance())
                            chars.append(self.advance())
                            was_dollar = False
                            was_gtlt = False
                    continue
                elif next_ch == "[":
                    self.pos -= 1
                    self._sync_to_parser()
                    arith_node, arith_text = self._parser._parse_deprecated_arithmetic()
                    self._sync_from_parser()
                    if arith_node is not None:
                        chars.append(arith_text)
                        was_dollar = False
                        was_gtlt = False
                    else:
                        chars.append(self.advance())
                        was_dollar = True
                        was_gtlt = False
                    continue
            if ch == "(" and was_gtlt and flags & MatchedPairFlags_DOLBRACE | MatchedPairFlags_ARRAYSUB:
                direction = chars[-1]
                chars = chars[:-1]
                self.pos -= 1
                self._sync_to_parser()
                procsub_node, procsub_text = self._parser._parse_process_substitution()
                self._sync_from_parser()
                if procsub_node is not None:
                    chars.append(procsub_text)
                    was_dollar = False
                    was_gtlt = False
                else:
                    chars.append(direction)
                    chars.append(self.advance())
                    was_dollar = False
                    was_gtlt = False
                continue
            chars.append(ch)
            was_dollar = ch == "$"
            was_gtlt = ch in "<>"
        return "".join(chars)

    def _collect_param_argument(self, flags: int, was_dollar: bool) -> str:
        return self._parse_matched_pair("{", "}", flags | MatchedPairFlags_DOLBRACE, was_dollar)

    def _read_word_internal(self, ctx: int, at_command_start: bool, in_array_literal: bool, in_assign_builtin: bool) -> Word:
        start = self.pos
        chars: list[str] = []
        parts: list[Node] = []
        bracket_depth = 0
        bracket_start_pos: int = -1
        seen_equals = False
        paren_depth = 0
        while not self.at_end():
            ch = self.peek()
            if ctx == WORD_CTX_REGEX:
                if ch == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                    self.advance()
                    self.advance()
                    continue
            if ctx != WORD_CTX_NORMAL and self._is_word_terminator(ctx, ch, bracket_depth, paren_depth):
                break
            if ctx == WORD_CTX_NORMAL and ch == "[":
                if bracket_depth > 0:
                    bracket_depth += 1
                    chars.append(self.advance())
                    continue
                if chars and at_command_start and not seen_equals and _is_array_assignment_prefix(chars):
                    prev_char = chars[-1]
                    if prev_char.isalnum() or prev_char == "_":
                        bracket_start_pos = self.pos
                        bracket_depth += 1
                        chars.append(self.advance())
                        continue
                if not chars and not seen_equals and in_array_literal:
                    bracket_start_pos = self.pos
                    bracket_depth += 1
                    chars.append(self.advance())
                    continue
            if ctx == WORD_CTX_NORMAL and ch == "]" and bracket_depth > 0:
                bracket_depth -= 1
                chars.append(self.advance())
                continue
            if ctx == WORD_CTX_NORMAL and ch == "=" and bracket_depth == 0:
                seen_equals = True
            if ctx == WORD_CTX_REGEX and ch == "(":
                paren_depth += 1
                chars.append(self.advance())
                continue
            if ctx == WORD_CTX_REGEX and ch == ")":
                if paren_depth > 0:
                    paren_depth -= 1
                    chars.append(self.advance())
                    continue
                break
            if (ctx == WORD_CTX_COND or ctx == WORD_CTX_REGEX) and ch == "[":
                for_regex = ctx == WORD_CTX_REGEX
                if self._read_bracket_expression(chars, parts, for_regex, paren_depth):
                    continue
                chars.append(self.advance())
                continue
            if ctx == WORD_CTX_COND and ch == "(":
                if self._extglob and chars and _is_extglob_prefix(chars[-1]):
                    chars.append(self.advance())
                    content = self._parse_matched_pair("(", ")", MatchedPairFlags_EXTGLOB, False)
                    chars.append(content)
                    chars.append(")")
                    continue
                else:
                    break
            if ctx == WORD_CTX_REGEX and _is_whitespace(ch) and paren_depth > 0:
                chars.append(self.advance())
                continue
            if ch == "'":
                self.advance()
                track_newline = ctx == WORD_CTX_NORMAL
                content, saw_newline = self._read_single_quote(start)
                chars.append(content)
                if track_newline and saw_newline and self._parser is not None:
                    self._parser._saw_newline_in_single_quote = True
                continue
            if ch == "\"":
                self.advance()
                if ctx == WORD_CTX_NORMAL:
                    chars.append("\"")
                    in_single_in_dquote = False
                    while not self.at_end() and (in_single_in_dquote or self.peek() != "\""):
                        c = self.peek()
                        if in_single_in_dquote:
                            chars.append(self.advance())
                            if c == "'":
                                in_single_in_dquote = False
                            continue
                        if c == "\\" and self.pos + 1 < self.length:
                            next_c = self.source[self.pos + 1]
                            if next_c == "\n":
                                self.advance()
                                self.advance()
                            else:
                                chars.append(self.advance())
                                chars.append(self.advance())
                        elif c == "$":
                            self._sync_to_parser()
                            if not self._parser._parse_dollar_expansion(chars, parts, True):
                                self._sync_from_parser()
                                chars.append(self.advance())
                            else:
                                self._sync_from_parser()
                        elif c == "`":
                            self._sync_to_parser()
                            cmdsub_result0, cmdsub_result1 = self._parser._parse_backtick_substitution()
                            self._sync_from_parser()
                            if cmdsub_result0 is not None:
                                parts.append(cmdsub_result0)
                                chars.append(cmdsub_result1)
                            else:
                                chars.append(self.advance())
                        else:
                            chars.append(self.advance())
                    if self.at_end():
                        raise ParseError("Unterminated double quote", start)
                    chars.append(self.advance())
                else:
                    handle_line_continuation = ctx == WORD_CTX_COND
                    self._sync_to_parser()
                    self._parser._scan_double_quote(chars, parts, start, handle_line_continuation)
                    self._sync_from_parser()
                continue
            if ch == "\\" and self.pos + 1 < self.length:
                next_ch = self.source[self.pos + 1]
                if ctx != WORD_CTX_REGEX and next_ch == "\n":
                    self.advance()
                    self.advance()
                else:
                    chars.append(self.advance())
                    chars.append(self.advance())
                continue
            if ctx != WORD_CTX_REGEX and ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "'":
                ansi_result0, ansi_result1 = self._read_ansi_c_quote()
                if ansi_result0 is not None:
                    parts.append(ansi_result0)
                    chars.append(ansi_result1)
                else:
                    chars.append(self.advance())
                continue
            if ctx != WORD_CTX_REGEX and ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\"":
                locale_result0, locale_result1, locale_result2 = self._read_locale_string()
                if locale_result0 is not None:
                    parts.append(locale_result0)
                    parts.extend(locale_result2)
                    chars.append(locale_result1)
                else:
                    chars.append(self.advance())
                continue
            if ch == "$":
                self._sync_to_parser()
                if not self._parser._parse_dollar_expansion(chars, parts, False):
                    self._sync_from_parser()
                    chars.append(self.advance())
                else:
                    self._sync_from_parser()
                    if self._extglob and ctx == WORD_CTX_NORMAL and chars and len(chars[-1]) == 2 and chars[-1][0] == "$" and (chars[-1][1] in "?*@") and not self.at_end() and self.peek() == "(":
                        chars.append(self.advance())
                        content = self._parse_matched_pair("(", ")", MatchedPairFlags_EXTGLOB, False)
                        chars.append(content)
                        chars.append(")")
                continue
            if ctx != WORD_CTX_REGEX and ch == "`":
                self._sync_to_parser()
                cmdsub_result0, cmdsub_result1 = self._parser._parse_backtick_substitution()
                self._sync_from_parser()
                if cmdsub_result0 is not None:
                    parts.append(cmdsub_result0)
                    chars.append(cmdsub_result1)
                else:
                    chars.append(self.advance())
                continue
            if ctx != WORD_CTX_REGEX and _is_redirect_char(ch) and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                self._sync_to_parser()
                procsub_result0, procsub_result1 = self._parser._parse_process_substitution()
                self._sync_from_parser()
                if procsub_result0 is not None:
                    parts.append(procsub_result0)
                    chars.append(procsub_result1)
                elif procsub_result1:
                    chars.append(procsub_result1)
                else:
                    chars.append(self.advance())
                    if ctx == WORD_CTX_NORMAL:
                        chars.append(self.advance())
                continue
            if ctx == WORD_CTX_NORMAL and ch == "(" and chars and bracket_depth == 0:
                is_array_assign = False
                if len(chars) >= 3 and chars[-2] == "+" and chars[-1] == "=":
                    is_array_assign = _is_array_assignment_prefix(chars[:-2])
                elif chars[-1] == "=" and len(chars) >= 2:
                    is_array_assign = _is_array_assignment_prefix(chars[:-1])
                if is_array_assign and (at_command_start or in_assign_builtin):
                    self._sync_to_parser()
                    array_result0, array_result1 = self._parser._parse_array_literal()
                    self._sync_from_parser()
                    if array_result0 is not None:
                        parts.append(array_result0)
                        chars.append(array_result1)
                    else:
                        break
                    continue
            if self._extglob and ctx == WORD_CTX_NORMAL and _is_extglob_prefix(ch) and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                chars.append(self.advance())
                chars.append(self.advance())
                content = self._parse_matched_pair("(", ")", MatchedPairFlags_EXTGLOB, False)
                chars.append(content)
                chars.append(")")
                continue
            if ctx == WORD_CTX_NORMAL and self._parser_state & ParserStateFlags_PST_EOFTOKEN and self._eof_token != "" and ch == self._eof_token and bracket_depth == 0:
                if not chars:
                    chars.append(self.advance())
                break
            if ctx == WORD_CTX_NORMAL and _is_metachar(ch) and bracket_depth == 0:
                break
            chars.append(self.advance())
        if bracket_depth > 0 and bracket_start_pos != -1 and self.at_end():
            raise MatchedPairError("unexpected EOF looking for `]'", bracket_start_pos)
        if not chars:
            return None
        if parts:
            return Word(value="".join(chars), parts=parts, kind="word")
        return Word(value="".join(chars), kind="word")

    def _read_word(self) -> Token:
        start = self.pos
        if self.pos >= self.length:
            return None
        c = self.peek()
        if c == "":
            return None
        is_procsub = (c == "<" or c == ">") and self.pos + 1 < self.length and self.source[self.pos + 1] == "("
        is_regex_paren = self._word_context == WORD_CTX_REGEX and (c == "(" or c == ")")
        if self.is_metachar(c) and not is_procsub and not is_regex_paren:
            return None
        word = self._read_word_internal(self._word_context, self._at_command_start, self._in_array_literal, self._in_assign_builtin)
        if word is None:
            return None
        return Token(type=TokenType_WORD, value=word.value, pos=start, word=word)

    def next_token(self) -> Token:
        if self._token_cache is not None:
            tok = self._token_cache
            self._token_cache = None
            self._last_read_token = tok
            return tok
        self.skip_blanks()
        if self.at_end():
            tok = Token(type=TokenType_EOF, value="", pos=self.pos)
            self._last_read_token = tok
            return tok
        if self._eof_token != "" and self.peek() == self._eof_token and not self._parser_state & ParserStateFlags_PST_CASEPAT and not self._parser_state & ParserStateFlags_PST_EOFTOKEN:
            tok = Token(type=TokenType_EOF, value="", pos=self.pos)
            self._last_read_token = tok
            return tok
        while self._skip_comment():
            self.skip_blanks()
            if self.at_end():
                tok = Token(type=TokenType_EOF, value="", pos=self.pos)
                self._last_read_token = tok
                return tok
            if self._eof_token != "" and self.peek() == self._eof_token and not self._parser_state & ParserStateFlags_PST_CASEPAT and not self._parser_state & ParserStateFlags_PST_EOFTOKEN:
                tok = Token(type=TokenType_EOF, value="", pos=self.pos)
                self._last_read_token = tok
                return tok
        tok = self._read_operator()
        if tok is not None:
            self._last_read_token = tok
            return tok
        tok = self._read_word()
        if tok is not None:
            self._last_read_token = tok
            return tok
        tok = Token(type=TokenType_EOF, value="", pos=self.pos)
        self._last_read_token = tok
        return tok

    def peek_token(self) -> Token:
        if self._token_cache is None:
            saved_last = self._last_read_token
            self._token_cache = self.next_token()
            self._last_read_token = saved_last
        return self._token_cache

    def _read_ansi_c_quote(self) -> tuple[Node | None, str]:
        if self.at_end() or self.peek() != "$":
            return (None, "")
        if self.pos + 1 >= self.length or self.source[self.pos + 1] != "'":
            return (None, "")
        start = self.pos
        self.advance()
        self.advance()
        content_chars: list[str] = []
        found_close = False
        while not self.at_end():
            ch = self.peek()
            if ch == "'":
                self.advance()
                found_close = True
                break
            elif ch == "\\":
                content_chars.append(self.advance())
                if not self.at_end():
                    content_chars.append(self.advance())
            else:
                content_chars.append(self.advance())
        if not found_close:
            raise MatchedPairError("unexpected EOF while looking for matching `''", start)
        text = _substring(self.source, start, self.pos)
        content = "".join(content_chars)
        node = AnsiCQuote(content=content, kind="ansi-c")
        return (node, text)

    def _sync_to_parser(self) -> None:
        if self._parser is not None:
            self._parser.pos = self.pos

    def _sync_from_parser(self) -> None:
        if self._parser is not None:
            self.pos = self._parser.pos

    def _read_locale_string(self) -> tuple[Node | None, str, list[Node]]:
        if self.at_end() or self.peek() != "$":
            return (None, "", [])
        if self.pos + 1 >= self.length or self.source[self.pos + 1] != "\"":
            return (None, "", [])
        start = self.pos
        self.advance()
        self.advance()
        content_chars: list[str] = []
        inner_parts: list[Node] = []
        found_close = False
        while not self.at_end():
            ch = self.peek()
            if ch == "\"":
                self.advance()
                found_close = True
                break
            elif ch == "\\" and self.pos + 1 < self.length:
                next_ch = self.source[self.pos + 1]
                if next_ch == "\n":
                    self.advance()
                    self.advance()
                else:
                    content_chars.append(self.advance())
                    content_chars.append(self.advance())
            elif ch == "$" and self.pos + 2 < self.length and self.source[self.pos + 1] == "(" and self.source[self.pos + 2] == "(":
                self._sync_to_parser()
                arith_node, arith_text = self._parser._parse_arithmetic_expansion()
                self._sync_from_parser()
                if arith_node is not None:
                    inner_parts.append(arith_node)
                    content_chars.append(arith_text)
                else:
                    self._sync_to_parser()
                    cmdsub_node, cmdsub_text = self._parser._parse_command_substitution()
                    self._sync_from_parser()
                    if cmdsub_node is not None:
                        inner_parts.append(cmdsub_node)
                        content_chars.append(cmdsub_text)
                    else:
                        content_chars.append(self.advance())
            elif _is_expansion_start(self.source, self.pos, "$("):
                self._sync_to_parser()
                cmdsub_node, cmdsub_text = self._parser._parse_command_substitution()
                self._sync_from_parser()
                if cmdsub_node is not None:
                    inner_parts.append(cmdsub_node)
                    content_chars.append(cmdsub_text)
                else:
                    content_chars.append(self.advance())
            elif ch == "$":
                self._sync_to_parser()
                param_node, param_text = self._parser._parse_param_expansion(False)
                self._sync_from_parser()
                if param_node is not None:
                    inner_parts.append(param_node)
                    content_chars.append(param_text)
                else:
                    content_chars.append(self.advance())
            elif ch == "`":
                self._sync_to_parser()
                cmdsub_node, cmdsub_text = self._parser._parse_backtick_substitution()
                self._sync_from_parser()
                if cmdsub_node is not None:
                    inner_parts.append(cmdsub_node)
                    content_chars.append(cmdsub_text)
                else:
                    content_chars.append(self.advance())
            else:
                content_chars.append(self.advance())
        if not found_close:
            self.pos = start
            return (None, "", [])
        content = "".join(content_chars)
        text = "$\"" + content + "\""
        return (LocaleString(content=content, kind="locale"), text, inner_parts)

    def _update_dolbrace_for_op(self, op: str, has_param: bool) -> None:
        if self._dolbrace_state == DolbraceState_NONE:
            return
        if op == "" or len(op) == 0:
            return
        first_char = op[0]
        if self._dolbrace_state == DolbraceState_PARAM and has_param:
            if first_char in "%#^,":
                self._dolbrace_state = DolbraceState_QUOTE
                return
            if first_char == "/":
                self._dolbrace_state = DolbraceState_QUOTE2
                return
        if self._dolbrace_state == DolbraceState_PARAM:
            if first_char in "#%^,~:-=?+/":
                self._dolbrace_state = DolbraceState_OP

    def _consume_param_operator(self) -> str:
        if self.at_end():
            return ""
        ch = self.peek()
        if ch == ":":
            self.advance()
            if self.at_end():
                return ":"
            next_ch = self.peek()
            if _is_simple_param_op(next_ch):
                self.advance()
                return ":" + next_ch
            return ":"
        if _is_simple_param_op(ch):
            self.advance()
            return ch
        if ch == "#":
            self.advance()
            if not self.at_end() and self.peek() == "#":
                self.advance()
                return "##"
            return "#"
        if ch == "%":
            self.advance()
            if not self.at_end() and self.peek() == "%":
                self.advance()
                return "%%"
            return "%"
        if ch == "/":
            self.advance()
            if not self.at_end():
                next_ch = self.peek()
                if next_ch == "/":
                    self.advance()
                    return "//"
                elif next_ch == "#":
                    self.advance()
                    return "/#"
                elif next_ch == "%":
                    self.advance()
                    return "/%"
            return "/"
        if ch == "^":
            self.advance()
            if not self.at_end() and self.peek() == "^":
                self.advance()
                return "^^"
            return "^"
        if ch == ",":
            self.advance()
            if not self.at_end() and self.peek() == ",":
                self.advance()
                return ",,"
            return ","
        if ch == "@":
            self.advance()
            return "@"
        return ""

    def _param_subscript_has_close(self, start_pos: int) -> bool:
        depth = 1
        i = start_pos + 1
        quote = NewQuoteState()
        while i < self.length:
            c = self.source[i]
            if quote.single:
                if c == "'":
                    quote.single = False
                i += 1
                continue
            if quote.double:
                if c == "\\" and i + 1 < self.length:
                    i += 2
                    continue
                if c == "\"":
                    quote.double = False
                i += 1
                continue
            if c == "'":
                quote.single = True
                i += 1
                continue
            if c == "\"":
                quote.double = True
                i += 1
                continue
            if c == "\\":
                i += 2
                continue
            if c == "}":
                return False
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return True
            i += 1
        return False

    def _consume_param_name(self) -> str:
        if self.at_end():
            return ""
        ch = self.peek()
        if _is_special_param(ch):
            if ch == "$" and self.pos + 1 < self.length and (self.source[self.pos + 1] in "{'\""):
                return ""
            self.advance()
            return ch
        if ch.isdigit():
            name_chars: list[str] = []
            while not self.at_end() and self.peek().isdigit():
                name_chars.append(self.advance())
            return "".join(name_chars)
        if ch.isalpha() or ch == "_":
            name_chars = []
            while not self.at_end():
                c = self.peek()
                if c.isalnum() or c == "_":
                    name_chars.append(self.advance())
                elif c == "[":
                    if not self._param_subscript_has_close(self.pos):
                        break
                    name_chars.append(self.advance())
                    content = self._parse_matched_pair("[", "]", MatchedPairFlags_ARRAYSUB, False)
                    name_chars.append(content)
                    name_chars.append("]")
                    break
                else:
                    break
            if name_chars:
                return "".join(name_chars)
            else:
                return ""
        return ""

    def _read_param_expansion(self, in_dquote: bool) -> tuple[Node | None, str]:
        if self.at_end() or self.peek() != "$":
            return (None, "")
        start = self.pos
        self.advance()
        if self.at_end():
            self.pos = start
            return (None, "")
        ch = self.peek()
        if ch == "{":
            self.advance()
            return self._read_braced_param(start, in_dquote)
        if _is_special_param_unbraced(ch) or _is_digit(ch) or ch == "#":
            self.advance()
            text = _substring(self.source, start, self.pos)
            return (ParamExpansion(param=ch, kind="param"), text)
        if ch.isalpha() or ch == "_":
            name_start = self.pos
            while not self.at_end():
                c = self.peek()
                if c.isalnum() or c == "_":
                    self.advance()
                else:
                    break
            name = _substring(self.source, name_start, self.pos)
            text = _substring(self.source, start, self.pos)
            return (ParamExpansion(param=name, kind="param"), text)
        self.pos = start
        return (None, "")

    def _read_braced_param(self, start: int, in_dquote: bool) -> tuple[Node | None, str]:
        if self.at_end():
            raise MatchedPairError("unexpected EOF looking for `}'", start)
        saved_dolbrace = self._dolbrace_state
        self._dolbrace_state = DolbraceState_PARAM
        ch = self.peek()
        if _is_funsub_char(ch):
            self._dolbrace_state = saved_dolbrace
            return self._read_funsub(start)
        if ch == "#":
            self.advance()
            param = self._consume_param_name()
            if param and not self.at_end() and self.peek() == "}":
                self.advance()
                text = _substring(self.source, start, self.pos)
                self._dolbrace_state = saved_dolbrace
                return (ParamLength(param=param, kind="param-len"), text)
            self.pos = start + 2
        if ch == "!":
            self.advance()
            while not self.at_end() and _is_whitespace_no_newline(self.peek()):
                self.advance()
            param = self._consume_param_name()
            if param:
                while not self.at_end() and _is_whitespace_no_newline(self.peek()):
                    self.advance()
                if not self.at_end() and self.peek() == "}":
                    self.advance()
                    text = _substring(self.source, start, self.pos)
                    self._dolbrace_state = saved_dolbrace
                    return (ParamIndirect(param=param, kind="param-indirect"), text)
                if not self.at_end() and _is_at_or_star(self.peek()):
                    suffix = self.advance()
                    trailing = self._parse_matched_pair("{", "}", MatchedPairFlags_DOLBRACE, False)
                    text = _substring(self.source, start, self.pos)
                    self._dolbrace_state = saved_dolbrace
                    return (ParamIndirect(param=param + suffix + trailing, kind="param-indirect"), text)
                op = self._consume_param_operator()
                if op == "" and not self.at_end() and (self.peek() not in "}\"'`"):
                    op = self.advance()
                if op != "" and (op not in "\"'`"):
                    arg = self._parse_matched_pair("{", "}", MatchedPairFlags_DOLBRACE, False)
                    text = _substring(self.source, start, self.pos)
                    self._dolbrace_state = saved_dolbrace
                    return (ParamIndirect(param=param, op=op, arg=arg, kind="param-indirect"), text)
                if self.at_end():
                    self._dolbrace_state = saved_dolbrace
                    raise MatchedPairError("unexpected EOF looking for `}'", start)
                self.pos = start + 2
            else:
                self.pos = start + 2
        param = self._consume_param_name()
        if not param:
            if not self.at_end() and ((self.peek() in "-=+?") or self.peek() == ":" and self.pos + 1 < self.length and _is_simple_param_op(self.source[self.pos + 1])):
                param = ""
            else:
                content = self._parse_matched_pair("{", "}", MatchedPairFlags_DOLBRACE, False)
                text = "${" + content + "}"
                self._dolbrace_state = saved_dolbrace
                return (ParamExpansion(param=content, kind="param"), text)
        if self.at_end():
            self._dolbrace_state = saved_dolbrace
            raise MatchedPairError("unexpected EOF looking for `}'", start)
        if self.peek() == "}":
            self.advance()
            text = _substring(self.source, start, self.pos)
            self._dolbrace_state = saved_dolbrace
            return (ParamExpansion(param=param, kind="param"), text)
        op = self._consume_param_operator()
        if op == "":
            if not self.at_end() and self.peek() == "$" and self.pos + 1 < self.length and (self.source[self.pos + 1] == "\"" or self.source[self.pos + 1] == "'"):
                dollar_count = 1 + _count_consecutive_dollars_before(self.source, self.pos)
                if dollar_count % 2 == 1:
                    op = ""
                else:
                    op = self.advance()
            elif not self.at_end() and self.peek() == "`":
                backtick_pos = self.pos
                self.advance()
                while not self.at_end() and self.peek() != "`":
                    bc = self.peek()
                    if bc == "\\" and self.pos + 1 < self.length:
                        next_c = self.source[self.pos + 1]
                        if _is_escape_char_in_backtick(next_c):
                            self.advance()
                    self.advance()
                if self.at_end():
                    self._dolbrace_state = saved_dolbrace
                    raise ParseError("Unterminated backtick", backtick_pos)
                self.advance()
                op = "`"
            elif not self.at_end() and self.peek() == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "{":
                op = ""
            elif not self.at_end() and (self.peek() == "'" or self.peek() == "\""):
                op = ""
            elif not self.at_end() and self.peek() == "\\":
                op = self.advance()
                if not self.at_end():
                    op += self.advance()
            else:
                op = self.advance()
        self._update_dolbrace_for_op(op, len(param) > 0)
        try:
            flags = MatchedPairFlags_DQUOTE if in_dquote else MatchedPairFlags_NONE
            param_ends_with_dollar = param != "" and param.endswith("$")
            arg = self._collect_param_argument(flags, param_ends_with_dollar)
        except MatchedPairError as e:
            self._dolbrace_state = saved_dolbrace
            raise e
        if (op == "<" or op == ">") and arg.startswith("(") and arg.endswith(")"):
            inner = arg[1:-1]
            try:
                sub_parser = NewParser(inner, True, self._parser._extglob)
                parsed = sub_parser.parse_list(True)
                if parsed is not None and sub_parser.at_end():
                    formatted = _format_cmdsub_node(parsed, 0, True, False, True)
                    arg = "(" + formatted + ")"
            except Exception as _e:
                pass
        text = "${" + param + op + arg + "}"
        self._dolbrace_state = saved_dolbrace
        return (ParamExpansion(param=param, op=op, arg=arg, kind="param"), text)

    def _read_funsub(self, start: int) -> tuple[Node | None, str]:
        return self._parser._parse_funsub(start)


@dataclass
class Word(Node):
    value: str = ""
    parts: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        value = self.value
        value = self._expand_all_ansi_c_quotes(value)
        value = self._strip_locale_string_dollars(value)
        value = self._normalize_array_whitespace(value)
        value = self._format_command_substitutions(value, False)
        value = self._normalize_param_expansion_newlines(value)
        value = self._strip_arith_line_continuations(value)
        value = self._double_ctlesc_smart(value)
        value = value.replace("\u007f", "\u0001\u007f")
        value = value.replace("\\", "\\\\")
        if value.endswith("\\\\") and not value.endswith("\\\\\\\\"):
            value = value + "\\\\"
        escaped = value.replace("\"", "\\\"").replace("\n", "\\n").replace("\t", "\\t")
        return "(word \"" + escaped + "\")"

    def _append_with_ctlesc(self, result: list[int], byte_val: int) -> None:
        result.append(byte_val)

    def _double_ctlesc_smart(self, value: str) -> str:
        result = []
        quote = NewQuoteState()
        for c in value:
            if c == "'" and not quote.double:
                quote.single = not quote.single
            elif c == "\"" and not quote.single:
                quote.double = not quote.double
            result.append(c)
            if c == "\u0001":
                if quote.double:
                    bs_count = 0
                    j: int = len(result) - 2
                    while j > -1:
                        if result[j] == "\\":
                            bs_count += 1
                        else:
                            break
                        j += -1
                    if bs_count % 2 == 0:
                        result.append("\u0001")
                else:
                    result.append("\u0001")
        return "".join(result)

    def _normalize_param_expansion_newlines(self, value: str) -> str:
        result = []
        i = 0
        quote = NewQuoteState()
        while i < len(value):
            c = value[i]
            if c == "'" and not quote.double:
                quote.single = not quote.single
                result.append(c)
                i += 1
            elif c == "\"" and not quote.single:
                quote.double = not quote.double
                result.append(c)
                i += 1
            elif _is_expansion_start(value, i, "${") and not quote.single:
                result.append("$")
                result.append("{")
                i += 2
                had_leading_newline = i < len(value) and value[i] == "\n"
                if had_leading_newline:
                    result.append(" ")
                    i += 1
                depth = 1
                while i < len(value) and depth > 0:
                    ch = value[i]
                    if ch == "\\" and i + 1 < len(value) and not quote.single:
                        if value[i + 1] == "\n":
                            i += 2
                            continue
                        result.append(ch)
                        result.append(value[i + 1])
                        i += 2
                        continue
                    if ch == "'" and not quote.double:
                        quote.single = not quote.single
                    elif ch == "\"" and not quote.single:
                        quote.double = not quote.double
                    elif not quote.in_quotes():
                        if ch == "{":
                            depth += 1
                        elif ch == "}":
                            depth -= 1
                            if depth == 0:
                                if had_leading_newline:
                                    result.append(" ")
                                result.append(ch)
                                i += 1
                                break
                    result.append(ch)
                    i += 1
            else:
                result.append(c)
                i += 1
        return "".join(result)

    def _sh_single_quote(self, s: str) -> str:
        if not s:
            return "''"
        if s == "'":
            return "\\'"
        result = ["'"]
        for c in s:
            if c == "'":
                result.append("'\\''")
            else:
                result.append(c)
        result.append("'")
        return "".join(result)

    def _ansi_c_to_bytes(self, inner: str) -> list[int]:
        result = []
        i = 0
        while i < len(inner):
            if inner[i] == "\\" and i + 1 < len(inner):
                c = inner[i + 1]
                simple = _get_ansi_escape(c)
                if simple >= 0:
                    result.append(simple)
                    i += 2
                elif c == "'":
                    result.append(39)
                    i += 2
                elif c == "x":
                    if i + 2 < len(inner) and inner[i + 2] == "{":
                        j = i + 3
                        while j < len(inner) and _is_hex_digit(inner[j]):
                            j += 1
                        hex_str = _substring(inner, i + 3, j)
                        if j < len(inner) and inner[j] == "}":
                            j += 1
                        if not hex_str:
                            return result
                        byte_val = int(hex_str, 16) & 255
                        if byte_val == 0:
                            return result
                        self._append_with_ctlesc(result, byte_val)
                        i = j
                    else:
                        j = i + 2
                        while j < len(inner) and j < i + 4 and _is_hex_digit(inner[j]):
                            j += 1
                        if j > i + 2:
                            byte_val = int(_substring(inner, i + 2, j), 16)
                            if byte_val == 0:
                                return result
                            self._append_with_ctlesc(result, byte_val)
                            i = j
                        else:
                            result.append(ord(inner[i][0]))
                            i += 1
                elif c == "u":
                    j = i + 2
                    while j < len(inner) and j < i + 6 and _is_hex_digit(inner[j]):
                        j += 1
                    if j > i + 2:
                        codepoint = int(_substring(inner, i + 2, j), 16)
                        if codepoint == 0:
                            return result
                        result.extend(chr(codepoint).encode("utf-8"))
                        i = j
                    else:
                        result.append(ord(inner[i][0]))
                        i += 1
                elif c == "U":
                    j = i + 2
                    while j < len(inner) and j < i + 10 and _is_hex_digit(inner[j]):
                        j += 1
                    if j > i + 2:
                        codepoint = int(_substring(inner, i + 2, j), 16)
                        if codepoint == 0:
                            return result
                        result.extend(chr(codepoint).encode("utf-8"))
                        i = j
                    else:
                        result.append(ord(inner[i][0]))
                        i += 1
                elif c == "c":
                    if i + 3 <= len(inner):
                        ctrl_char = inner[i + 2]
                        skip_extra = 0
                        if ctrl_char == "\\" and i + 4 <= len(inner) and inner[i + 3] == "\\":
                            skip_extra = 1
                        ctrl_val = ord(ctrl_char[0]) & 31
                        if ctrl_val == 0:
                            return result
                        self._append_with_ctlesc(result, ctrl_val)
                        i += 3 + skip_extra
                    else:
                        result.append(ord(inner[i][0]))
                        i += 1
                elif c == "0":
                    j = i + 2
                    while j < len(inner) and j < i + 4 and _is_octal_digit(inner[j]):
                        j += 1
                    if j > i + 2:
                        byte_val = int(_substring(inner, i + 1, j), 8) & 255
                        if byte_val == 0:
                            return result
                        self._append_with_ctlesc(result, byte_val)
                        i = j
                    else:
                        return result
                elif c >= "1" and c <= "7":
                    j = i + 1
                    while j < len(inner) and j < i + 4 and _is_octal_digit(inner[j]):
                        j += 1
                    byte_val = int(_substring(inner, i + 1, j), 8) & 255
                    if byte_val == 0:
                        return result
                    self._append_with_ctlesc(result, byte_val)
                    i = j
                else:
                    result.append(92)
                    result.append(ord(c[0]))
                    i += 2
            else:
                result.extend(inner[i].encode("utf-8"))
                i += 1
        return result

    def _expand_ansi_c_escapes(self, value: str) -> str:
        if not (value.startswith("'") and value.endswith("'")):
            return value
        inner = _substring(value, 1, len(value) - 1)
        literal_bytes = self._ansi_c_to_bytes(inner)
        literal_str = bytes(literal_bytes).decode("utf-8", errors="replace")
        return self._sh_single_quote(literal_str)

    def _expand_all_ansi_c_quotes(self, value: str) -> str:
        result = []
        i = 0
        quote = NewQuoteState()
        in_backtick = False
        brace_depth = 0
        while i < len(value):
            ch = value[i]
            if ch == "`" and not quote.single:
                in_backtick = not in_backtick
                result.append(ch)
                i += 1
                continue
            if in_backtick:
                if ch == "\\" and i + 1 < len(value):
                    result.append(ch)
                    result.append(value[i + 1])
                    i += 2
                else:
                    result.append(ch)
                    i += 1
                continue
            if not quote.single:
                if _is_expansion_start(value, i, "${"):
                    brace_depth += 1
                    quote.push()
                    result.append("${")
                    i += 2
                    continue
                elif ch == "}" and brace_depth > 0 and not quote.double:
                    brace_depth -= 1
                    result.append(ch)
                    quote.pop()
                    i += 1
                    continue
            effective_in_dquote = quote.double
            if ch == "'" and not effective_in_dquote:
                is_ansi_c = not quote.single and i > 0 and value[i - 1] == "$" and _count_consecutive_dollars_before(value, i - 1) % 2 == 0
                if not is_ansi_c:
                    quote.single = not quote.single
                result.append(ch)
                i += 1
            elif ch == "\"" and not quote.single:
                quote.double = not quote.double
                result.append(ch)
                i += 1
            elif ch == "\\" and i + 1 < len(value) and not quote.single:
                result.append(ch)
                result.append(value[i + 1])
                i += 2
            elif _starts_with_at(value, i, "$'") and not quote.single and not effective_in_dquote and _count_consecutive_dollars_before(value, i) % 2 == 0:
                j = i + 2
                while j < len(value):
                    if value[j] == "\\" and j + 1 < len(value):
                        j += 2
                    elif value[j] == "'":
                        j += 1
                        break
                    else:
                        j += 1
                ansi_str = _substring(value, i, j)
                expanded = self._expand_ansi_c_escapes(_substring(ansi_str, 1, len(ansi_str)))
                outer_in_dquote = quote.outer_double()
                if brace_depth > 0 and outer_in_dquote and expanded.startswith("'") and expanded.endswith("'"):
                    inner = _substring(expanded, 1, len(expanded) - 1)
                    if inner.find("\u0001") == -1:
                        result_str = "".join(result)
                        in_pattern = False
                        last_brace_idx = result_str.rfind("${")
                        if last_brace_idx >= 0:
                            after_brace = result_str[last_brace_idx + 2:]
                            var_name_len = 0
                            if after_brace:
                                if after_brace[0] in "@*#?-$!0123456789_":
                                    var_name_len = 1
                                elif after_brace[0].isalpha() or after_brace[0] == "_":
                                    while var_name_len < len(after_brace):
                                        c = after_brace[var_name_len]
                                        if not (c.isalnum() or c == "_"):
                                            break
                                        var_name_len += 1
                            if var_name_len > 0 and var_name_len < len(after_brace) and (after_brace[0] not in "#?-"):
                                op_start = after_brace[var_name_len:]
                                if op_start.startswith("@") and len(op_start) > 1:
                                    op_start = op_start[1:]
                                for op in ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]:
                                    if op_start.startswith(op):
                                        in_pattern = True
                                        break
                                if not in_pattern and op_start and (op_start[0] not in "%#/^,~:+-=?"):
                                    for op in ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]:
                                        if op in op_start:
                                            in_pattern = True
                                            break
                            elif var_name_len == 0 and len(after_brace) > 1:
                                first_char = after_brace[0]
                                if first_char not in "%#/^,":
                                    rest = after_brace[1:]
                                    for op in ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]:
                                        if op in rest:
                                            in_pattern = True
                                            break
                        if not in_pattern:
                            expanded = inner
                result.append(expanded)
                i = j
            else:
                result.append(ch)
                i += 1
        return "".join(result)

    def _strip_locale_string_dollars(self, value: str) -> str:
        result = []
        i = 0
        brace_depth = 0
        bracket_depth = 0
        quote = NewQuoteState()
        brace_quote = NewQuoteState()
        bracket_in_double_quote = False
        while i < len(value):
            ch = value[i]
            if ch == "\\" and i + 1 < len(value) and not quote.single and not brace_quote.single:
                result.append(ch)
                result.append(value[i + 1])
                i += 2
            elif _starts_with_at(value, i, "${") and not quote.single and not brace_quote.single and (i == 0 or value[i - 1] != "$"):
                brace_depth += 1
                brace_quote.double = False
                brace_quote.single = False
                result.append("$")
                result.append("{")
                i += 2
            elif ch == "}" and brace_depth > 0 and not quote.single and not brace_quote.double and not brace_quote.single:
                brace_depth -= 1
                result.append(ch)
                i += 1
            elif ch == "[" and brace_depth > 0 and not quote.single and not brace_quote.double:
                bracket_depth += 1
                bracket_in_double_quote = False
                result.append(ch)
                i += 1
            elif ch == "]" and bracket_depth > 0 and not quote.single and not bracket_in_double_quote:
                bracket_depth -= 1
                result.append(ch)
                i += 1
            elif ch == "'" and not quote.double and brace_depth == 0:
                quote.single = not quote.single
                result.append(ch)
                i += 1
            elif ch == "\"" and not quote.single and brace_depth == 0:
                quote.double = not quote.double
                result.append(ch)
                i += 1
            elif ch == "\"" and not quote.single and bracket_depth > 0:
                bracket_in_double_quote = not bracket_in_double_quote
                result.append(ch)
                i += 1
            elif ch == "\"" and not quote.single and not brace_quote.single and brace_depth > 0:
                brace_quote.double = not brace_quote.double
                result.append(ch)
                i += 1
            elif ch == "'" and not quote.double and not brace_quote.double and brace_depth > 0:
                brace_quote.single = not brace_quote.single
                result.append(ch)
                i += 1
            elif _starts_with_at(value, i, "$\"") and not quote.single and not brace_quote.single and (brace_depth > 0 or bracket_depth > 0 or not quote.double) and not brace_quote.double and not bracket_in_double_quote:
                dollar_count = 1 + _count_consecutive_dollars_before(value, i)
                if dollar_count % 2 == 1:
                    result.append("\"")
                    if bracket_depth > 0:
                        bracket_in_double_quote = True
                    elif brace_depth > 0:
                        brace_quote.double = True
                    else:
                        quote.double = True
                    i += 2
                else:
                    result.append(ch)
                    i += 1
            else:
                result.append(ch)
                i += 1
        return "".join(result)

    def _normalize_array_whitespace(self, value: str) -> str:
        i = 0
        if not (i < len(value) and (value[i].isalpha() or value[i] == "_")):
            return value
        i += 1
        while i < len(value) and (value[i].isalnum() or value[i] == "_"):
            i += 1
        while i < len(value) and value[i] == "[":
            depth = 1
            i += 1
            while i < len(value) and depth > 0:
                if value[i] == "[":
                    depth += 1
                elif value[i] == "]":
                    depth -= 1
                i += 1
            if depth != 0:
                return value
        if i < len(value) and value[i] == "+":
            i += 1
        if not (i + 1 < len(value) and value[i] == "=" and value[i + 1] == "("):
            return value
        prefix = _substring(value, 0, i + 1)
        open_paren_pos = i + 1
        if value.endswith(")"):
            close_paren_pos = len(value) - 1
        else:
            close_paren_pos = self._find_matching_paren(value, open_paren_pos)
            if close_paren_pos < 0:
                return value
        inner = _substring(value, open_paren_pos + 1, close_paren_pos)
        suffix = _substring(value, close_paren_pos + 1, len(value))
        result = self._normalize_array_inner(inner)
        return prefix + "(" + result + ")" + suffix

    def _find_matching_paren(self, value: str, open_pos: int) -> int:
        if open_pos >= len(value) or value[open_pos] != "(":
            return -1
        i = open_pos + 1
        depth = 1
        quote = NewQuoteState()
        while i < len(value) and depth > 0:
            ch = value[i]
            if ch == "\\" and i + 1 < len(value) and not quote.single:
                i += 2
                continue
            if ch == "'" and not quote.double:
                quote.single = not quote.single
                i += 1
                continue
            if ch == "\"" and not quote.single:
                quote.double = not quote.double
                i += 1
                continue
            if quote.single or quote.double:
                i += 1
                continue
            if ch == "#":
                while i < len(value) and value[i] != "\n":
                    i += 1
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _normalize_array_inner(self, inner: str) -> str:
        normalized = []
        i = 0
        in_whitespace = True
        brace_depth = 0
        bracket_depth = 0
        while i < len(inner):
            ch = inner[i]
            if _is_whitespace(ch):
                if not in_whitespace and normalized and brace_depth == 0 and bracket_depth == 0:
                    normalized.append(" ")
                    in_whitespace = True
                if brace_depth > 0 or bracket_depth > 0:
                    normalized.append(ch)
                i += 1
            elif ch == "'":
                in_whitespace = False
                j = i + 1
                while j < len(inner) and inner[j] != "'":
                    j += 1
                normalized.append(_substring(inner, i, j + 1))
                i = j + 1
            elif ch == "\"":
                in_whitespace = False
                j = i + 1
                dq_content = ["\""]
                dq_brace_depth = 0
                while j < len(inner):
                    if inner[j] == "\\" and j + 1 < len(inner):
                        if inner[j + 1] == "\n":
                            j += 2
                        else:
                            dq_content.append(inner[j])
                            dq_content.append(inner[j + 1])
                            j += 2
                    elif _is_expansion_start(inner, j, "${"):
                        dq_content.append("${")
                        dq_brace_depth += 1
                        j += 2
                    elif inner[j] == "}" and dq_brace_depth > 0:
                        dq_content.append("}")
                        dq_brace_depth -= 1
                        j += 1
                    elif inner[j] == "\"" and dq_brace_depth == 0:
                        dq_content.append("\"")
                        j += 1
                        break
                    else:
                        dq_content.append(inner[j])
                        j += 1
                normalized.append("".join(dq_content))
                i = j
            elif ch == "\\" and i + 1 < len(inner):
                if inner[i + 1] == "\n":
                    i += 2
                else:
                    in_whitespace = False
                    normalized.append(_substring(inner, i, i + 2))
                    i += 2
            elif _is_expansion_start(inner, i, "$(("):
                in_whitespace = False
                j = i + 3
                depth = 1
                while j < len(inner) and depth > 0:
                    if j + 1 < len(inner) and inner[j] == "(" and inner[j + 1] == "(":
                        depth += 1
                        j += 2
                    elif j + 1 < len(inner) and inner[j] == ")" and inner[j + 1] == ")":
                        depth -= 1
                        j += 2
                    else:
                        j += 1
                normalized.append(_substring(inner, i, j))
                i = j
            elif _is_expansion_start(inner, i, "$("):
                in_whitespace = False
                j = i + 2
                depth = 1
                while j < len(inner) and depth > 0:
                    if inner[j] == "(" and j > 0 and inner[j - 1] == "$":
                        depth += 1
                    elif inner[j] == ")":
                        depth -= 1
                    elif inner[j] == "'":
                        j += 1
                        while j < len(inner) and inner[j] != "'":
                            j += 1
                    elif inner[j] == "\"":
                        j += 1
                        while j < len(inner):
                            if inner[j] == "\\" and j + 1 < len(inner):
                                j += 2
                                continue
                            if inner[j] == "\"":
                                break
                            j += 1
                    j += 1
                normalized.append(_substring(inner, i, j))
                i = j
            elif (ch == "<" or ch == ">") and i + 1 < len(inner) and inner[i + 1] == "(":
                in_whitespace = False
                j = i + 2
                depth = 1
                while j < len(inner) and depth > 0:
                    if inner[j] == "(":
                        depth += 1
                    elif inner[j] == ")":
                        depth -= 1
                    elif inner[j] == "'":
                        j += 1
                        while j < len(inner) and inner[j] != "'":
                            j += 1
                    elif inner[j] == "\"":
                        j += 1
                        while j < len(inner):
                            if inner[j] == "\\" and j + 1 < len(inner):
                                j += 2
                                continue
                            if inner[j] == "\"":
                                break
                            j += 1
                    j += 1
                normalized.append(_substring(inner, i, j))
                i = j
            elif _is_expansion_start(inner, i, "${"):
                in_whitespace = False
                normalized.append("${")
                brace_depth += 1
                i += 2
            elif ch == "{" and brace_depth > 0:
                normalized.append(ch)
                brace_depth += 1
                i += 1
            elif ch == "}" and brace_depth > 0:
                normalized.append(ch)
                brace_depth -= 1
                i += 1
            elif ch == "#" and brace_depth == 0 and in_whitespace:
                while i < len(inner) and inner[i] != "\n":
                    i += 1
            elif ch == "[":
                if in_whitespace or bracket_depth > 0:
                    bracket_depth += 1
                in_whitespace = False
                normalized.append(ch)
                i += 1
            elif ch == "]" and bracket_depth > 0:
                normalized.append(ch)
                bracket_depth -= 1
                i += 1
            else:
                in_whitespace = False
                normalized.append(ch)
                i += 1
        return "".join(normalized).rstrip(" \t\n\r")

    def _strip_arith_line_continuations(self, value: str) -> str:
        result = []
        i = 0
        while i < len(value):
            if _is_expansion_start(value, i, "$(("):
                start = i
                i += 3
                depth = 2
                arith_content = []
                first_close_idx: int = -1
                while i < len(value) and depth > 0:
                    if value[i] == "(":
                        arith_content.append("(")
                        depth += 1
                        i += 1
                        if depth > 1:
                            first_close_idx = -1
                    elif value[i] == ")":
                        if depth == 2:
                            first_close_idx = len(arith_content)
                        depth -= 1
                        if depth > 0:
                            arith_content.append(")")
                        i += 1
                    elif value[i] == "\\" and i + 1 < len(value) and value[i + 1] == "\n":
                        num_backslashes = 0
                        j = len(arith_content) - 1
                        while j >= 0 and arith_content[j] == "\n":
                            j -= 1
                        while j >= 0 and arith_content[j] == "\\":
                            num_backslashes += 1
                            j -= 1
                        if num_backslashes % 2 == 1:
                            arith_content.append("\\")
                            arith_content.append("\n")
                            i += 2
                        else:
                            i += 2
                        if depth == 1:
                            first_close_idx = -1
                    else:
                        arith_content.append(value[i])
                        i += 1
                        if depth == 1:
                            first_close_idx = -1
                if depth == 0 or depth == 1 and first_close_idx != -1:
                    content = "".join(arith_content)
                    if first_close_idx != -1:
                        content = content[:first_close_idx]
                        closing = "))" if depth == 0 else ")"
                        result.append("$((" + content + closing)
                    else:
                        result.append("$((" + content + ")")
                else:
                    result.append(_substring(value, start, i))
            else:
                result.append(value[i])
                i += 1
        return "".join(result)

    def _collect_cmdsubs(self, node: Node) -> list[Node]:
        result: list[Node] = []
        if isinstance(node, CommandSubstitution):
            node = node
            result.append(node)
        elif isinstance(node, Array):
            node = node
            for elem in (node.elements or []):
                for p in (elem.parts or []):
                    if isinstance(p, CommandSubstitution):
                        p = p
                        result.append(p)
                    else:
                        result.extend(self._collect_cmdsubs(p))
        elif isinstance(node, ArithmeticExpansion):
            node = node
            if node.expression is not None:
                result.extend(self._collect_cmdsubs(node.expression))
        elif isinstance(node, ArithBinaryOp):
            node = node
            result.extend(self._collect_cmdsubs(node.left))
            result.extend(self._collect_cmdsubs(node.right))
        elif isinstance(node, ArithComma):
            node = node
            result.extend(self._collect_cmdsubs(node.left))
            result.extend(self._collect_cmdsubs(node.right))
        elif isinstance(node, ArithUnaryOp):
            node = node
            result.extend(self._collect_cmdsubs(node.operand))
        elif isinstance(node, ArithPreIncr):
            node = node
            result.extend(self._collect_cmdsubs(node.operand))
        elif isinstance(node, ArithPostIncr):
            node = node
            result.extend(self._collect_cmdsubs(node.operand))
        elif isinstance(node, ArithPreDecr):
            node = node
            result.extend(self._collect_cmdsubs(node.operand))
        elif isinstance(node, ArithPostDecr):
            node = node
            result.extend(self._collect_cmdsubs(node.operand))
        elif isinstance(node, ArithTernary):
            node = node
            result.extend(self._collect_cmdsubs(node.condition))
            result.extend(self._collect_cmdsubs(node.if_true))
            result.extend(self._collect_cmdsubs(node.if_false))
        elif isinstance(node, ArithAssign):
            node = node
            result.extend(self._collect_cmdsubs(node.target))
            result.extend(self._collect_cmdsubs(node.value))
        return result

    def _collect_procsubs(self, node: Node) -> list[Node]:
        result: list[Node] = []
        if isinstance(node, ProcessSubstitution):
            node = node
            result.append(node)
        elif isinstance(node, Array):
            node = node
            for elem in (node.elements or []):
                for p in (elem.parts or []):
                    if isinstance(p, ProcessSubstitution):
                        p = p
                        result.append(p)
                    else:
                        result.extend(self._collect_procsubs(p))
        return result

    def _format_command_substitutions(self, value: str, in_arith: bool) -> str:
        cmdsub_parts = []
        procsub_parts = []
        has_arith = False
        for p in (self.parts or []):
            if isinstance(p, CommandSubstitution):
                p = p
                cmdsub_parts.append(p)
            elif isinstance(p, ProcessSubstitution):
                p = p
                procsub_parts.append(p)
            elif isinstance(p, ArithmeticExpansion):
                p = p
                has_arith = True
            else:
                cmdsub_parts.extend(self._collect_cmdsubs(p))
                procsub_parts.extend(self._collect_procsubs(p))
        has_brace_cmdsub = value.find("${ ") != -1 or value.find("${\t") != -1 or value.find("${\n") != -1 or value.find("${|") != -1
        has_untracked_cmdsub = False
        has_untracked_procsub = False
        idx = 0
        scan_quote = NewQuoteState()
        while idx < len(value):
            if value[idx] == "\"":
                scan_quote.double = not scan_quote.double
                idx += 1
            elif value[idx] == "'" and not scan_quote.double:
                idx += 1
                while idx < len(value) and value[idx] != "'":
                    idx += 1
                if idx < len(value):
                    idx += 1
            elif _starts_with_at(value, idx, "$(") and not _starts_with_at(value, idx, "$((") and not _is_backslash_escaped(value, idx) and not _is_dollar_dollar_paren(value, idx):
                has_untracked_cmdsub = True
                break
            elif (_starts_with_at(value, idx, "<(") or _starts_with_at(value, idx, ">(")) and not scan_quote.double:
                if idx == 0 or not value[idx - 1].isalnum() and (value[idx - 1] not in "\"'"):
                    has_untracked_procsub = True
                    break
                idx += 1
            else:
                idx += 1
        has_param_with_procsub_pattern = ("${" in value) and (("<(" in value) or (">(" in value))
        if not cmdsub_parts and not procsub_parts and not has_brace_cmdsub and not has_untracked_cmdsub and not has_untracked_procsub and not has_param_with_procsub_pattern:
            return value
        result = []
        i = 0
        cmdsub_idx = 0
        procsub_idx = 0
        main_quote = NewQuoteState()
        extglob_depth = 0
        deprecated_arith_depth = 0
        arith_depth = 0
        arith_paren_depth = 0
        while i < len(value):
            if i > 0 and _is_extglob_prefix(value[i - 1]) and value[i] == "(" and not _is_backslash_escaped(value, i - 1):
                extglob_depth += 1
                result.append(value[i])
                i += 1
                continue
            if value[i] == ")" and extglob_depth > 0:
                extglob_depth -= 1
                result.append(value[i])
                i += 1
                continue
            if _starts_with_at(value, i, "$[") and not _is_backslash_escaped(value, i):
                deprecated_arith_depth += 1
                result.append(value[i])
                i += 1
                continue
            if value[i] == "]" and deprecated_arith_depth > 0:
                deprecated_arith_depth -= 1
                result.append(value[i])
                i += 1
                continue
            if _is_expansion_start(value, i, "$((") and not _is_backslash_escaped(value, i) and has_arith:
                arith_depth += 1
                arith_paren_depth += 2
                result.append("$((")
                i += 3
                continue
            if arith_depth > 0 and arith_paren_depth == 2 and _starts_with_at(value, i, "))"):
                arith_depth -= 1
                arith_paren_depth -= 2
                result.append("))")
                i += 2
                continue
            if arith_depth > 0:
                if value[i] == "(":
                    arith_paren_depth += 1
                    result.append(value[i])
                    i += 1
                    continue
                elif value[i] == ")":
                    arith_paren_depth -= 1
                    result.append(value[i])
                    i += 1
                    continue
            if _is_expansion_start(value, i, "$((") and not has_arith:
                j = _find_cmdsub_end(value, i + 2)
                result.append(_substring(value, i, j))
                if cmdsub_idx < len(cmdsub_parts):
                    cmdsub_idx += 1
                i = j
                continue
            if _starts_with_at(value, i, "$(") and not _starts_with_at(value, i, "$((") and not _is_backslash_escaped(value, i) and not _is_dollar_dollar_paren(value, i):
                j = _find_cmdsub_end(value, i + 2)
                if extglob_depth > 0:
                    result.append(_substring(value, i, j))
                    if cmdsub_idx < len(cmdsub_parts):
                        cmdsub_idx += 1
                    i = j
                    continue
                inner = _substring(value, i + 2, j - 1)
                if cmdsub_idx < len(cmdsub_parts):
                    node = cmdsub_parts[cmdsub_idx]
                    formatted = _format_cmdsub_node(node.command, 0, False, False, False)
                    cmdsub_idx += 1
                else:
                    try:
                        parser = NewParser(inner, False, False)
                        parsed = parser.parse_list(True)
                        formatted = _format_cmdsub_node(parsed, 0, False, False, False) if parsed is not None else ""
                    except Exception as _e:
                        formatted = inner
                if formatted.startswith("("):
                    result.append("$( " + formatted + ")")
                else:
                    result.append("$(" + formatted + ")")
                i = j
            elif value[i] == "`" and cmdsub_idx < len(cmdsub_parts):
                j = i + 1
                while j < len(value):
                    if value[j] == "\\" and j + 1 < len(value):
                        j += 2
                        continue
                    if value[j] == "`":
                        j += 1
                        break
                    j += 1
                result.append(_substring(value, i, j))
                cmdsub_idx += 1
                i = j
            elif _is_expansion_start(value, i, "${") and i + 2 < len(value) and _is_funsub_char(value[i + 2]) and not _is_backslash_escaped(value, i):
                j = _find_funsub_end(value, i + 2)
                cmdsub_node = cmdsub_parts[cmdsub_idx] if cmdsub_idx < len(cmdsub_parts) else None
                if isinstance(cmdsub_node, CommandSubstitution) and cmdsub_node.brace:
                    node = cmdsub_node
                    formatted = _format_cmdsub_node(node.command, 0, False, False, False)
                    has_pipe = value[i + 2] == "|"
                    prefix = "${|" if has_pipe else "${ "
                    orig_inner = _substring(value, i + 2, j - 1)
                    ends_with_newline = orig_inner.endswith("\n")
                    if not formatted or formatted.isspace():
                        suffix = "}"
                    elif formatted.endswith("&") or formatted.endswith("& "):
                        suffix = " }" if formatted.endswith("&") else "}"
                    elif ends_with_newline:
                        suffix = "\n }"
                    else:
                        suffix = "; }"
                    result.append(prefix + formatted + suffix)
                    cmdsub_idx += 1
                else:
                    result.append(_substring(value, i, j))
                i = j
            elif (_starts_with_at(value, i, ">(") or _starts_with_at(value, i, "<(")) and not main_quote.double and deprecated_arith_depth == 0 and arith_depth == 0:
                is_procsub = i == 0 or not value[i - 1].isalnum() and (value[i - 1] not in "\"'")
                if extglob_depth > 0:
                    j = _find_cmdsub_end(value, i + 2)
                    result.append(_substring(value, i, j))
                    if procsub_idx < len(procsub_parts):
                        procsub_idx += 1
                    i = j
                    continue
                if procsub_idx < len(procsub_parts):
                    direction = value[i]
                    j = _find_cmdsub_end(value, i + 2)
                    node = procsub_parts[procsub_idx]
                    compact = _starts_with_subshell(node.command)
                    formatted = _format_cmdsub_node(node.command, 0, True, compact, True)
                    raw_content = _substring(value, i + 2, j - 1)
                    if node.command.kind == "subshell":
                        leading_ws_end = 0
                        while leading_ws_end < len(raw_content) and (raw_content[leading_ws_end] in " \t\n"):
                            leading_ws_end += 1
                        leading_ws = raw_content[:leading_ws_end]
                        stripped = raw_content[leading_ws_end:]
                        if stripped.startswith("("):
                            if leading_ws:
                                normalized_ws = leading_ws.replace("\n", " ").replace("\t", " ")
                                spaced = _format_cmdsub_node(node.command, 0, False, False, False)
                                result.append(direction + "(" + normalized_ws + spaced + ")")
                            else:
                                raw_content = raw_content.replace("\\\n", "")
                                result.append(direction + "(" + raw_content + ")")
                            procsub_idx += 1
                            i = j
                            continue
                    raw_content = _substring(value, i + 2, j - 1)
                    raw_stripped = raw_content.replace("\\\n", "")
                    if _starts_with_subshell(node.command) and formatted != raw_stripped:
                        result.append(direction + "(" + raw_stripped + ")")
                    else:
                        final_output = direction + "(" + formatted + ")"
                        result.append(final_output)
                    procsub_idx += 1
                    i = j
                elif is_procsub and len(self.parts):
                    direction = value[i]
                    j = _find_cmdsub_end(value, i + 2)
                    if j > len(value) or j > 0 and j <= len(value) and value[j - 1] != ")":
                        result.append(value[i])
                        i += 1
                        continue
                    inner = _substring(value, i + 2, j - 1)
                    try:
                        parser = NewParser(inner, False, False)
                        parsed = parser.parse_list(True)
                        if parsed is not None and parser.pos == len(inner) and ("\n" not in inner):
                            compact = _starts_with_subshell(parsed)
                            formatted = _format_cmdsub_node(parsed, 0, True, compact, True)
                        else:
                            formatted = inner
                    except Exception as _e:
                        formatted = inner
                    result.append(direction + "(" + formatted + ")")
                    i = j
                elif is_procsub:
                    direction = value[i]
                    j = _find_cmdsub_end(value, i + 2)
                    if j > len(value) or j > 0 and j <= len(value) and value[j - 1] != ")":
                        result.append(value[i])
                        i += 1
                        continue
                    inner = _substring(value, i + 2, j - 1)
                    if in_arith:
                        result.append(direction + "(" + inner + ")")
                    elif inner.strip(" \t\n\r"):
                        stripped = inner.lstrip(" \t")
                        result.append(direction + "(" + stripped + ")")
                    else:
                        result.append(direction + "(" + inner + ")")
                    i = j
                else:
                    result.append(value[i])
                    i += 1
            elif (_is_expansion_start(value, i, "${ ") or _is_expansion_start(value, i, "${\t") or _is_expansion_start(value, i, "${\n") or _is_expansion_start(value, i, "${|")) and not _is_backslash_escaped(value, i):
                prefix = _substring(value, i, i + 3).replace("\t", " ").replace("\n", " ")
                j = i + 3
                depth = 1
                while j < len(value) and depth > 0:
                    if value[j] == "{":
                        depth += 1
                    elif value[j] == "}":
                        depth -= 1
                    j += 1
                inner = _substring(value, i + 2, j - 1)
                if inner.strip(" \t\n\r") == "":
                    result.append("${ }")
                else:
                    try:
                        parser = NewParser(inner.lstrip(" \t\n|"), False, False)
                        parsed = parser.parse_list(True)
                        if parsed is not None:
                            formatted = _format_cmdsub_node(parsed, 0, False, False, False)
                            formatted = formatted.rstrip(";")
                            if inner.rstrip(" \t").endswith("\n"):
                                terminator = "\n }"
                            elif formatted.endswith(" &"):
                                terminator = " }"
                            else:
                                terminator = "; }"
                            result.append(prefix + formatted + terminator)
                        else:
                            result.append("${ }")
                    except Exception as _e:
                        result.append(_substring(value, i, j))
                i = j
            elif _is_expansion_start(value, i, "${") and not _is_backslash_escaped(value, i):
                j = i + 2
                depth = 1
                brace_quote = NewQuoteState()
                while j < len(value) and depth > 0:
                    c = value[j]
                    if c == "\\" and j + 1 < len(value) and not brace_quote.single:
                        j += 2
                        continue
                    if c == "'" and not brace_quote.double:
                        brace_quote.single = not brace_quote.single
                    elif c == "\"" and not brace_quote.single:
                        brace_quote.double = not brace_quote.double
                    elif not brace_quote.in_quotes():
                        if _is_expansion_start(value, j, "$(") and not _starts_with_at(value, j, "$(("):
                            j = _find_cmdsub_end(value, j + 2)
                            continue
                        if c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                    j += 1
                if depth > 0:
                    inner = _substring(value, i + 2, j)
                else:
                    inner = _substring(value, i + 2, j - 1)
                formatted_inner = self._format_command_substitutions(inner, False)
                formatted_inner = self._normalize_extglob_whitespace(formatted_inner)
                if depth == 0:
                    result.append("${" + formatted_inner + "}")
                else:
                    result.append("${" + formatted_inner)
                i = j
            elif value[i] == "\"":
                main_quote.double = not main_quote.double
                result.append(value[i])
                i += 1
            elif value[i] == "'" and not main_quote.double:
                j = i + 1
                while j < len(value) and value[j] != "'":
                    j += 1
                if j < len(value):
                    j += 1
                result.append(_substring(value, i, j))
                i = j
            else:
                result.append(value[i])
                i += 1
        return "".join(result)

    def _normalize_extglob_whitespace(self, value: str) -> str:
        result = []
        i = 0
        extglob_quote = NewQuoteState()
        deprecated_arith_depth = 0
        while i < len(value):
            if value[i] == "\"":
                extglob_quote.double = not extglob_quote.double
                result.append(value[i])
                i += 1
                continue
            if _starts_with_at(value, i, "$[") and not _is_backslash_escaped(value, i):
                deprecated_arith_depth += 1
                result.append(value[i])
                i += 1
                continue
            if value[i] == "]" and deprecated_arith_depth > 0:
                deprecated_arith_depth -= 1
                result.append(value[i])
                i += 1
                continue
            if i + 1 < len(value) and value[i + 1] == "(":
                prefix_char = value[i]
                if (prefix_char in "><") and not extglob_quote.double and deprecated_arith_depth == 0:
                    result.append(prefix_char)
                    result.append("(")
                    i += 2
                    depth = 1
                    pattern_parts = []
                    current_part = []
                    has_pipe = False
                    while i < len(value) and depth > 0:
                        if value[i] == "\\" and i + 1 < len(value):
                            current_part.append(value[i:i + 2])
                            i += 2
                            continue
                        elif value[i] == "(":
                            depth += 1
                            current_part.append(value[i])
                            i += 1
                        elif value[i] == ")":
                            depth -= 1
                            if depth == 0:
                                part_content = "".join(current_part)
                                if "<<" in part_content:
                                    pattern_parts.append(part_content)
                                elif has_pipe:
                                    pattern_parts.append(part_content.strip(" \t\n\r"))
                                else:
                                    pattern_parts.append(part_content)
                                break
                            current_part.append(value[i])
                            i += 1
                        elif value[i] == "|" and depth == 1:
                            if i + 1 < len(value) and value[i + 1] == "|":
                                current_part.append("||")
                                i += 2
                            else:
                                has_pipe = True
                                part_content = "".join(current_part)
                                if "<<" in part_content:
                                    pattern_parts.append(part_content)
                                else:
                                    pattern_parts.append(part_content.strip(" \t\n\r"))
                                current_part = []
                                i += 1
                        else:
                            current_part.append(value[i])
                            i += 1
                    result.append(" | ".join(pattern_parts))
                    if depth == 0:
                        result.append(")")
                        i += 1
                    continue
            result.append(value[i])
            i += 1
        return "".join(result)

    def get_cond_formatted_value(self) -> str:
        value = self._expand_all_ansi_c_quotes(self.value)
        value = self._strip_locale_string_dollars(value)
        value = self._format_command_substitutions(value, False)
        value = self._normalize_extglob_whitespace(value)
        value = value.replace("\u0001", "\u0001\u0001")
        return value.rstrip("\n")

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Command(Node):
    words: list[Word] = field(default_factory=list)
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        parts = []
        for w in (self.words or []):
            parts.append(w.to_sexp())
        for r in (self.redirects or []):
            parts.append(r.to_sexp())
        inner = " ".join(parts)
        if not inner:
            return "(command)"
        return "(command " + inner + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Pipeline(Node):
    commands: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        if len(self.commands) == 1:
            return self.commands[0].to_sexp()
        cmds = []
        i = 0
        while i < len(self.commands):
            cmd = self.commands[i]
            if isinstance(cmd, PipeBoth):
                cmd = cmd
                i += 1
                continue
            needs_redirect = i + 1 < len(self.commands) and self.commands[i + 1].kind == "pipe-both"
            cmds.append((cmd, needs_redirect))
            i += 1
        if len(cmds) == 1:
            pair = cmds[0]
            cmd = pair[0]
            needs = pair[1]
            return self._cmd_sexp(cmd, needs)
        last_pair = cmds[-1]
        last_cmd = last_pair[0]
        last_needs = last_pair[1]
        result = self._cmd_sexp(last_cmd, last_needs)
        j = len(cmds) - 2
        while j >= 0:
            pair = cmds[j]
            cmd = pair[0]
            needs = pair[1]
            if needs and cmd.kind != "command":
                result = "(pipe " + cmd.to_sexp() + " (redirect \">&\" 1) " + result + ")"
            else:
                result = "(pipe " + self._cmd_sexp(cmd, needs) + " " + result + ")"
            j -= 1
        return result

    def _cmd_sexp(self, cmd: Node, needs_redirect: bool) -> str:
        if not needs_redirect:
            return cmd.to_sexp()
        if isinstance(cmd, Command):
            cmd = cmd
            parts = []
            for w in (cmd.words or []):
                parts.append(w.to_sexp())
            for r in (cmd.redirects or []):
                parts.append(r.to_sexp())
            parts.append("(redirect \">&\" 1)")
            return "(command " + " ".join(parts) + ")"
        return cmd.to_sexp()

    def GetKind(self) -> str:
        return self.kind


@dataclass
class List(Node):
    parts: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        parts = self.parts.copy()
        op_names = {"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
        while len(parts) > 1 and parts[-1].kind == "operator" and (parts[-1].op == ";" or parts[-1].op == "\n"):
            parts = _sublist(parts, 0, len(parts) - 1)
        if len(parts) == 1:
            return parts[0].to_sexp()
        if parts[-1].kind == "operator" and parts[-1].op == "&":
            i: int = len(parts) - 3
            while i > 0:
                if parts[i].kind == "operator" and (parts[i].op == ";" or parts[i].op == "\n"):
                    left = _sublist(parts, 0, i)
                    right = _sublist(parts, i + 1, len(parts) - 1)
                    if len(left) > 1:
                        left_sexp = List(parts=left, kind="list").to_sexp()
                    else:
                        left_sexp = left[0].to_sexp()
                    if len(right) > 1:
                        right_sexp = List(parts=right, kind="list").to_sexp()
                    else:
                        right_sexp = right[0].to_sexp()
                    return "(semi " + left_sexp + " (background " + right_sexp + "))"
                i += -2
            inner_parts = _sublist(parts, 0, len(parts) - 1)
            if len(inner_parts) == 1:
                return "(background " + inner_parts[0].to_sexp() + ")"
            inner_list = List(parts=inner_parts, kind="list")
            return "(background " + inner_list.to_sexp() + ")"
        return self._to_sexp_with_precedence(parts, op_names)

    def _to_sexp_with_precedence(self, parts: list[Node], op_names: dict[str, str]) -> str:
        semi_positions = []
        for i in range(len(parts)):
            if parts[i].kind == "operator" and (parts[i].op == ";" or parts[i].op == "\n"):
                semi_positions.append(i)
        if semi_positions:
            segments = []
            start = 0
            for pos in semi_positions:
                seg = _sublist(parts, start, pos)
                if seg and seg[0].kind != "operator":
                    segments.append(seg)
                start = pos + 1
            seg = _sublist(parts, start, len(parts))
            if seg and seg[0].kind != "operator":
                segments.append(seg)
            if not segments:
                return "()"
            result = self._to_sexp_amp_and_higher(segments[0], op_names)
            i: int = 1
            while i < len(segments):
                result = "(semi " + result + " " + self._to_sexp_amp_and_higher(segments[i], op_names) + ")"
                i += 1
            return result
        return self._to_sexp_amp_and_higher(parts, op_names)

    def _to_sexp_amp_and_higher(self, parts: list[Node], op_names: dict[str, str]) -> str:
        if len(parts) == 1:
            return parts[0].to_sexp()
        amp_positions = []
        i: int = 1
        while i < len(parts) - 1:
            if parts[i].kind == "operator" and parts[i].op == "&":
                amp_positions.append(i)
            i += 2
        if amp_positions:
            segments = []
            start = 0
            for pos in amp_positions:
                segments.append(_sublist(parts, start, pos))
                start = pos + 1
            segments.append(_sublist(parts, start, len(parts)))
            result = self._to_sexp_and_or(segments[0], op_names)
            i: int = 1
            while i < len(segments):
                result = "(background " + result + " " + self._to_sexp_and_or(segments[i], op_names) + ")"
                i += 1
            return result
        return self._to_sexp_and_or(parts, op_names)

    def _to_sexp_and_or(self, parts: list[Node], op_names: dict[str, str]) -> str:
        if len(parts) == 1:
            return parts[0].to_sexp()
        result = parts[0].to_sexp()
        i: int = 1
        while i < len(parts) - 1:
            op = parts[i]
            cmd = parts[i + 1]
            op_name = op_names.get(op.op, op.op)
            result = "(" + op_name + " " + result + " " + cmd.to_sexp() + ")"
            i += 2
        return result

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Operator(Node):
    op: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        names = {"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}
        return "(" + names.get(self.op, self.op) + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class PipeBoth(Node):
    kind: str = ""

    def to_sexp(self) -> str:
        return "(pipe-both)"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Empty(Node):
    kind: str = ""

    def to_sexp(self) -> str:
        return ""

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Comment(Node):
    text: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        return ""

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Redirect(Node):
    op: str = ""
    target: Word = None
    fd: int = 0
    kind: str = ""

    def to_sexp(self) -> str:
        op = self.op.lstrip("0123456789")
        if op.startswith("{"):
            j = 1
            if j < len(op) and (op[j].isalpha() or op[j] == "_"):
                j += 1
                while j < len(op) and (op[j].isalnum() or op[j] == "_"):
                    j += 1
                if j < len(op) and op[j] == "[":
                    j += 1
                    while j < len(op) and op[j] != "]":
                        j += 1
                    if j < len(op) and op[j] == "]":
                        j += 1
                if j < len(op) and op[j] == "}":
                    op = _substring(op, j + 1, len(op))
        target_val = self.target.value
        target_val = self.target._expand_all_ansi_c_quotes(target_val)
        target_val = self.target._strip_locale_string_dollars(target_val)
        target_val = self.target._format_command_substitutions(target_val, False)
        target_val = self.target._strip_arith_line_continuations(target_val)
        if target_val.endswith("\\") and not target_val.endswith("\\\\"):
            target_val = target_val + "\\"
        if target_val.startswith("&"):
            if op == ">":
                op = ">&"
            elif op == "<":
                op = "<&"
            raw = _substring(target_val, 1, len(target_val))
            if raw.isdigit() and int(raw, 10) <= 2147483647:
                return "(redirect \"" + op + "\" " + str(int(raw, 10)) + ")"
            if raw.endswith("-") and raw[:-1].isdigit() and int(raw[:-1], 10) <= 2147483647:
                return "(redirect \"" + op + "\" " + str(int(raw[:-1], 10)) + ")"
            if target_val == "&-":
                return "(redirect \">&-\" 0)"
            fd_target = raw[:-1] if raw.endswith("-") else raw
            return "(redirect \"" + op + "\" \"" + fd_target + "\")"
        if op == ">&" or op == "<&":
            if target_val.isdigit() and int(target_val, 10) <= 2147483647:
                return "(redirect \"" + op + "\" " + str(int(target_val, 10)) + ")"
            if target_val == "-":
                return "(redirect \">&-\" 0)"
            if target_val.endswith("-") and target_val[:-1].isdigit() and int(target_val[:-1], 10) <= 2147483647:
                return "(redirect \"" + op + "\" " + str(int(target_val[:-1], 10)) + ")"
            out_val = target_val[:-1] if target_val.endswith("-") else target_val
            return "(redirect \"" + op + "\" \"" + out_val + "\")"
        return "(redirect \"" + op + "\" \"" + target_val + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class HereDoc(Node):
    delimiter: str = ""
    content: str = ""
    strip_tabs: bool = False
    quoted: bool = False
    fd: int = 0
    complete: bool = False
    _start_pos: int = 0
    kind: str = ""

    def to_sexp(self) -> str:
        op = "<<-" if self.strip_tabs else "<<"
        content = self.content
        if content.endswith("\\") and not content.endswith("\\\\"):
            content = content + "\\"
        return f"(redirect \"{op}\" \"{content}\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Subshell(Node):
    body: Node = None
    redirects: list[Node] | None = None
    kind: str = ""

    def to_sexp(self) -> str:
        base = "(subshell " + self.body.to_sexp() + ")"
        return _append_redirects(base, self.redirects)

    def GetKind(self) -> str:
        return self.kind


@dataclass
class BraceGroup(Node):
    body: Node = None
    redirects: list[Node] | None = None
    kind: str = ""

    def to_sexp(self) -> str:
        base = "(brace-group " + self.body.to_sexp() + ")"
        return _append_redirects(base, self.redirects)

    def GetKind(self) -> str:
        return self.kind


@dataclass
class If(Node):
    condition: Node = None
    then_body: Node = None
    else_body: Node | None = None
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        result = "(if " + self.condition.to_sexp() + " " + self.then_body.to_sexp()
        if self.else_body is not None:
            result = result + " " + self.else_body.to_sexp()
        result = result + ")"
        for r in (self.redirects or []):
            result = result + " " + r.to_sexp()
        return result

    def GetKind(self) -> str:
        return self.kind


@dataclass
class While(Node):
    condition: Node = None
    body: Node = None
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        base = "(while " + self.condition.to_sexp() + " " + self.body.to_sexp() + ")"
        return _append_redirects(base, self.redirects)

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Until(Node):
    condition: Node = None
    body: Node = None
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        base = "(until " + self.condition.to_sexp() + " " + self.body.to_sexp() + ")"
        return _append_redirects(base, self.redirects)

    def GetKind(self) -> str:
        return self.kind


@dataclass
class For(Node):
    var: str = ""
    words: list[Word] | None = None
    body: Node = None
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        suffix = ""
        if self.redirects:
            redirect_parts = []
            for r in (self.redirects or []):
                redirect_parts.append(r.to_sexp())
            suffix = " " + " ".join(redirect_parts)
        temp_word = Word(value=self.var, parts=[], kind="word")
        var_formatted = temp_word._format_command_substitutions(self.var, False)
        var_escaped = var_formatted.replace("\\", "\\\\").replace("\"", "\\\"")
        if self.words is None:
            return "(for (word \"" + var_escaped + "\") (in (word \"\\\"$@\\\"\")) " + self.body.to_sexp() + ")" + suffix
        elif len(self.words) == 0:
            return "(for (word \"" + var_escaped + "\") (in) " + self.body.to_sexp() + ")" + suffix
        else:
            word_parts = []
            for w in (self.words or []):
                word_parts.append(w.to_sexp())
            word_strs = " ".join(word_parts)
            return "(for (word \"" + var_escaped + "\") (in " + word_strs + ") " + self.body.to_sexp() + ")" + suffix

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ForArith(Node):
    init: str = ""
    cond: str = ""
    incr: str = ""
    body: Node = None
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        suffix = ""
        if self.redirects:
            redirect_parts = []
            for r in (self.redirects or []):
                redirect_parts.append(r.to_sexp())
            suffix = " " + " ".join(redirect_parts)
        init_val = self.init if self.init else "1"
        cond_val = self.cond if self.cond else "1"
        incr_val = self.incr if self.incr else "1"
        init_str = _format_arith_val(init_val)
        cond_str = _format_arith_val(cond_val)
        incr_str = _format_arith_val(incr_val)
        body_str = self.body.to_sexp()
        return f"(arith-for (init (word \"{init_str}\")) (test (word \"{cond_str}\")) (step (word \"{incr_str}\")) {body_str}){suffix}"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Select(Node):
    var: str = ""
    words: list[Word] | None = None
    body: Node = None
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        suffix = ""
        if self.redirects:
            redirect_parts = []
            for r in (self.redirects or []):
                redirect_parts.append(r.to_sexp())
            suffix = " " + " ".join(redirect_parts)
        var_escaped = self.var.replace("\\", "\\\\").replace("\"", "\\\"")
        if self.words is not None:
            word_parts = []
            for w in (self.words or []):
                word_parts.append(w.to_sexp())
            word_strs = " ".join(word_parts)
            if self.words:
                in_clause = "(in " + word_strs + ")"
            else:
                in_clause = "(in)"
        else:
            in_clause = "(in (word \"\\\"$@\\\"\"))"
        return "(select (word \"" + var_escaped + "\") " + in_clause + " " + self.body.to_sexp() + ")" + suffix

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Case(Node):
    word: Word = None
    patterns: list[CasePattern] = field(default_factory=list)
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        parts = []
        parts.append("(case " + self.word.to_sexp())
        for p in (self.patterns or []):
            parts.append(p.to_sexp())
        base = " ".join(parts) + ")"
        return _append_redirects(base, self.redirects)

    def GetKind(self) -> str:
        return self.kind


@dataclass
class CasePattern(Node):
    pattern: str = ""
    body: Node | None = None
    terminator: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        alternatives = []
        current = []
        i = 0
        depth = 0
        while i < len(self.pattern):
            ch = self.pattern[i]
            if ch == "\\" and i + 1 < len(self.pattern):
                current.append(_substring(self.pattern, i, i + 2))
                i += 2
            elif (ch == "@" or ch == "?" or ch == "*" or ch == "+" or ch == "!") and i + 1 < len(self.pattern) and self.pattern[i + 1] == "(":
                current.append(ch)
                current.append("(")
                depth += 1
                i += 2
            elif _is_expansion_start(self.pattern, i, "$("):
                current.append(ch)
                current.append("(")
                depth += 1
                i += 2
            elif ch == "(" and depth > 0:
                current.append(ch)
                depth += 1
                i += 1
            elif ch == ")" and depth > 0:
                current.append(ch)
                depth -= 1
                i += 1
            elif ch == "[":
                result0, result1, result2 = _consume_bracket_class(self.pattern, i, depth)
                i = result0
                current.extend(result1)
            elif ch == "'" and depth == 0:
                result0, result1 = _consume_single_quote(self.pattern, i)
                i = result0
                current.extend(result1)
            elif ch == "\"" and depth == 0:
                result0, result1 = _consume_double_quote(self.pattern, i)
                i = result0
                current.extend(result1)
            elif ch == "|" and depth == 0:
                alternatives.append("".join(current))
                current = []
                i += 1
            else:
                current.append(ch)
                i += 1
        alternatives.append("".join(current))
        word_list = []
        for alt in alternatives:
            word_list.append(Word(value=alt, kind="word").to_sexp())
        pattern_str = " ".join(word_list)
        parts = ["(pattern (" + pattern_str + ")"]
        if self.body is not None:
            parts.append(" " + self.body.to_sexp())
        else:
            parts.append(" ()")
        parts.append(")")
        return "".join(parts)

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Function(Node):
    name: str = ""
    body: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(function \"" + self.name + "\" " + self.body.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ParamExpansion(Node):
    param: str = ""
    op: str = ""
    arg: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        escaped_param = self.param.replace("\\", "\\\\").replace("\"", "\\\"")
        if self.op != "":
            escaped_op = self.op.replace("\\", "\\\\").replace("\"", "\\\"")
            if self.arg != "":
                arg_val = self.arg
            else:
                arg_val = ""
            escaped_arg = arg_val.replace("\\", "\\\\").replace("\"", "\\\"")
            return "(param \"" + escaped_param + "\" \"" + escaped_op + "\" \"" + escaped_arg + "\")"
        return "(param \"" + escaped_param + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ParamLength(Node):
    param: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace("\"", "\\\"")
        return "(param-len \"" + escaped + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ParamIndirect(Node):
    param: str = ""
    op: str = ""
    arg: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace("\"", "\\\"")
        if self.op != "":
            escaped_op = self.op.replace("\\", "\\\\").replace("\"", "\\\"")
            if self.arg != "":
                arg_val = self.arg
            else:
                arg_val = ""
            escaped_arg = arg_val.replace("\\", "\\\\").replace("\"", "\\\"")
            return "(param-indirect \"" + escaped + "\" \"" + escaped_op + "\" \"" + escaped_arg + "\")"
        return "(param-indirect \"" + escaped + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class CommandSubstitution(Node):
    command: Node = None
    brace: bool = False
    kind: str = ""

    def to_sexp(self) -> str:
        if self.brace:
            return "(funsub " + self.command.to_sexp() + ")"
        return "(cmdsub " + self.command.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithmeticExpansion(Node):
    expression: Node | None = None
    kind: str = ""

    def to_sexp(self) -> str:
        if self.expression is None:
            return "(arith)"
        return "(arith " + self.expression.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithmeticCommand(Node):
    expression: Node | None = None
    redirects: list[Node] = field(default_factory=list)
    raw_content: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        formatted = Word(value=self.raw_content, kind="word")._format_command_substitutions(self.raw_content, True)
        escaped = formatted.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\t", "\\t")
        result = "(arith (word \"" + escaped + "\"))"
        if self.redirects:
            redirect_parts = []
            for r in (self.redirects or []):
                redirect_parts.append(r.to_sexp())
            redirect_sexps = " ".join(redirect_parts)
            return result + " " + redirect_sexps
        return result

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithNumber(Node):
    value: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        return "(number \"" + self.value + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithEmpty(Node):
    kind: str = ""

    def to_sexp(self) -> str:
        return "(empty)"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithVar(Node):
    name: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        return "(var \"" + self.name + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithBinaryOp(Node):
    op: str = ""
    left: Node = None
    right: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(binary-op \"" + self.op + "\" " + self.left.to_sexp() + " " + self.right.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithUnaryOp(Node):
    op: str = ""
    operand: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(unary-op \"" + self.op + "\" " + self.operand.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithPreIncr(Node):
    operand: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(pre-incr " + self.operand.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithPostIncr(Node):
    operand: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(post-incr " + self.operand.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithPreDecr(Node):
    operand: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(pre-decr " + self.operand.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithPostDecr(Node):
    operand: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(post-decr " + self.operand.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithAssign(Node):
    op: str = ""
    target: Node = None
    value: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(assign \"" + self.op + "\" " + self.target.to_sexp() + " " + self.value.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithTernary(Node):
    condition: Node = None
    if_true: Node = None
    if_false: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(ternary " + self.condition.to_sexp() + " " + self.if_true.to_sexp() + " " + self.if_false.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithComma(Node):
    left: Node = None
    right: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(comma " + self.left.to_sexp() + " " + self.right.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithSubscript(Node):
    array: str = ""
    index: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(subscript \"" + self.array + "\" " + self.index.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithEscape(Node):
    char: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        return "(escape \"" + self.char + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithDeprecated(Node):
    expression: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        escaped = self.expression.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
        return "(arith-deprecated \"" + escaped + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ArithConcat(Node):
    parts: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        sexps = []
        for p in (self.parts or []):
            sexps.append(p.to_sexp())
        return "(arith-concat " + " ".join(sexps) + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class AnsiCQuote(Node):
    content: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
        return "(ansi-c \"" + escaped + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class LocaleString(Node):
    content: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
        return "(locale \"" + escaped + "\")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ProcessSubstitution(Node):
    direction: str = ""
    command: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(procsub \"" + self.direction + "\" " + self.command.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Negation(Node):
    pipeline: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        if self.pipeline is None:
            return "(negation (command))"
        return "(negation " + self.pipeline.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Time(Node):
    pipeline: Node = None
    posix: bool = False
    kind: str = ""

    def to_sexp(self) -> str:
        if self.pipeline is None:
            if self.posix:
                return "(time -p (command))"
            else:
                return "(time (command))"
        if self.posix:
            return "(time -p " + self.pipeline.to_sexp() + ")"
        return "(time " + self.pipeline.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class ConditionalExpr(Node):
    body: any = None
    redirects: list[Node] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        body = self.body
        if isinstance(body, str):
            body = body
            escaped = body.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
            result = "(cond \"" + escaped + "\")"
        else:
            result = "(cond " + body.to_sexp() + ")"
        if self.redirects:
            redirect_parts = []
            for r in (self.redirects or []):
                redirect_parts.append(r.to_sexp())
            redirect_sexps = " ".join(redirect_parts)
            return result + " " + redirect_sexps
        return result

    def GetKind(self) -> str:
        return self.kind


@dataclass
class UnaryTest(Node):
    op: str = ""
    operand: Word = None
    kind: str = ""

    def to_sexp(self) -> str:
        operand_val = self.operand.get_cond_formatted_value()
        return "(cond-unary \"" + self.op + "\" (cond-term \"" + operand_val + "\"))"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class BinaryTest(Node):
    op: str = ""
    left: Word = None
    right: Word = None
    kind: str = ""

    def to_sexp(self) -> str:
        left_val = self.left.get_cond_formatted_value()
        right_val = self.right.get_cond_formatted_value()
        return "(cond-binary \"" + self.op + "\" (cond-term \"" + left_val + "\") (cond-term \"" + right_val + "\"))"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class CondAnd(Node):
    left: Node = None
    right: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(cond-and " + self.left.to_sexp() + " " + self.right.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class CondOr(Node):
    left: Node = None
    right: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(cond-or " + self.left.to_sexp() + " " + self.right.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class CondNot(Node):
    operand: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return self.operand.to_sexp()

    def GetKind(self) -> str:
        return self.kind


@dataclass
class CondParen(Node):
    inner: Node = None
    kind: str = ""

    def to_sexp(self) -> str:
        return "(cond-expr " + self.inner.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Array(Node):
    elements: list[Word] = field(default_factory=list)
    kind: str = ""

    def to_sexp(self) -> str:
        if not self.elements:
            return "(array)"
        parts = []
        for e in (self.elements or []):
            parts.append(e.to_sexp())
        inner = " ".join(parts)
        return "(array " + inner + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Coproc(Node):
    command: Node = None
    name: str = ""
    kind: str = ""

    def to_sexp(self) -> str:
        if self.name:
            name = self.name
        else:
            name = "COPROC"
        return "(coproc \"" + name + "\" " + self.command.to_sexp() + ")"

    def GetKind(self) -> str:
        return self.kind


@dataclass
class Parser:
    source: str = ""
    pos: int = 0
    length: int = 0
    _pending_heredocs: list[HereDoc] = field(default_factory=list)
    _cmdsub_heredoc_end: int = 0
    _saw_newline_in_single_quote: bool = False
    _in_process_sub: bool = False
    _extglob: bool = False
    _ctx: ContextStack = None
    _lexer: Lexer = None
    _token_history: list[Token | None] = field(default_factory=list)
    _parser_state: int = 0
    _dolbrace_state: int = 0
    _eof_token: str = ""
    _word_context: int = 0
    _at_command_start: bool = False
    _in_array_literal: bool = False
    _in_assign_builtin: bool = False
    _arith_src: str = ""
    _arith_pos: int = 0
    _arith_len: int = 0

    def _set_state(self, flag: int) -> None:
        self._parser_state = self._parser_state | flag

    def _clear_state(self, flag: int) -> None:
        self._parser_state = self._parser_state & ~flag

    def _in_state(self, flag: int) -> bool:
        return (self._parser_state & flag) != 0

    def _save_parser_state(self) -> SavedParserState:
        return SavedParserState(parser_state=self._parser_state, dolbrace_state=self._dolbrace_state, pending_heredocs=self._pending_heredocs, ctx_stack=self._ctx.copy_stack(), eof_token=self._eof_token)

    def _restore_parser_state(self, saved: SavedParserState) -> None:
        self._parser_state = saved.parser_state
        self._dolbrace_state = saved.dolbrace_state
        self._eof_token = saved.eof_token
        self._ctx.restore_from(saved.ctx_stack)

    def _record_token(self, tok: Token) -> None:
        self._token_history = [tok, self._token_history[0], self._token_history[1], self._token_history[2]]

    def _update_dolbrace_for_op(self, op: str, has_param: bool) -> None:
        if self._dolbrace_state == DolbraceState_NONE:
            return
        if op == "" or len(op) == 0:
            return
        first_char = op[0]
        if self._dolbrace_state == DolbraceState_PARAM and has_param:
            if first_char in "%#^,":
                self._dolbrace_state = DolbraceState_QUOTE
                return
            if first_char == "/":
                self._dolbrace_state = DolbraceState_QUOTE2
                return
        if self._dolbrace_state == DolbraceState_PARAM:
            if first_char in "#%^,~:-=?+/":
                self._dolbrace_state = DolbraceState_OP

    def _sync_lexer(self) -> None:
        if self._lexer._token_cache is not None:
            if self._lexer._token_cache.pos != self.pos or self._lexer._cached_word_context != self._word_context or self._lexer._cached_at_command_start != self._at_command_start or self._lexer._cached_in_array_literal != self._in_array_literal or self._lexer._cached_in_assign_builtin != self._in_assign_builtin:
                self._lexer._token_cache = None
        if self._lexer.pos != self.pos:
            self._lexer.pos = self.pos
        self._lexer._eof_token = self._eof_token
        self._lexer._parser_state = self._parser_state
        self._lexer._last_read_token = self._token_history[0]
        self._lexer._word_context = self._word_context
        self._lexer._at_command_start = self._at_command_start
        self._lexer._in_array_literal = self._in_array_literal
        self._lexer._in_assign_builtin = self._in_assign_builtin

    def _sync_parser(self) -> None:
        self.pos = self._lexer.pos

    def _lex_peek_token(self) -> Token:
        if self._lexer._token_cache is not None and self._lexer._token_cache.pos == self.pos and self._lexer._cached_word_context == self._word_context and self._lexer._cached_at_command_start == self._at_command_start and self._lexer._cached_in_array_literal == self._in_array_literal and self._lexer._cached_in_assign_builtin == self._in_assign_builtin:
            return self._lexer._token_cache
        saved_pos = self.pos
        self._sync_lexer()
        result = self._lexer.peek_token()
        self._lexer._cached_word_context = self._word_context
        self._lexer._cached_at_command_start = self._at_command_start
        self._lexer._cached_in_array_literal = self._in_array_literal
        self._lexer._cached_in_assign_builtin = self._in_assign_builtin
        self._lexer._post_read_pos = self._lexer.pos
        self.pos = saved_pos
        return result

    def _lex_next_token(self) -> Token:
        if self._lexer._token_cache is not None and self._lexer._token_cache.pos == self.pos and self._lexer._cached_word_context == self._word_context and self._lexer._cached_at_command_start == self._at_command_start and self._lexer._cached_in_array_literal == self._in_array_literal and self._lexer._cached_in_assign_builtin == self._in_assign_builtin:
            tok = self._lexer.next_token()
            self.pos = self._lexer._post_read_pos
            self._lexer.pos = self._lexer._post_read_pos
        else:
            self._sync_lexer()
            tok = self._lexer.next_token()
            self._lexer._cached_word_context = self._word_context
            self._lexer._cached_at_command_start = self._at_command_start
            self._lexer._cached_in_array_literal = self._in_array_literal
            self._lexer._cached_in_assign_builtin = self._in_assign_builtin
            self._sync_parser()
        self._record_token(tok)
        return tok

    def _lex_skip_blanks(self) -> None:
        self._sync_lexer()
        self._lexer.skip_blanks()
        self._sync_parser()

    def _lex_skip_comment(self) -> bool:
        self._sync_lexer()
        result = self._lexer._skip_comment()
        self._sync_parser()
        return result

    def _lex_is_command_terminator(self) -> bool:
        tok = self._lex_peek_token()
        t = tok.type
        return t == TokenType_EOF or t == TokenType_NEWLINE or t == TokenType_PIPE or t == TokenType_SEMI or t == TokenType_LPAREN or t == TokenType_RPAREN or t == TokenType_AMP

    def _lex_peek_operator(self) -> tuple[int, str]:
        tok = self._lex_peek_token()
        t = tok.type
        if t >= TokenType_SEMI and t <= TokenType_GREATER or t >= TokenType_AND_AND and t <= TokenType_PIPE_AMP:
            return (t, tok.value)
        return (0, "")

    def _lex_peek_reserved_word(self) -> str:
        tok = self._lex_peek_token()
        if tok.type != TokenType_WORD:
            return ""
        word = tok.value
        if word.endswith("\\\n"):
            word = word[:-2]
        if (word in RESERVED_WORDS) or word == "{" or word == "}" or word == "[[" or word == "]]" or word == "!" or word == "time":
            return word
        return ""

    def _lex_is_at_reserved_word(self, word: str) -> bool:
        reserved = self._lex_peek_reserved_word()
        return reserved == word

    def _lex_consume_word(self, expected: str) -> bool:
        tok = self._lex_peek_token()
        if tok.type != TokenType_WORD:
            return False
        word = tok.value
        if word.endswith("\\\n"):
            word = word[:-2]
        if word == expected:
            self._lex_next_token()
            return True
        return False

    def _lex_peek_case_terminator(self) -> str:
        tok = self._lex_peek_token()
        t = tok.type
        if t == TokenType_SEMI_SEMI:
            return ";;"
        if t == TokenType_SEMI_AMP:
            return ";&"
        if t == TokenType_SEMI_SEMI_AMP:
            return ";;&"
        return ""

    def at_end(self) -> bool:
        return self.pos >= self.length

    def peek(self) -> str:
        if self.at_end():
            return ""
        return self.source[self.pos]

    def advance(self) -> str:
        if self.at_end():
            return ""
        ch = self.source[self.pos]
        self.pos += 1
        return ch

    def peek_at(self, offset: int) -> str:
        pos = self.pos + offset
        if pos < 0 or pos >= self.length:
            return ""
        return self.source[pos]

    def lookahead(self, n: int) -> str:
        return _substring(self.source, self.pos, self.pos + n)

    def _is_bang_followed_by_procsub(self) -> bool:
        if self.pos + 2 >= self.length:
            return False
        next_char = self.source[self.pos + 1]
        if next_char != ">" and next_char != "<":
            return False
        return self.source[self.pos + 2] == "("

    def skip_whitespace(self) -> None:
        while not self.at_end():
            self._lex_skip_blanks()
            if self.at_end():
                break
            ch = self.peek()
            if ch == "#":
                self._lex_skip_comment()
            elif ch == "\\" and self.peek_at(1) == "\n":
                self.advance()
                self.advance()
            else:
                break

    def skip_whitespace_and_newlines(self) -> None:
        while not self.at_end():
            ch = self.peek()
            if _is_whitespace(ch):
                self.advance()
                if ch == "\n":
                    self._gather_heredoc_bodies()
                    if self._cmdsub_heredoc_end != -1 and self._cmdsub_heredoc_end > self.pos:
                        self.pos = self._cmdsub_heredoc_end
                        self._cmdsub_heredoc_end = -1
            elif ch == "#":
                while not self.at_end() and self.peek() != "\n":
                    self.advance()
            elif ch == "\\" and self.peek_at(1) == "\n":
                self.advance()
                self.advance()
            else:
                break

    def _at_list_terminating_bracket(self) -> bool:
        if self.at_end():
            return False
        ch = self.peek()
        if self._eof_token != "" and ch == self._eof_token:
            return True
        if ch == ")":
            return True
        if ch == "}":
            next_pos = self.pos + 1
            if next_pos >= self.length:
                return True
            return _is_word_end_context(self.source[next_pos])
        return False

    def _at_eof_token(self) -> bool:
        if self._eof_token == "":
            return False
        tok = self._lex_peek_token()
        if self._eof_token == ")":
            return tok.type == TokenType_RPAREN
        if self._eof_token == "}":
            return tok.type == TokenType_WORD and tok.value == "}"
        return False

    def _collect_redirects(self) -> list[Node]:
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)
        return redirects if redirects else None

    def _parse_loop_body(self, context: str) -> Node:
        if self.peek() == "{":
            brace = self.parse_brace_group()
            if brace is None:
                raise ParseError(f"Expected brace group body in {context}", self._lex_peek_token().pos)
            return brace.body
        if self._lex_consume_word("do"):
            body = self.parse_list_until({"done"})
            if body is None:
                raise ParseError("Expected commands after 'do'", self._lex_peek_token().pos)
            self.skip_whitespace_and_newlines()
            if not self._lex_consume_word("done"):
                raise ParseError(f"Expected 'done' to close {context}", self._lex_peek_token().pos)
            return body
        raise ParseError(f"Expected 'do' or '{{' in {context}", self._lex_peek_token().pos)

    def peek_word(self) -> str:
        saved_pos = self.pos
        self.skip_whitespace()
        if self.at_end() or _is_metachar(self.peek()):
            self.pos = saved_pos
            return ""
        chars = []
        while not self.at_end() and not _is_metachar(self.peek()):
            ch = self.peek()
            if _is_quote(ch):
                break
            if ch == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                break
            if ch == "\\" and self.pos + 1 < self.length:
                chars.append(self.advance())
                chars.append(self.advance())
                continue
            chars.append(self.advance())
        if chars:
            word = "".join(chars)
        else:
            word = ""
        self.pos = saved_pos
        return word

    def consume_word(self, expected: str) -> bool:
        saved_pos = self.pos
        self.skip_whitespace()
        word = self.peek_word()
        keyword_word = word
        has_leading_brace = False
        if word != "" and self._in_process_sub and len(word) > 1 and word[0] == "}":
            keyword_word = word[1:]
            has_leading_brace = True
        if keyword_word != expected:
            self.pos = saved_pos
            return False
        self.skip_whitespace()
        if has_leading_brace:
            self.advance()
        for _ in expected:
            self.advance()
        while self.peek() == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
            self.advance()
            self.advance()
        return True

    def _is_word_terminator(self, ctx: int, ch: str, bracket_depth: int, paren_depth: int) -> bool:
        self._sync_lexer()
        return self._lexer._is_word_terminator(ctx, ch, bracket_depth, paren_depth)

    def _scan_double_quote(self, chars: list[str], parts: list[Node], start: int, handle_line_continuation: bool) -> None:
        chars.append("\"")
        while not self.at_end() and self.peek() != "\"":
            c = self.peek()
            if c == "\\" and self.pos + 1 < self.length:
                next_c = self.source[self.pos + 1]
                if handle_line_continuation and next_c == "\n":
                    self.advance()
                    self.advance()
                else:
                    chars.append(self.advance())
                    chars.append(self.advance())
            elif c == "$":
                if not self._parse_dollar_expansion(chars, parts, True):
                    chars.append(self.advance())
            else:
                chars.append(self.advance())
        if self.at_end():
            raise ParseError("Unterminated double quote", start)
        chars.append(self.advance())

    def _parse_dollar_expansion(self, chars: list[str], parts: list[Node], in_dquote: bool) -> bool:
        if self.pos + 2 < self.length and self.source[self.pos + 1] == "(" and self.source[self.pos + 2] == "(":
            result0, result1 = self._parse_arithmetic_expansion()
            if result0 is not None:
                parts.append(result0)
                chars.append(result1)
                return True
            result0, result1 = self._parse_command_substitution()
            if result0 is not None:
                parts.append(result0)
                chars.append(result1)
                return True
            return False
        if self.pos + 1 < self.length and self.source[self.pos + 1] == "[":
            result0, result1 = self._parse_deprecated_arithmetic()
            if result0 is not None:
                parts.append(result0)
                chars.append(result1)
                return True
            return False
        if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            result0, result1 = self._parse_command_substitution()
            if result0 is not None:
                parts.append(result0)
                chars.append(result1)
                return True
            return False
        result0, result1 = self._parse_param_expansion(in_dquote)
        if result0 is not None:
            parts.append(result0)
            chars.append(result1)
            return True
        return False

    def _parse_word_internal(self, ctx: int, at_command_start: bool, in_array_literal: bool) -> Word:
        self._word_context = ctx
        return self.parse_word(at_command_start, in_array_literal, False)

    def parse_word(self, at_command_start: bool, in_array_literal: bool, in_assign_builtin: bool) -> Word:
        self.skip_whitespace()
        if self.at_end():
            return None
        self._at_command_start = at_command_start
        self._in_array_literal = in_array_literal
        self._in_assign_builtin = in_assign_builtin
        tok = self._lex_peek_token()
        if tok.type != TokenType_WORD:
            self._at_command_start = False
            self._in_array_literal = False
            self._in_assign_builtin = False
            return None
        self._lex_next_token()
        self._at_command_start = False
        self._in_array_literal = False
        self._in_assign_builtin = False
        return tok.word

    def _parse_command_substitution(self) -> tuple[Node | None, str]:
        if self.at_end() or self.peek() != "$":
            return (None, "")
        start = self.pos
        self.advance()
        if self.at_end() or self.peek() != "(":
            self.pos = start
            return (None, "")
        self.advance()
        saved = self._save_parser_state()
        self._set_state(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)
        self._eof_token = ")"
        cmd = self.parse_list(True)
        if cmd is None:
            cmd = Empty(kind="empty")
        self.skip_whitespace_and_newlines()
        if self.at_end() or self.peek() != ")":
            self._restore_parser_state(saved)
            self.pos = start
            return (None, "")
        self.advance()
        text_end = self.pos
        text = _substring(self.source, start, text_end)
        self._restore_parser_state(saved)
        return (CommandSubstitution(command=cmd, kind="cmdsub"), text)

    def _parse_funsub(self, start: int) -> tuple[Node | None, str]:
        self._sync_parser()
        if not self.at_end() and self.peek() == "|":
            self.advance()
        saved = self._save_parser_state()
        self._set_state(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)
        self._eof_token = "}"
        cmd = self.parse_list(True)
        if cmd is None:
            cmd = Empty(kind="empty")
        self.skip_whitespace_and_newlines()
        if self.at_end() or self.peek() != "}":
            self._restore_parser_state(saved)
            raise MatchedPairError("unexpected EOF looking for `}'", start)
        self.advance()
        text = _substring(self.source, start, self.pos)
        self._restore_parser_state(saved)
        self._sync_lexer()
        return (CommandSubstitution(command=cmd, brace=True, kind="cmdsub"), text)

    def _is_assignment_word(self, word: Node) -> bool:
        return _assignment(word.value, 0) != -1

    def _parse_backtick_substitution(self) -> tuple[Node | None, str]:
        if self.at_end() or self.peek() != "`":
            return (None, "")
        start = self.pos
        self.advance()
        content_chars: list[str] = []
        text_chars = ["`"]
        pending_heredocs: list[tuple[str, bool]] = []
        in_heredoc_body = False
        current_heredoc_delim = ""
        current_heredoc_strip = False
        while not self.at_end() and (in_heredoc_body or self.peek() != "`"):
            if in_heredoc_body:
                line_start = self.pos
                line_end = line_start
                while line_end < self.length and self.source[line_end] != "\n":
                    line_end += 1
                line = _substring(self.source, line_start, line_end)
                check_line = line.lstrip("\t") if current_heredoc_strip else line
                if check_line == current_heredoc_delim:
                    for ch in line:
                        content_chars.append(ch)
                        text_chars.append(ch)
                    self.pos = line_end
                    if self.pos < self.length and self.source[self.pos] == "\n":
                        content_chars.append("\n")
                        text_chars.append("\n")
                        self.advance()
                    in_heredoc_body = False
                    if len(pending_heredocs) > 0:
                        current_heredoc_delim, current_heredoc_strip = pending_heredocs.pop(0)
                        in_heredoc_body = True
                elif check_line.startswith(current_heredoc_delim) and len(check_line) > len(current_heredoc_delim):
                    tabs_stripped = len(line) - len(check_line)
                    end_pos = tabs_stripped + len(current_heredoc_delim)
                    i: int = 0
                    while i < end_pos:
                        content_chars.append(line[i])
                        text_chars.append(line[i])
                        i += 1
                    self.pos = line_start + end_pos
                    in_heredoc_body = False
                    if len(pending_heredocs) > 0:
                        current_heredoc_delim, current_heredoc_strip = pending_heredocs.pop(0)
                        in_heredoc_body = True
                else:
                    for ch in line:
                        content_chars.append(ch)
                        text_chars.append(ch)
                    self.pos = line_end
                    if self.pos < self.length and self.source[self.pos] == "\n":
                        content_chars.append("\n")
                        text_chars.append("\n")
                        self.advance()
                continue
            c = self.peek()
            if c == "\\" and self.pos + 1 < self.length:
                next_c = self.source[self.pos + 1]
                if next_c == "\n":
                    self.advance()
                    self.advance()
                elif _is_escape_char_in_backtick(next_c):
                    self.advance()
                    escaped = self.advance()
                    content_chars.append(escaped)
                    text_chars.append("\\")
                    text_chars.append(escaped)
                else:
                    ch = self.advance()
                    content_chars.append(ch)
                    text_chars.append(ch)
                continue
            if c == "<" and self.pos + 1 < self.length and self.source[self.pos + 1] == "<":
                if self.pos + 2 < self.length and self.source[self.pos + 2] == "<":
                    content_chars.append(self.advance())
                    text_chars.append("<")
                    content_chars.append(self.advance())
                    text_chars.append("<")
                    content_chars.append(self.advance())
                    text_chars.append("<")
                    while not self.at_end() and _is_whitespace_no_newline(self.peek()):
                        ch = self.advance()
                        content_chars.append(ch)
                        text_chars.append(ch)
                    while not self.at_end() and not _is_whitespace(self.peek()) and (self.peek() not in "()"):
                        if self.peek() == "\\" and self.pos + 1 < self.length:
                            ch = self.advance()
                            content_chars.append(ch)
                            text_chars.append(ch)
                            ch = self.advance()
                            content_chars.append(ch)
                            text_chars.append(ch)
                        elif self.peek() in "\"'":
                            quote = self.peek()
                            ch = self.advance()
                            content_chars.append(ch)
                            text_chars.append(ch)
                            while not self.at_end() and self.peek() != quote:
                                if quote == "\"" and self.peek() == "\\":
                                    ch = self.advance()
                                    content_chars.append(ch)
                                    text_chars.append(ch)
                                ch = self.advance()
                                content_chars.append(ch)
                                text_chars.append(ch)
                            if not self.at_end():
                                ch = self.advance()
                                content_chars.append(ch)
                                text_chars.append(ch)
                        else:
                            ch = self.advance()
                            content_chars.append(ch)
                            text_chars.append(ch)
                    continue
                content_chars.append(self.advance())
                text_chars.append("<")
                content_chars.append(self.advance())
                text_chars.append("<")
                strip_tabs = False
                if not self.at_end() and self.peek() == "-":
                    strip_tabs = True
                    content_chars.append(self.advance())
                    text_chars.append("-")
                while not self.at_end() and _is_whitespace_no_newline(self.peek()):
                    ch = self.advance()
                    content_chars.append(ch)
                    text_chars.append(ch)
                delimiter_chars: list[str] = []
                if not self.at_end():
                    ch = self.peek()
                    if _is_quote(ch):
                        quote = self.advance()
                        content_chars.append(quote)
                        text_chars.append(quote)
                        while not self.at_end() and self.peek() != quote:
                            dch = self.advance()
                            content_chars.append(dch)
                            text_chars.append(dch)
                            delimiter_chars.append(dch)
                        if not self.at_end():
                            closing = self.advance()
                            content_chars.append(closing)
                            text_chars.append(closing)
                    elif ch == "\\":
                        esc = self.advance()
                        content_chars.append(esc)
                        text_chars.append(esc)
                        if not self.at_end():
                            dch = self.advance()
                            content_chars.append(dch)
                            text_chars.append(dch)
                            delimiter_chars.append(dch)
                        while not self.at_end() and not _is_metachar(self.peek()):
                            dch = self.advance()
                            content_chars.append(dch)
                            text_chars.append(dch)
                            delimiter_chars.append(dch)
                    else:
                        while not self.at_end() and not _is_metachar(self.peek()) and self.peek() != "`":
                            ch = self.peek()
                            if _is_quote(ch):
                                quote = self.advance()
                                content_chars.append(quote)
                                text_chars.append(quote)
                                while not self.at_end() and self.peek() != quote:
                                    dch = self.advance()
                                    content_chars.append(dch)
                                    text_chars.append(dch)
                                    delimiter_chars.append(dch)
                                if not self.at_end():
                                    closing = self.advance()
                                    content_chars.append(closing)
                                    text_chars.append(closing)
                            elif ch == "\\":
                                esc = self.advance()
                                content_chars.append(esc)
                                text_chars.append(esc)
                                if not self.at_end():
                                    dch = self.advance()
                                    content_chars.append(dch)
                                    text_chars.append(dch)
                                    delimiter_chars.append(dch)
                            else:
                                dch = self.advance()
                                content_chars.append(dch)
                                text_chars.append(dch)
                                delimiter_chars.append(dch)
                delimiter = "".join(delimiter_chars)
                if delimiter:
                    pending_heredocs.append((delimiter, strip_tabs))
                continue
            if c == "\n":
                ch = self.advance()
                content_chars.append(ch)
                text_chars.append(ch)
                if len(pending_heredocs) > 0:
                    current_heredoc_delim, current_heredoc_strip = pending_heredocs.pop(0)
                    in_heredoc_body = True
                continue
            ch = self.advance()
            content_chars.append(ch)
            text_chars.append(ch)
        if self.at_end():
            raise ParseError("Unterminated backtick", start)
        self.advance()
        text_chars.append("`")
        text = "".join(text_chars)
        content = "".join(content_chars)
        if len(pending_heredocs) > 0:
            heredoc_start, heredoc_end = _find_heredoc_content_end(self.source, self.pos, pending_heredocs)
            if heredoc_end > heredoc_start:
                content = content + _substring(self.source, heredoc_start, heredoc_end)
                if self._cmdsub_heredoc_end == -1:
                    self._cmdsub_heredoc_end = heredoc_end
                else:
                    self._cmdsub_heredoc_end = self._cmdsub_heredoc_end if self._cmdsub_heredoc_end > heredoc_end else heredoc_end
        sub_parser = NewParser(content, False, self._extglob)
        cmd = sub_parser.parse_list(True)
        if cmd is None:
            cmd = Empty(kind="empty")
        return (CommandSubstitution(command=cmd, kind="cmdsub"), text)

    def _parse_process_substitution(self) -> tuple[Node | None, str]:
        if self.at_end() or not _is_redirect_char(self.peek()):
            return (None, "")
        start = self.pos
        direction = self.advance()
        if self.at_end() or self.peek() != "(":
            self.pos = start
            return (None, "")
        self.advance()
        saved = self._save_parser_state()
        old_in_process_sub = self._in_process_sub
        self._in_process_sub = True
        self._set_state(ParserStateFlags_PST_EOFTOKEN)
        self._eof_token = ")"
        try:
            cmd = self.parse_list(True)
            if cmd is None:
                cmd = Empty(kind="empty")
            self.skip_whitespace_and_newlines()
            if self.at_end() or self.peek() != ")":
                raise ParseError("Invalid process substitution", start)
            self.advance()
            text_end = self.pos
            text = _substring(self.source, start, text_end)
            text = _strip_line_continuations_comment_aware(text)
            self._restore_parser_state(saved)
            self._in_process_sub = old_in_process_sub
            return (ProcessSubstitution(direction=direction, command=cmd, kind="procsub"), text)
        except ParseError as e:
            self._restore_parser_state(saved)
            self._in_process_sub = old_in_process_sub
            content_start_char = self.source[start + 2] if start + 2 < self.length else ""
            if content_start_char in " \t\n":
                raise e
            self.pos = start + 2
            self._lexer.pos = self.pos
            self._lexer._parse_matched_pair("(", ")", 0, False)
            self.pos = self._lexer.pos
            text = _substring(self.source, start, self.pos)
            text = _strip_line_continuations_comment_aware(text)
            return (None, text)

    def _parse_array_literal(self) -> tuple[Node | None, str]:
        if self.at_end() or self.peek() != "(":
            return (None, "")
        start = self.pos
        self.advance()
        self._set_state(ParserStateFlags_PST_COMPASSIGN)
        elements = []
        while True:
            self.skip_whitespace_and_newlines()
            if self.at_end():
                self._clear_state(ParserStateFlags_PST_COMPASSIGN)
                raise ParseError("Unterminated array literal", start)
            if self.peek() == ")":
                break
            word = self.parse_word(False, True, False)
            if word is None:
                if self.peek() == ")":
                    break
                self._clear_state(ParserStateFlags_PST_COMPASSIGN)
                raise ParseError("Expected word in array literal", self.pos)
            elements.append(word)
        if self.at_end() or self.peek() != ")":
            self._clear_state(ParserStateFlags_PST_COMPASSIGN)
            raise ParseError("Expected ) to close array literal", self.pos)
        self.advance()
        text = _substring(self.source, start, self.pos)
        self._clear_state(ParserStateFlags_PST_COMPASSIGN)
        return (Array(elements=elements, kind="array"), text)

    def _parse_arithmetic_expansion(self) -> tuple[Node | None, str]:
        if self.at_end() or self.peek() != "$":
            return (None, "")
        start = self.pos
        if self.pos + 2 >= self.length or self.source[self.pos + 1] != "(" or self.source[self.pos + 2] != "(":
            return (None, "")
        self.advance()
        self.advance()
        self.advance()
        content_start = self.pos
        depth = 2
        first_close_pos: int = -1
        while not self.at_end() and depth > 0:
            c = self.peek()
            if c == "'":
                self.advance()
                while not self.at_end() and self.peek() != "'":
                    self.advance()
                if not self.at_end():
                    self.advance()
            elif c == "\"":
                self.advance()
                while not self.at_end():
                    if self.peek() == "\\" and self.pos + 1 < self.length:
                        self.advance()
                        self.advance()
                    elif self.peek() == "\"":
                        self.advance()
                        break
                    else:
                        self.advance()
            elif c == "\\" and self.pos + 1 < self.length:
                self.advance()
                self.advance()
            elif c == "(":
                depth += 1
                self.advance()
            elif c == ")":
                if depth == 2:
                    first_close_pos = self.pos
                depth -= 1
                if depth == 0:
                    break
                self.advance()
            else:
                if depth == 1:
                    first_close_pos = -1
                self.advance()
        if depth != 0:
            if self.at_end():
                raise MatchedPairError("unexpected EOF looking for `))'", start)
            self.pos = start
            return (None, "")
        if first_close_pos != -1:
            content = _substring(self.source, content_start, first_close_pos)
        else:
            content = _substring(self.source, content_start, self.pos)
        self.advance()
        text = _substring(self.source, start, self.pos)
        try:
            expr = self._parse_arith_expr(content)
        except ParseError as _e:
            self.pos = start
            return (None, "")
        return (ArithmeticExpansion(expression=expr, kind="arith"), text)

    def _parse_arith_expr(self, content: str) -> Node:
        saved_arith_src = self._arith_src
        saved_arith_pos = self._arith_pos
        saved_arith_len = self._arith_len
        saved_parser_state = self._parser_state
        self._set_state(ParserStateFlags_PST_ARITH)
        self._arith_src = content
        self._arith_pos = 0
        self._arith_len = len(content)
        self._arith_skip_ws()
        if self._arith_at_end():
            result = None
        else:
            result = self._arith_parse_comma()
        self._parser_state = saved_parser_state
        if saved_arith_src != "":
            self._arith_src = saved_arith_src
            self._arith_pos = saved_arith_pos
            self._arith_len = saved_arith_len
        return result

    def _arith_at_end(self) -> bool:
        return self._arith_pos >= self._arith_len

    def _arith_peek(self, offset: int) -> str:
        pos = self._arith_pos + offset
        if pos >= self._arith_len:
            return ""
        return self._arith_src[pos]

    def _arith_advance(self) -> str:
        if self._arith_at_end():
            return ""
        c = self._arith_src[self._arith_pos]
        self._arith_pos += 1
        return c

    def _arith_skip_ws(self) -> None:
        while not self._arith_at_end():
            c = self._arith_src[self._arith_pos]
            if _is_whitespace(c):
                self._arith_pos += 1
            elif c == "\\" and self._arith_pos + 1 < self._arith_len and self._arith_src[self._arith_pos + 1] == "\n":
                self._arith_pos += 2
            else:
                break

    def _arith_match(self, s: str) -> bool:
        return _starts_with_at(self._arith_src, self._arith_pos, s)

    def _arith_consume(self, s: str) -> bool:
        if self._arith_match(s):
            self._arith_pos += len(s)
            return True
        return False

    def _arith_parse_comma(self) -> Node:
        left = self._arith_parse_assign()
        while True:
            self._arith_skip_ws()
            if self._arith_consume(","):
                self._arith_skip_ws()
                right = self._arith_parse_assign()
                left = ArithComma(left=left, right=right, kind="comma")
            else:
                break
        return left

    def _arith_parse_assign(self) -> Node:
        left = self._arith_parse_ternary()
        self._arith_skip_ws()
        assign_ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="]
        for op in assign_ops:
            if self._arith_match(op):
                if op == "=" and self._arith_peek(1) == "=":
                    break
                self._arith_consume(op)
                self._arith_skip_ws()
                right = self._arith_parse_assign()
                return ArithAssign(op=op, target=left, value=right, kind="assign")
        return left

    def _arith_parse_ternary(self) -> Node:
        cond = self._arith_parse_logical_or()
        self._arith_skip_ws()
        if self._arith_consume("?"):
            self._arith_skip_ws()
            if self._arith_match(":"):
                if_true = None
            else:
                if_true = self._arith_parse_assign()
            self._arith_skip_ws()
            if self._arith_consume(":"):
                self._arith_skip_ws()
                if self._arith_at_end() or self._arith_peek(0) == ")":
                    if_false = None
                else:
                    if_false = self._arith_parse_ternary()
            else:
                if_false = None
            return ArithTernary(condition=cond, if_true=if_true, if_false=if_false, kind="ternary")
        return cond

    def _arith_parse_left_assoc(self, ops: list[str], parsefn: Callable[[], Node]) -> Node:
        left = parsefn()
        while True:
            self._arith_skip_ws()
            matched = False
            for op in ops:
                if self._arith_match(op):
                    self._arith_consume(op)
                    self._arith_skip_ws()
                    left = ArithBinaryOp(op=op, left=left, right=parsefn(), kind="binary-op")
                    matched = True
                    break
            if not matched:
                break
        return left

    def _arith_parse_logical_or(self) -> Node:
        return self._arith_parse_left_assoc(["||"], self._arith_parse_logical_and)

    def _arith_parse_logical_and(self) -> Node:
        return self._arith_parse_left_assoc(["&&"], self._arith_parse_bitwise_or)

    def _arith_parse_bitwise_or(self) -> Node:
        left = self._arith_parse_bitwise_xor()
        while True:
            self._arith_skip_ws()
            if self._arith_peek(0) == "|" and self._arith_peek(1) != "|" and self._arith_peek(1) != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_bitwise_xor()
                left = ArithBinaryOp(op="|", left=left, right=right, kind="binary-op")
            else:
                break
        return left

    def _arith_parse_bitwise_xor(self) -> Node:
        left = self._arith_parse_bitwise_and()
        while True:
            self._arith_skip_ws()
            if self._arith_peek(0) == "^" and self._arith_peek(1) != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_bitwise_and()
                left = ArithBinaryOp(op="^", left=left, right=right, kind="binary-op")
            else:
                break
        return left

    def _arith_parse_bitwise_and(self) -> Node:
        left = self._arith_parse_equality()
        while True:
            self._arith_skip_ws()
            if self._arith_peek(0) == "&" and self._arith_peek(1) != "&" and self._arith_peek(1) != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_equality()
                left = ArithBinaryOp(op="&", left=left, right=right, kind="binary-op")
            else:
                break
        return left

    def _arith_parse_equality(self) -> Node:
        return self._arith_parse_left_assoc(["==", "!="], self._arith_parse_comparison)

    def _arith_parse_comparison(self) -> Node:
        left = self._arith_parse_shift()
        while True:
            self._arith_skip_ws()
            if self._arith_match("<="):
                self._arith_consume("<=")
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp(op="<=", left=left, right=right, kind="binary-op")
            elif self._arith_match(">="):
                self._arith_consume(">=")
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp(op=">=", left=left, right=right, kind="binary-op")
            elif self._arith_peek(0) == "<" and self._arith_peek(1) != "<" and self._arith_peek(1) != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp(op="<", left=left, right=right, kind="binary-op")
            elif self._arith_peek(0) == ">" and self._arith_peek(1) != ">" and self._arith_peek(1) != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp(op=">", left=left, right=right, kind="binary-op")
            else:
                break
        return left

    def _arith_parse_shift(self) -> Node:
        left = self._arith_parse_additive()
        while True:
            self._arith_skip_ws()
            if self._arith_match("<<="):
                break
            if self._arith_match(">>="):
                break
            if self._arith_match("<<"):
                self._arith_consume("<<")
                self._arith_skip_ws()
                right = self._arith_parse_additive()
                left = ArithBinaryOp(op="<<", left=left, right=right, kind="binary-op")
            elif self._arith_match(">>"):
                self._arith_consume(">>")
                self._arith_skip_ws()
                right = self._arith_parse_additive()
                left = ArithBinaryOp(op=">>", left=left, right=right, kind="binary-op")
            else:
                break
        return left

    def _arith_parse_additive(self) -> Node:
        left = self._arith_parse_multiplicative()
        while True:
            self._arith_skip_ws()
            c = self._arith_peek(0)
            c2 = self._arith_peek(1)
            if c == "+" and c2 != "+" and c2 != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_multiplicative()
                left = ArithBinaryOp(op="+", left=left, right=right, kind="binary-op")
            elif c == "-" and c2 != "-" and c2 != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_multiplicative()
                left = ArithBinaryOp(op="-", left=left, right=right, kind="binary-op")
            else:
                break
        return left

    def _arith_parse_multiplicative(self) -> Node:
        left = self._arith_parse_exponentiation()
        while True:
            self._arith_skip_ws()
            c = self._arith_peek(0)
            c2 = self._arith_peek(1)
            if c == "*" and c2 != "*" and c2 != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_exponentiation()
                left = ArithBinaryOp(op="*", left=left, right=right, kind="binary-op")
            elif c == "/" and c2 != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_exponentiation()
                left = ArithBinaryOp(op="/", left=left, right=right, kind="binary-op")
            elif c == "%" and c2 != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_exponentiation()
                left = ArithBinaryOp(op="%", left=left, right=right, kind="binary-op")
            else:
                break
        return left

    def _arith_parse_exponentiation(self) -> Node:
        left = self._arith_parse_unary()
        self._arith_skip_ws()
        if self._arith_match("**"):
            self._arith_consume("**")
            self._arith_skip_ws()
            right = self._arith_parse_exponentiation()
            return ArithBinaryOp(op="**", left=left, right=right, kind="binary-op")
        return left

    def _arith_parse_unary(self) -> Node:
        self._arith_skip_ws()
        if self._arith_match("++"):
            self._arith_consume("++")
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithPreIncr(operand=operand, kind="pre-incr")
        if self._arith_match("--"):
            self._arith_consume("--")
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithPreDecr(operand=operand, kind="pre-decr")
        c = self._arith_peek(0)
        if c == "!":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp(op="!", operand=operand, kind="unary-op")
        if c == "~":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp(op="~", operand=operand, kind="unary-op")
        if c == "+" and self._arith_peek(1) != "+":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp(op="+", operand=operand, kind="unary-op")
        if c == "-" and self._arith_peek(1) != "-":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp(op="-", operand=operand, kind="unary-op")
        return self._arith_parse_postfix()

    def _arith_parse_postfix(self) -> Node:
        left = self._arith_parse_primary()
        while True:
            self._arith_skip_ws()
            if self._arith_match("++"):
                self._arith_consume("++")
                left = ArithPostIncr(operand=left, kind="post-incr")
            elif self._arith_match("--"):
                self._arith_consume("--")
                left = ArithPostDecr(operand=left, kind="post-decr")
            elif self._arith_peek(0) == "[":
                if isinstance(left, ArithVar):
                    left = left
                    self._arith_advance()
                    self._arith_skip_ws()
                    index = self._arith_parse_comma()
                    self._arith_skip_ws()
                    if not self._arith_consume("]"):
                        raise ParseError("Expected ']' in array subscript", self._arith_pos)
                    left = ArithSubscript(array=left.name, index=index, kind="subscript")
                else:
                    break
            else:
                break
        return left

    def _arith_parse_primary(self) -> Node:
        self._arith_skip_ws()
        c = self._arith_peek(0)
        if c == "(":
            self._arith_advance()
            self._arith_skip_ws()
            expr = self._arith_parse_comma()
            self._arith_skip_ws()
            if not self._arith_consume(")"):
                raise ParseError("Expected ')' in arithmetic expression", self._arith_pos)
            return expr
        if c == "#" and self._arith_peek(1) == "$":
            self._arith_advance()
            return self._arith_parse_expansion()
        if c == "$":
            return self._arith_parse_expansion()
        if c == "'":
            return self._arith_parse_single_quote()
        if c == "\"":
            return self._arith_parse_double_quote()
        if c == "`":
            return self._arith_parse_backtick()
        if c == "\\":
            self._arith_advance()
            if self._arith_at_end():
                raise ParseError("Unexpected end after backslash in arithmetic", self._arith_pos)
            escaped_char = self._arith_advance()
            return ArithEscape(char=escaped_char, kind="escape")
        if self._arith_at_end() or (c in ")]:,;?|&<>=!+-*/%^~#{}"):
            return ArithEmpty(kind="empty")
        return self._arith_parse_number_or_var()

    def _arith_parse_expansion(self) -> Node:
        if not self._arith_consume("$"):
            raise ParseError("Expected '$'", self._arith_pos)
        c = self._arith_peek(0)
        if c == "(":
            return self._arith_parse_cmdsub()
        if c == "{":
            return self._arith_parse_braced_param()
        name_chars = []
        while not self._arith_at_end():
            ch = self._arith_peek(0)
            if ch.isalnum() or ch == "_":
                name_chars.append(self._arith_advance())
            elif (_is_special_param_or_digit(ch) or ch == "#") and not name_chars:
                name_chars.append(self._arith_advance())
                break
            else:
                break
        if not name_chars:
            raise ParseError("Expected variable name after $", self._arith_pos)
        return ParamExpansion(param="".join(name_chars), kind="param")

    def _arith_parse_cmdsub(self) -> Node:
        self._arith_advance()
        if self._arith_peek(0) == "(":
            self._arith_advance()
            depth = 1
            content_start = self._arith_pos
            while not self._arith_at_end() and depth > 0:
                ch = self._arith_peek(0)
                if ch == "(":
                    depth += 1
                    self._arith_advance()
                elif ch == ")":
                    if depth == 1 and self._arith_peek(1) == ")":
                        break
                    depth -= 1
                    self._arith_advance()
                else:
                    self._arith_advance()
            content = _substring(self._arith_src, content_start, self._arith_pos)
            self._arith_advance()
            self._arith_advance()
            inner_expr = self._parse_arith_expr(content)
            return ArithmeticExpansion(expression=inner_expr, kind="arith")
        depth = 1
        content_start = self._arith_pos
        while not self._arith_at_end() and depth > 0:
            ch = self._arith_peek(0)
            if ch == "(":
                depth += 1
                self._arith_advance()
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
                self._arith_advance()
            else:
                self._arith_advance()
        content = _substring(self._arith_src, content_start, self._arith_pos)
        self._arith_advance()
        sub_parser = NewParser(content, False, self._extglob)
        cmd = sub_parser.parse_list(True)
        return CommandSubstitution(command=cmd, kind="cmdsub")

    def _arith_parse_braced_param(self) -> Node:
        self._arith_advance()
        if self._arith_peek(0) == "!":
            self._arith_advance()
            name_chars = []
            while not self._arith_at_end() and self._arith_peek(0) != "}":
                name_chars.append(self._arith_advance())
            self._arith_consume("}")
            return ParamIndirect(param="".join(name_chars), kind="param-indirect")
        if self._arith_peek(0) == "#":
            self._arith_advance()
            name_chars = []
            while not self._arith_at_end() and self._arith_peek(0) != "}":
                name_chars.append(self._arith_advance())
            self._arith_consume("}")
            return ParamLength(param="".join(name_chars), kind="param-len")
        name_chars = []
        while not self._arith_at_end():
            ch = self._arith_peek(0)
            if ch == "}":
                self._arith_advance()
                return ParamExpansion(param="".join(name_chars), kind="param")
            if _is_param_expansion_op(ch):
                break
            name_chars.append(self._arith_advance())
        name = "".join(name_chars)
        op_chars = []
        depth = 1
        while not self._arith_at_end() and depth > 0:
            ch = self._arith_peek(0)
            if ch == "{":
                depth += 1
                op_chars.append(self._arith_advance())
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
                op_chars.append(self._arith_advance())
            else:
                op_chars.append(self._arith_advance())
        self._arith_consume("}")
        op_str = "".join(op_chars)
        if op_str.startswith(":-"):
            return ParamExpansion(param=name, op=":-", arg=_substring(op_str, 2, len(op_str)), kind="param")
        if op_str.startswith(":="):
            return ParamExpansion(param=name, op=":=", arg=_substring(op_str, 2, len(op_str)), kind="param")
        if op_str.startswith(":+"):
            return ParamExpansion(param=name, op=":+", arg=_substring(op_str, 2, len(op_str)), kind="param")
        if op_str.startswith(":?"):
            return ParamExpansion(param=name, op=":?", arg=_substring(op_str, 2, len(op_str)), kind="param")
        if op_str.startswith(":"):
            return ParamExpansion(param=name, op=":", arg=_substring(op_str, 1, len(op_str)), kind="param")
        if op_str.startswith("##"):
            return ParamExpansion(param=name, op="##", arg=_substring(op_str, 2, len(op_str)), kind="param")
        if op_str.startswith("#"):
            return ParamExpansion(param=name, op="#", arg=_substring(op_str, 1, len(op_str)), kind="param")
        if op_str.startswith("%%"):
            return ParamExpansion(param=name, op="%%", arg=_substring(op_str, 2, len(op_str)), kind="param")
        if op_str.startswith("%"):
            return ParamExpansion(param=name, op="%", arg=_substring(op_str, 1, len(op_str)), kind="param")
        if op_str.startswith("//"):
            return ParamExpansion(param=name, op="//", arg=_substring(op_str, 2, len(op_str)), kind="param")
        if op_str.startswith("/"):
            return ParamExpansion(param=name, op="/", arg=_substring(op_str, 1, len(op_str)), kind="param")
        return ParamExpansion(param=name, op="", arg=op_str, kind="param")

    def _arith_parse_single_quote(self) -> Node:
        self._arith_advance()
        content_start = self._arith_pos
        while not self._arith_at_end() and self._arith_peek(0) != "'":
            self._arith_advance()
        content = _substring(self._arith_src, content_start, self._arith_pos)
        if not self._arith_consume("'"):
            raise ParseError("Unterminated single quote in arithmetic", self._arith_pos)
        return ArithNumber(value=content, kind="number")

    def _arith_parse_double_quote(self) -> Node:
        self._arith_advance()
        content_start = self._arith_pos
        while not self._arith_at_end() and self._arith_peek(0) != "\"":
            c = self._arith_peek(0)
            if c == "\\" and not self._arith_at_end():
                self._arith_advance()
                self._arith_advance()
            else:
                self._arith_advance()
        content = _substring(self._arith_src, content_start, self._arith_pos)
        if not self._arith_consume("\""):
            raise ParseError("Unterminated double quote in arithmetic", self._arith_pos)
        return ArithNumber(value=content, kind="number")

    def _arith_parse_backtick(self) -> Node:
        self._arith_advance()
        content_start = self._arith_pos
        while not self._arith_at_end() and self._arith_peek(0) != "`":
            c = self._arith_peek(0)
            if c == "\\" and not self._arith_at_end():
                self._arith_advance()
                self._arith_advance()
            else:
                self._arith_advance()
        content = _substring(self._arith_src, content_start, self._arith_pos)
        if not self._arith_consume("`"):
            raise ParseError("Unterminated backtick in arithmetic", self._arith_pos)
        sub_parser = NewParser(content, False, self._extglob)
        cmd = sub_parser.parse_list(True)
        return CommandSubstitution(command=cmd, kind="cmdsub")

    def _arith_parse_number_or_var(self) -> Node:
        self._arith_skip_ws()
        chars = []
        c = self._arith_peek(0)
        if c.isdigit():
            while not self._arith_at_end():
                ch = self._arith_peek(0)
                if ch.isalnum() or ch == "#" or ch == "_":
                    chars.append(self._arith_advance())
                else:
                    break
            prefix = "".join(chars)
            if not self._arith_at_end() and self._arith_peek(0) == "$":
                expansion = self._arith_parse_expansion()
                return ArithConcat(parts=[ArithNumber(value=prefix, kind="number"), expansion], kind="arith-concat")
            return ArithNumber(value=prefix, kind="number")
        if c.isalpha() or c == "_":
            while not self._arith_at_end():
                ch = self._arith_peek(0)
                if ch.isalnum() or ch == "_":
                    chars.append(self._arith_advance())
                else:
                    break
            return ArithVar(name="".join(chars), kind="var")
        raise ParseError("Unexpected character '" + c + "' in arithmetic expression", self._arith_pos)

    def _parse_deprecated_arithmetic(self) -> tuple[Node | None, str]:
        if self.at_end() or self.peek() != "$":
            return (None, "")
        start = self.pos
        if self.pos + 1 >= self.length or self.source[self.pos + 1] != "[":
            return (None, "")
        self.advance()
        self.advance()
        self._lexer.pos = self.pos
        content = self._lexer._parse_matched_pair("[", "]", MatchedPairFlags_ARITH, False)
        self.pos = self._lexer.pos
        text = _substring(self.source, start, self.pos)
        return (ArithDeprecated(expression=content, kind="arith-deprecated"), text)

    def _parse_param_expansion(self, in_dquote: bool) -> tuple[Node | None, str]:
        self._sync_lexer()
        result0, result1 = self._lexer._read_param_expansion(in_dquote)
        self._sync_parser()
        return (result0, result1)

    def parse_redirect(self) -> Node:
        self.skip_whitespace()
        if self.at_end():
            return None
        start = self.pos
        fd: int = -1
        varfd = ""
        if self.peek() == "{":
            saved = self.pos
            self.advance()
            varname_chars = []
            in_bracket = False
            while not self.at_end() and not _is_redirect_char(self.peek()):
                ch = self.peek()
                if ch == "}" and not in_bracket:
                    break
                elif ch == "[":
                    in_bracket = True
                    varname_chars.append(self.advance())
                elif ch == "]":
                    in_bracket = False
                    varname_chars.append(self.advance())
                elif ch.isalnum() or ch == "_":
                    varname_chars.append(self.advance())
                elif in_bracket and not _is_metachar(ch):
                    varname_chars.append(self.advance())
                else:
                    break
            varname = "".join(varname_chars)
            is_valid_varfd = False
            if varname:
                if varname[0].isalpha() or varname[0] == "_":
                    if ("[" in varname) or ("]" in varname):
                        left = varname.find("[")
                        right = varname.rfind("]")
                        if left != -1 and right == len(varname) - 1 and right > left + 1:
                            base = varname[:left]
                            if base and (base[0].isalpha() or base[0] == "_"):
                                is_valid_varfd = True
                                for c in base[1:]:
                                    if not (c.isalnum() or c == "_"):
                                        is_valid_varfd = False
                                        break
                    else:
                        is_valid_varfd = True
                        for c in varname[1:]:
                            if not (c.isalnum() or c == "_"):
                                is_valid_varfd = False
                                break
            if not self.at_end() and self.peek() == "}" and is_valid_varfd:
                self.advance()
                varfd = varname
            else:
                self.pos = saved
        if varfd == "" and self.peek() and self.peek().isdigit():
            fd_chars = []
            while not self.at_end() and self.peek().isdigit():
                fd_chars.append(self.advance())
            fd = int("".join(fd_chars), 10)
        ch = self.peek()
        if ch == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == ">":
            if fd != -1 or varfd != "":
                self.pos = start
                return None
            self.advance()
            self.advance()
            if not self.at_end() and self.peek() == ">":
                self.advance()
                op = "&>>"
            else:
                op = "&>"
            self.skip_whitespace()
            target = self.parse_word(False, False, False)
            if target is None:
                raise ParseError("Expected target for redirect " + op, self.pos)
            return Redirect(op=op, target=target, kind="redirect")
        if ch == "" or not _is_redirect_char(ch):
            self.pos = start
            return None
        if fd == -1 and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            self.pos = start
            return None
        op = self.advance()
        strip_tabs = False
        if not self.at_end():
            next_ch = self.peek()
            if op == ">" and next_ch == ">":
                self.advance()
                op = ">>"
            elif op == "<" and next_ch == "<":
                self.advance()
                if not self.at_end() and self.peek() == "<":
                    self.advance()
                    op = "<<<"
                elif not self.at_end() and self.peek() == "-":
                    self.advance()
                    op = "<<"
                    strip_tabs = True
                else:
                    op = "<<"
            elif op == "<" and next_ch == ">":
                self.advance()
                op = "<>"
            elif op == ">" and next_ch == "|":
                self.advance()
                op = ">|"
            elif fd == -1 and varfd == "" and op == ">" and next_ch == "&":
                if self.pos + 1 >= self.length or not _is_digit_or_dash(self.source[self.pos + 1]):
                    self.advance()
                    op = ">&"
            elif fd == -1 and varfd == "" and op == "<" and next_ch == "&":
                if self.pos + 1 >= self.length or not _is_digit_or_dash(self.source[self.pos + 1]):
                    self.advance()
                    op = "<&"
        if op == "<<":
            return self._parse_heredoc(fd, strip_tabs)
        if varfd != "":
            op = "{" + varfd + "}" + op
        elif fd != -1:
            op = str(fd) + op
        if not self.at_end() and self.peek() == "&":
            self.advance()
            self.skip_whitespace()
            if not self.at_end() and self.peek() == "-":
                if self.pos + 1 < self.length and not _is_metachar(self.source[self.pos + 1]):
                    self.advance()
                    target = Word(value="&-", kind="word")
                else:
                    target = None
            else:
                target = None
            if target is None:
                if not self.at_end() and (self.peek().isdigit() or self.peek() == "-"):
                    word_start = self.pos
                    fd_chars = []
                    while not self.at_end() and self.peek().isdigit():
                        fd_chars.append(self.advance())
                    if fd_chars:
                        fd_target = "".join(fd_chars)
                    else:
                        fd_target = ""
                    if not self.at_end() and self.peek() == "-":
                        fd_target += self.advance()
                    if fd_target != "-" and not self.at_end() and not _is_metachar(self.peek()):
                        self.pos = word_start
                        inner_word = self.parse_word(False, False, False)
                        if inner_word is not None:
                            target = Word(value="&" + inner_word.value, kind="word")
                            target.parts = inner_word.parts
                        else:
                            raise ParseError("Expected target for redirect " + op, self.pos)
                    else:
                        target = Word(value="&" + fd_target, kind="word")
                else:
                    inner_word = self.parse_word(False, False, False)
                    if inner_word is not None:
                        target = Word(value="&" + inner_word.value, kind="word")
                        target.parts = inner_word.parts
                    else:
                        raise ParseError("Expected target for redirect " + op, self.pos)
        else:
            self.skip_whitespace()
            if (op == ">&" or op == "<&") and not self.at_end() and self.peek() == "-":
                if self.pos + 1 < self.length and not _is_metachar(self.source[self.pos + 1]):
                    self.advance()
                    target = Word(value="&-", kind="word")
                else:
                    target = self.parse_word(False, False, False)
            else:
                target = self.parse_word(False, False, False)
        if target is None:
            raise ParseError("Expected target for redirect " + op, self.pos)
        return Redirect(op=op, target=target, kind="redirect")

    def _parse_heredoc_delimiter(self) -> tuple[str, bool]:
        self.skip_whitespace()
        quoted = False
        delimiter_chars: list[str] = []
        while True:
            while not self.at_end() and not _is_metachar(self.peek()):
                ch = self.peek()
                if ch == "\"":
                    quoted = True
                    self.advance()
                    while not self.at_end() and self.peek() != "\"":
                        delimiter_chars.append(self.advance())
                    if not self.at_end():
                        self.advance()
                elif ch == "'":
                    quoted = True
                    self.advance()
                    while not self.at_end() and self.peek() != "'":
                        c = self.advance()
                        if c == "\n":
                            self._saw_newline_in_single_quote = True
                        delimiter_chars.append(c)
                    if not self.at_end():
                        self.advance()
                elif ch == "\\":
                    self.advance()
                    if not self.at_end():
                        next_ch = self.peek()
                        if next_ch == "\n":
                            self.advance()
                        else:
                            quoted = True
                            delimiter_chars.append(self.advance())
                elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "'":
                    quoted = True
                    self.advance()
                    self.advance()
                    while not self.at_end() and self.peek() != "'":
                        c = self.peek()
                        if c == "\\" and self.pos + 1 < self.length:
                            self.advance()
                            esc = self.peek()
                            esc_val = _get_ansi_escape(esc)
                            if esc_val >= 0:
                                delimiter_chars.append(chr(esc_val))
                                self.advance()
                            elif esc == "'":
                                delimiter_chars.append(self.advance())
                            else:
                                delimiter_chars.append(self.advance())
                        else:
                            delimiter_chars.append(self.advance())
                    if not self.at_end():
                        self.advance()
                elif _is_expansion_start(self.source, self.pos, "$("):
                    delimiter_chars.append(self.advance())
                    delimiter_chars.append(self.advance())
                    depth = 1
                    while not self.at_end() and depth > 0:
                        c = self.peek()
                        if c == "(":
                            depth += 1
                        elif c == ")":
                            depth -= 1
                        delimiter_chars.append(self.advance())
                elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "{":
                    dollar_count = 0
                    j = self.pos - 1
                    while j >= 0 and self.source[j] == "$":
                        dollar_count += 1
                        j -= 1
                    if j >= 0 and self.source[j] == "\\":
                        dollar_count -= 1
                    if dollar_count % 2 == 1:
                        delimiter_chars.append(self.advance())
                    else:
                        delimiter_chars.append(self.advance())
                        delimiter_chars.append(self.advance())
                        depth = 0
                        while not self.at_end():
                            c = self.peek()
                            if c == "{":
                                depth += 1
                            elif c == "}":
                                delimiter_chars.append(self.advance())
                                if depth == 0:
                                    break
                                depth -= 1
                                if depth == 0 and not self.at_end() and _is_metachar(self.peek()):
                                    break
                                continue
                            delimiter_chars.append(self.advance())
                elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "[":
                    dollar_count = 0
                    j = self.pos - 1
                    while j >= 0 and self.source[j] == "$":
                        dollar_count += 1
                        j -= 1
                    if j >= 0 and self.source[j] == "\\":
                        dollar_count -= 1
                    if dollar_count % 2 == 1:
                        delimiter_chars.append(self.advance())
                    else:
                        delimiter_chars.append(self.advance())
                        delimiter_chars.append(self.advance())
                        depth = 1
                        while not self.at_end() and depth > 0:
                            c = self.peek()
                            if c == "[":
                                depth += 1
                            elif c == "]":
                                depth -= 1
                            delimiter_chars.append(self.advance())
                elif ch == "`":
                    delimiter_chars.append(self.advance())
                    while not self.at_end() and self.peek() != "`":
                        c = self.peek()
                        if c == "'":
                            delimiter_chars.append(self.advance())
                            while not self.at_end() and self.peek() != "'" and self.peek() != "`":
                                delimiter_chars.append(self.advance())
                            if not self.at_end() and self.peek() == "'":
                                delimiter_chars.append(self.advance())
                        elif c == "\"":
                            delimiter_chars.append(self.advance())
                            while not self.at_end() and self.peek() != "\"" and self.peek() != "`":
                                if self.peek() == "\\" and self.pos + 1 < self.length:
                                    delimiter_chars.append(self.advance())
                                delimiter_chars.append(self.advance())
                            if not self.at_end() and self.peek() == "\"":
                                delimiter_chars.append(self.advance())
                        elif c == "\\" and self.pos + 1 < self.length:
                            delimiter_chars.append(self.advance())
                            delimiter_chars.append(self.advance())
                        else:
                            delimiter_chars.append(self.advance())
                    if not self.at_end():
                        delimiter_chars.append(self.advance())
                else:
                    delimiter_chars.append(self.advance())
            if not self.at_end() and (self.peek() in "<>") and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                delimiter_chars.append(self.advance())
                delimiter_chars.append(self.advance())
                depth = 1
                while not self.at_end() and depth > 0:
                    c = self.peek()
                    if c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                    delimiter_chars.append(self.advance())
                continue
            break
        return ("".join(delimiter_chars), quoted)

    def _read_heredoc_line(self, quoted: bool) -> tuple[str, int]:
        line_start = self.pos
        line_end = self.pos
        while line_end < self.length and self.source[line_end] != "\n":
            line_end += 1
        line = _substring(self.source, line_start, line_end)
        if not quoted:
            while line_end < self.length:
                trailing_bs = _count_trailing_backslashes(line)
                if trailing_bs % 2 == 0:
                    break
                line = _substring(line, 0, len(line) - 1)
                line_end += 1
                next_line_start = line_end
                while line_end < self.length and self.source[line_end] != "\n":
                    line_end += 1
                line = line + _substring(self.source, next_line_start, line_end)
        return (line, line_end)

    def _line_matches_delimiter(self, line: str, delimiter: str, strip_tabs: bool) -> tuple[bool, str]:
        check_line = line.lstrip("\t") if strip_tabs else line
        normalized_check = _normalize_heredoc_delimiter(check_line)
        normalized_delim = _normalize_heredoc_delimiter(delimiter)
        return (normalized_check == normalized_delim, check_line)

    def _gather_heredoc_bodies(self) -> None:
        for heredoc in (self._pending_heredocs or []):
            content_lines: list[str] = []
            line_start = self.pos
            while self.pos < self.length:
                line_start = self.pos
                line, line_end = self._read_heredoc_line(heredoc.quoted)
                matches, check_line = self._line_matches_delimiter(line, heredoc.delimiter, heredoc.strip_tabs)
                if matches:
                    self.pos = line_end + 1 if line_end < self.length else line_end
                    break
                normalized_check = _normalize_heredoc_delimiter(check_line)
                normalized_delim = _normalize_heredoc_delimiter(heredoc.delimiter)
                if self._eof_token == ")" and normalized_check.startswith(normalized_delim):
                    tabs_stripped = len(line) - len(check_line)
                    self.pos = line_start + tabs_stripped + len(heredoc.delimiter)
                    break
                if line_end >= self.length and normalized_check.startswith(normalized_delim) and self._in_process_sub:
                    tabs_stripped = len(line) - len(check_line)
                    self.pos = line_start + tabs_stripped + len(heredoc.delimiter)
                    break
                if heredoc.strip_tabs:
                    line = line.lstrip("\t")
                if line_end < self.length:
                    content_lines.append(line + "\n")
                    self.pos = line_end + 1
                else:
                    add_newline = True
                    if not heredoc.quoted and _count_trailing_backslashes(line) % 2 == 1:
                        add_newline = False
                    content_lines.append(line + ("\n" if add_newline else ""))
                    self.pos = self.length
            heredoc.content = "".join(content_lines)
        self._pending_heredocs = []

    def _parse_heredoc(self, fd: int, strip_tabs: bool) -> HereDoc:
        start_pos = self.pos
        self._set_state(ParserStateFlags_PST_HEREDOC)
        delimiter, quoted = self._parse_heredoc_delimiter()
        for existing in (self._pending_heredocs or []):
            if existing._start_pos == start_pos and existing.delimiter == delimiter:
                self._clear_state(ParserStateFlags_PST_HEREDOC)
                return existing
        heredoc = HereDoc(delimiter=delimiter, content="", strip_tabs=strip_tabs, quoted=quoted, fd=fd, complete=False, kind="heredoc")
        heredoc._start_pos = start_pos
        self._pending_heredocs.append(heredoc)
        self._clear_state(ParserStateFlags_PST_HEREDOC)
        return heredoc

    def parse_command(self) -> Command:
        words = []
        redirects = []
        while True:
            self.skip_whitespace()
            if self._lex_is_command_terminator():
                break
            if len(words) == 0:
                reserved = self._lex_peek_reserved_word()
                if reserved == "}" or reserved == "]]":
                    break
            redirect = self.parse_redirect()
            if redirect is not None:
                redirects.append(redirect)
                continue
            all_assignments = True
            for w in words:
                if not self._is_assignment_word(w):
                    all_assignments = False
                    break
            in_assign_builtin = len(words) > 0 and (words[0].value in ASSIGNMENT_BUILTINS)
            word = self.parse_word(not words or all_assignments and len(redirects) == 0, False, in_assign_builtin)
            if word is None:
                break
            words.append(word)
        if not words and not redirects:
            return None
        return Command(words=words, redirects=redirects, kind="command")

    def parse_subshell(self) -> Subshell:
        self.skip_whitespace()
        if self.at_end() or self.peek() != "(":
            return None
        self.advance()
        self._set_state(ParserStateFlags_PST_SUBSHELL)
        body = self.parse_list(True)
        if body is None:
            self._clear_state(ParserStateFlags_PST_SUBSHELL)
            raise ParseError("Expected command in subshell", self.pos)
        self.skip_whitespace()
        if self.at_end() or self.peek() != ")":
            self._clear_state(ParserStateFlags_PST_SUBSHELL)
            raise ParseError("Expected ) to close subshell", self.pos)
        self.advance()
        self._clear_state(ParserStateFlags_PST_SUBSHELL)
        return Subshell(body=body, redirects=self._collect_redirects(), kind="subshell")

    def parse_arithmetic_command(self) -> ArithmeticCommand:
        self.skip_whitespace()
        if self.at_end() or self.peek() != "(" or self.pos + 1 >= self.length or self.source[self.pos + 1] != "(":
            return None
        saved_pos = self.pos
        self.advance()
        self.advance()
        content_start = self.pos
        depth = 1
        while not self.at_end() and depth > 0:
            c = self.peek()
            if c == "'":
                self.advance()
                while not self.at_end() and self.peek() != "'":
                    self.advance()
                if not self.at_end():
                    self.advance()
            elif c == "\"":
                self.advance()
                while not self.at_end():
                    if self.peek() == "\\" and self.pos + 1 < self.length:
                        self.advance()
                        self.advance()
                    elif self.peek() == "\"":
                        self.advance()
                        break
                    else:
                        self.advance()
            elif c == "\\" and self.pos + 1 < self.length:
                self.advance()
                self.advance()
            elif c == "(":
                depth += 1
                self.advance()
            elif c == ")":
                if depth == 1 and self.pos + 1 < self.length and self.source[self.pos + 1] == ")":
                    break
                depth -= 1
                if depth == 0:
                    self.pos = saved_pos
                    return None
                self.advance()
            else:
                self.advance()
        if self.at_end():
            raise MatchedPairError("unexpected EOF looking for `))'", saved_pos)
        if depth != 1:
            self.pos = saved_pos
            return None
        content = _substring(self.source, content_start, self.pos)
        content = content.replace("\\\n", "")
        self.advance()
        self.advance()
        expr = self._parse_arith_expr(content)
        return ArithmeticCommand(expression=expr, redirects=self._collect_redirects(), raw_content=content, kind="arith-cmd")

    def parse_conditional_expr(self) -> ConditionalExpr:
        self.skip_whitespace()
        if self.at_end() or self.peek() != "[" or self.pos + 1 >= self.length or self.source[self.pos + 1] != "[":
            return None
        next_pos = self.pos + 2
        if next_pos < self.length and not (_is_whitespace(self.source[next_pos]) or self.source[next_pos] == "\\" and next_pos + 1 < self.length and self.source[next_pos + 1] == "\n"):
            return None
        self.advance()
        self.advance()
        self._set_state(ParserStateFlags_PST_CONDEXPR)
        self._word_context = WORD_CTX_COND
        body = self._parse_cond_or()
        while not self.at_end() and _is_whitespace_no_newline(self.peek()):
            self.advance()
        if self.at_end() or self.peek() != "]" or self.pos + 1 >= self.length or self.source[self.pos + 1] != "]":
            self._clear_state(ParserStateFlags_PST_CONDEXPR)
            self._word_context = WORD_CTX_NORMAL
            raise ParseError("Expected ]] to close conditional expression", self.pos)
        self.advance()
        self.advance()
        self._clear_state(ParserStateFlags_PST_CONDEXPR)
        self._word_context = WORD_CTX_NORMAL
        return ConditionalExpr(body=body, redirects=self._collect_redirects(), kind="cond-expr")

    def _cond_skip_whitespace(self) -> None:
        while not self.at_end():
            if _is_whitespace_no_newline(self.peek()):
                self.advance()
            elif self.peek() == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                self.advance()
                self.advance()
            elif self.peek() == "\n":
                self.advance()
            else:
                break

    def _cond_at_end(self) -> bool:
        return self.at_end() or self.peek() == "]" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]"

    def _parse_cond_or(self) -> Node:
        self._cond_skip_whitespace()
        left = self._parse_cond_and()
        self._cond_skip_whitespace()
        if not self._cond_at_end() and self.peek() == "|" and self.pos + 1 < self.length and self.source[self.pos + 1] == "|":
            self.advance()
            self.advance()
            right = self._parse_cond_or()
            return CondOr(left=left, right=right, kind="cond-or")
        return left

    def _parse_cond_and(self) -> Node:
        self._cond_skip_whitespace()
        left = self._parse_cond_term()
        self._cond_skip_whitespace()
        if not self._cond_at_end() and self.peek() == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == "&":
            self.advance()
            self.advance()
            right = self._parse_cond_and()
            return CondAnd(left=left, right=right, kind="cond-and")
        return left

    def _parse_cond_term(self) -> Node:
        self._cond_skip_whitespace()
        if self._cond_at_end():
            raise ParseError("Unexpected end of conditional expression", self.pos)
        if self.peek() == "!":
            if self.pos + 1 < self.length and not _is_whitespace_no_newline(self.source[self.pos + 1]):
                pass
            else:
                self.advance()
                operand = self._parse_cond_term()
                return CondNot(operand=operand, kind="cond-not")
        if self.peek() == "(":
            self.advance()
            inner = self._parse_cond_or()
            self._cond_skip_whitespace()
            if self.at_end() or self.peek() != ")":
                raise ParseError("Expected ) in conditional expression", self.pos)
            self.advance()
            return CondParen(inner=inner, kind="cond-paren")
        word1 = self._parse_cond_word()
        if word1 is None:
            raise ParseError("Expected word in conditional expression", self.pos)
        self._cond_skip_whitespace()
        if word1.value in COND_UNARY_OPS:
            unary_operand = self._parse_cond_word()
            if unary_operand is None:
                raise ParseError("Expected operand after " + word1.value, self.pos)
            return UnaryTest(op=word1.value, operand=unary_operand, kind="unary-test")
        if not self._cond_at_end() and self.peek() != "&" and self.peek() != "|" and self.peek() != ")":
            if _is_redirect_char(self.peek()) and not (self.pos + 1 < self.length and self.source[self.pos + 1] == "("):
                op = self.advance()
                self._cond_skip_whitespace()
                word2 = self._parse_cond_word()
                if word2 is None:
                    raise ParseError("Expected operand after " + op, self.pos)
                return BinaryTest(op=op, left=word1, right=word2, kind="binary-test")
            saved_pos = self.pos
            op_word = self._parse_cond_word()
            if op_word is not None and (op_word.value in COND_BINARY_OPS):
                self._cond_skip_whitespace()
                if op_word.value == "=~":
                    word2 = self._parse_cond_regex_word()
                else:
                    word2 = self._parse_cond_word()
                if word2 is None:
                    raise ParseError("Expected operand after " + op_word.value, self.pos)
                return BinaryTest(op=op_word.value, left=word1, right=word2, kind="binary-test")
            else:
                self.pos = saved_pos
        return UnaryTest(op="-n", operand=word1, kind="unary-test")

    def _parse_cond_word(self) -> Word:
        self._cond_skip_whitespace()
        if self._cond_at_end():
            return None
        c = self.peek()
        if _is_paren(c):
            return None
        if c == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == "&":
            return None
        if c == "|" and self.pos + 1 < self.length and self.source[self.pos + 1] == "|":
            return None
        return self._parse_word_internal(WORD_CTX_COND, False, False)

    def _parse_cond_regex_word(self) -> Word:
        self._cond_skip_whitespace()
        if self._cond_at_end():
            return None
        self._set_state(ParserStateFlags_PST_REGEXP)
        result = self._parse_word_internal(WORD_CTX_REGEX, False, False)
        self._clear_state(ParserStateFlags_PST_REGEXP)
        self._word_context = WORD_CTX_COND
        return result

    def parse_brace_group(self) -> BraceGroup:
        self.skip_whitespace()
        if not self._lex_consume_word("{"):
            return None
        self.skip_whitespace_and_newlines()
        body = self.parse_list(True)
        if body is None:
            raise ParseError("Expected command in brace group", self._lex_peek_token().pos)
        self.skip_whitespace()
        if not self._lex_consume_word("}"):
            raise ParseError("Expected } to close brace group", self._lex_peek_token().pos)
        return BraceGroup(body=body, redirects=self._collect_redirects(), kind="brace-group")

    def parse_if(self) -> If:
        self.skip_whitespace()
        if not self._lex_consume_word("if"):
            return None
        condition = self.parse_list_until({"then"})
        if condition is None:
            raise ParseError("Expected condition after 'if'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("then"):
            raise ParseError("Expected 'then' after if condition", self._lex_peek_token().pos)
        then_body = self.parse_list_until({"elif", "else", "fi"})
        if then_body is None:
            raise ParseError("Expected commands after 'then'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        else_body = None
        if self._lex_is_at_reserved_word("elif"):
            self._lex_consume_word("elif")
            elif_condition = self.parse_list_until({"then"})
            if elif_condition is None:
                raise ParseError("Expected condition after 'elif'", self._lex_peek_token().pos)
            self.skip_whitespace_and_newlines()
            if not self._lex_consume_word("then"):
                raise ParseError("Expected 'then' after elif condition", self._lex_peek_token().pos)
            elif_then_body = self.parse_list_until({"elif", "else", "fi"})
            if elif_then_body is None:
                raise ParseError("Expected commands after 'then'", self._lex_peek_token().pos)
            self.skip_whitespace_and_newlines()
            inner_else = None
            if self._lex_is_at_reserved_word("elif"):
                inner_else = self._parse_elif_chain()
            elif self._lex_is_at_reserved_word("else"):
                self._lex_consume_word("else")
                inner_else = self.parse_list_until({"fi"})
                if inner_else is None:
                    raise ParseError("Expected commands after 'else'", self._lex_peek_token().pos)
            else_body = If(condition=elif_condition, then_body=elif_then_body, else_body=inner_else, kind="if")
        elif self._lex_is_at_reserved_word("else"):
            self._lex_consume_word("else")
            else_body = self.parse_list_until({"fi"})
            if else_body is None:
                raise ParseError("Expected commands after 'else'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("fi"):
            raise ParseError("Expected 'fi' to close if statement", self._lex_peek_token().pos)
        return If(condition=condition, then_body=then_body, else_body=else_body, redirects=self._collect_redirects(), kind="if")

    def _parse_elif_chain(self) -> If:
        self._lex_consume_word("elif")
        condition = self.parse_list_until({"then"})
        if condition is None:
            raise ParseError("Expected condition after 'elif'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("then"):
            raise ParseError("Expected 'then' after elif condition", self._lex_peek_token().pos)
        then_body = self.parse_list_until({"elif", "else", "fi"})
        if then_body is None:
            raise ParseError("Expected commands after 'then'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        else_body = None
        if self._lex_is_at_reserved_word("elif"):
            else_body = self._parse_elif_chain()
        elif self._lex_is_at_reserved_word("else"):
            self._lex_consume_word("else")
            else_body = self.parse_list_until({"fi"})
            if else_body is None:
                raise ParseError("Expected commands after 'else'", self._lex_peek_token().pos)
        return If(condition=condition, then_body=then_body, else_body=else_body, kind="if")

    def parse_while(self) -> While:
        self.skip_whitespace()
        if not self._lex_consume_word("while"):
            return None
        condition = self.parse_list_until({"do"})
        if condition is None:
            raise ParseError("Expected condition after 'while'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("do"):
            raise ParseError("Expected 'do' after while condition", self._lex_peek_token().pos)
        body = self.parse_list_until({"done"})
        if body is None:
            raise ParseError("Expected commands after 'do'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("done"):
            raise ParseError("Expected 'done' to close while loop", self._lex_peek_token().pos)
        return While(condition=condition, body=body, redirects=self._collect_redirects(), kind="while")

    def parse_until(self) -> Until:
        self.skip_whitespace()
        if not self._lex_consume_word("until"):
            return None
        condition = self.parse_list_until({"do"})
        if condition is None:
            raise ParseError("Expected condition after 'until'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("do"):
            raise ParseError("Expected 'do' after until condition", self._lex_peek_token().pos)
        body = self.parse_list_until({"done"})
        if body is None:
            raise ParseError("Expected commands after 'do'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("done"):
            raise ParseError("Expected 'done' to close until loop", self._lex_peek_token().pos)
        return Until(condition=condition, body=body, redirects=self._collect_redirects(), kind="until")

    def parse_for(self) -> Node:
        self.skip_whitespace()
        if not self._lex_consume_word("for"):
            return None
        self.skip_whitespace()
        if self.peek() == "(" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            return self._parse_for_arith()
        if self.peek() == "$":
            var_word = self.parse_word(False, False, False)
            if var_word is None:
                raise ParseError("Expected variable name after 'for'", self._lex_peek_token().pos)
            var_name = var_word.value
        else:
            var_name = self.peek_word()
            if var_name == "":
                raise ParseError("Expected variable name after 'for'", self._lex_peek_token().pos)
            self.consume_word(var_name)
        self.skip_whitespace()
        if self.peek() == ";":
            self.advance()
        self.skip_whitespace_and_newlines()
        words = None
        if self._lex_is_at_reserved_word("in"):
            self._lex_consume_word("in")
            self.skip_whitespace()
            saw_delimiter = _is_semicolon_or_newline(self.peek())
            if self.peek() == ";":
                self.advance()
            self.skip_whitespace_and_newlines()
            words = []
            while True:
                self.skip_whitespace()
                if self.at_end():
                    break
                if _is_semicolon_or_newline(self.peek()):
                    saw_delimiter = True
                    if self.peek() == ";":
                        self.advance()
                    break
                if self._lex_is_at_reserved_word("do"):
                    if saw_delimiter:
                        break
                    raise ParseError("Expected ';' or newline before 'do'", self._lex_peek_token().pos)
                word = self.parse_word(False, False, False)
                if word is None:
                    break
                words.append(word)
        self.skip_whitespace_and_newlines()
        if self.peek() == "{":
            brace_group = self.parse_brace_group()
            if brace_group is None:
                raise ParseError("Expected brace group in for loop", self._lex_peek_token().pos)
            return For(var=var_name, words=words, body=brace_group.body, redirects=self._collect_redirects(), kind="for")
        if not self._lex_consume_word("do"):
            raise ParseError("Expected 'do' in for loop", self._lex_peek_token().pos)
        body = self.parse_list_until({"done"})
        if body is None:
            raise ParseError("Expected commands after 'do'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("done"):
            raise ParseError("Expected 'done' to close for loop", self._lex_peek_token().pos)
        return For(var=var_name, words=words, body=body, redirects=self._collect_redirects(), kind="for")

    def _parse_for_arith(self) -> ForArith:
        self.advance()
        self.advance()
        parts = []
        current = []
        paren_depth = 0
        while not self.at_end():
            ch = self.peek()
            if ch == "(":
                paren_depth += 1
                current.append(self.advance())
            elif ch == ")":
                if paren_depth > 0:
                    paren_depth -= 1
                    current.append(self.advance())
                elif self.pos + 1 < self.length and self.source[self.pos + 1] == ")":
                    parts.append("".join(current).lstrip(" \t"))
                    self.advance()
                    self.advance()
                    break
                else:
                    current.append(self.advance())
            elif ch == ";" and paren_depth == 0:
                parts.append("".join(current).lstrip(" \t"))
                current = []
                self.advance()
            else:
                current.append(self.advance())
        if len(parts) != 3:
            raise ParseError("Expected three expressions in for ((;;))", self.pos)
        init = parts[0]
        cond = parts[1]
        incr = parts[2]
        self.skip_whitespace()
        if not self.at_end() and self.peek() == ";":
            self.advance()
        self.skip_whitespace_and_newlines()
        body = self._parse_loop_body("for loop")
        return ForArith(init=init, cond=cond, incr=incr, body=body, redirects=self._collect_redirects(), kind="for-arith")

    def parse_select(self) -> Select:
        self.skip_whitespace()
        if not self._lex_consume_word("select"):
            return None
        self.skip_whitespace()
        var_name = self.peek_word()
        if var_name == "":
            raise ParseError("Expected variable name after 'select'", self._lex_peek_token().pos)
        self.consume_word(var_name)
        self.skip_whitespace()
        if self.peek() == ";":
            self.advance()
        self.skip_whitespace_and_newlines()
        words = None
        if self._lex_is_at_reserved_word("in"):
            self._lex_consume_word("in")
            self.skip_whitespace_and_newlines()
            words = []
            while True:
                self.skip_whitespace()
                if self.at_end():
                    break
                if _is_semicolon_newline_brace(self.peek()):
                    if self.peek() == ";":
                        self.advance()
                    break
                if self._lex_is_at_reserved_word("do"):
                    break
                word = self.parse_word(False, False, False)
                if word is None:
                    break
                words.append(word)
        self.skip_whitespace_and_newlines()
        body = self._parse_loop_body("select")
        return Select(var=var_name, words=words, body=body, redirects=self._collect_redirects(), kind="select")

    def _consume_case_terminator(self) -> str:
        term = self._lex_peek_case_terminator()
        if term != "":
            self._lex_next_token()
            return term
        return ";;"

    def parse_case(self) -> Case:
        if not self.consume_word("case"):
            return None
        self._set_state(ParserStateFlags_PST_CASESTMT)
        self.skip_whitespace()
        word = self.parse_word(False, False, False)
        if word is None:
            raise ParseError("Expected word after 'case'", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("in"):
            raise ParseError("Expected 'in' after case word", self._lex_peek_token().pos)
        self.skip_whitespace_and_newlines()
        patterns: list[CasePattern] = []
        self._set_state(ParserStateFlags_PST_CASEPAT)
        while True:
            self.skip_whitespace_and_newlines()
            if self._lex_is_at_reserved_word("esac"):
                saved = self.pos
                self.skip_whitespace()
                while not self.at_end() and not _is_metachar(self.peek()) and not _is_quote(self.peek()):
                    self.advance()
                self.skip_whitespace()
                is_pattern = False
                if not self.at_end() and self.peek() == ")":
                    if self._eof_token == ")":
                        is_pattern = False
                    else:
                        self.advance()
                        self.skip_whitespace()
                        if not self.at_end():
                            next_ch = self.peek()
                            if next_ch == ";":
                                is_pattern = True
                            elif not _is_newline_or_right_paren(next_ch):
                                is_pattern = True
                self.pos = saved
                if not is_pattern:
                    break
            self.skip_whitespace_and_newlines()
            if not self.at_end() and self.peek() == "(":
                self.advance()
                self.skip_whitespace_and_newlines()
            pattern_chars = []
            extglob_depth = 0
            while not self.at_end():
                ch = self.peek()
                if ch == ")":
                    if extglob_depth > 0:
                        pattern_chars.append(self.advance())
                        extglob_depth -= 1
                    else:
                        self.advance()
                        break
                elif ch == "\\":
                    if self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                        self.advance()
                        self.advance()
                    else:
                        pattern_chars.append(self.advance())
                        if not self.at_end():
                            pattern_chars.append(self.advance())
                elif _is_expansion_start(self.source, self.pos, "$("):
                    pattern_chars.append(self.advance())
                    pattern_chars.append(self.advance())
                    if not self.at_end() and self.peek() == "(":
                        pattern_chars.append(self.advance())
                        paren_depth = 2
                        while not self.at_end() and paren_depth > 0:
                            c = self.peek()
                            if c == "(":
                                paren_depth += 1
                            elif c == ")":
                                paren_depth -= 1
                            pattern_chars.append(self.advance())
                    else:
                        extglob_depth += 1
                elif ch == "(" and extglob_depth > 0:
                    pattern_chars.append(self.advance())
                    extglob_depth += 1
                elif self._extglob and _is_extglob_prefix(ch) and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                    pattern_chars.append(self.advance())
                    pattern_chars.append(self.advance())
                    extglob_depth += 1
                elif ch == "[":
                    is_char_class = False
                    scan_pos = self.pos + 1
                    scan_depth = 0
                    has_first_bracket_literal = False
                    if scan_pos < self.length and _is_caret_or_bang(self.source[scan_pos]):
                        scan_pos += 1
                    if scan_pos < self.length and self.source[scan_pos] == "]":
                        if self.source.find("]", scan_pos + 1) != -1:
                            scan_pos += 1
                            has_first_bracket_literal = True
                    while scan_pos < self.length:
                        sc = self.source[scan_pos]
                        if sc == "]" and scan_depth == 0:
                            is_char_class = True
                            break
                        elif sc == "[":
                            scan_depth += 1
                        elif sc == ")" and scan_depth == 0:
                            break
                        elif sc == "|" and scan_depth == 0:
                            break
                        scan_pos += 1
                    if is_char_class:
                        pattern_chars.append(self.advance())
                        if not self.at_end() and _is_caret_or_bang(self.peek()):
                            pattern_chars.append(self.advance())
                        if has_first_bracket_literal and not self.at_end() and self.peek() == "]":
                            pattern_chars.append(self.advance())
                        while not self.at_end() and self.peek() != "]":
                            pattern_chars.append(self.advance())
                        if not self.at_end():
                            pattern_chars.append(self.advance())
                    else:
                        pattern_chars.append(self.advance())
                elif ch == "'":
                    pattern_chars.append(self.advance())
                    while not self.at_end() and self.peek() != "'":
                        pattern_chars.append(self.advance())
                    if not self.at_end():
                        pattern_chars.append(self.advance())
                elif ch == "\"":
                    pattern_chars.append(self.advance())
                    while not self.at_end() and self.peek() != "\"":
                        if self.peek() == "\\" and self.pos + 1 < self.length:
                            pattern_chars.append(self.advance())
                        pattern_chars.append(self.advance())
                    if not self.at_end():
                        pattern_chars.append(self.advance())
                elif _is_whitespace(ch):
                    if extglob_depth > 0:
                        pattern_chars.append(self.advance())
                    else:
                        self.advance()
                else:
                    pattern_chars.append(self.advance())
            pattern = "".join(pattern_chars)
            if not pattern:
                raise ParseError("Expected pattern in case statement", self._lex_peek_token().pos)
            self.skip_whitespace()
            body = None
            is_empty_body = self._lex_peek_case_terminator() != ""
            if not is_empty_body:
                self.skip_whitespace_and_newlines()
                if not self.at_end() and not self._lex_is_at_reserved_word("esac"):
                    is_at_terminator = self._lex_peek_case_terminator() != ""
                    if not is_at_terminator:
                        body = self.parse_list_until({"esac"})
                        self.skip_whitespace()
            terminator = self._consume_case_terminator()
            self.skip_whitespace_and_newlines()
            patterns.append(CasePattern(pattern=pattern, body=body, terminator=terminator, kind="pattern"))
        self._clear_state(ParserStateFlags_PST_CASEPAT)
        self.skip_whitespace_and_newlines()
        if not self._lex_consume_word("esac"):
            self._clear_state(ParserStateFlags_PST_CASESTMT)
            raise ParseError("Expected 'esac' to close case statement", self._lex_peek_token().pos)
        self._clear_state(ParserStateFlags_PST_CASESTMT)
        return Case(word=word, patterns=patterns, redirects=self._collect_redirects(), kind="case")

    def parse_coproc(self) -> Coproc:
        self.skip_whitespace()
        if not self._lex_consume_word("coproc"):
            return None
        self.skip_whitespace()
        name = ""
        ch = ""
        if not self.at_end():
            ch = self.peek()
        if ch == "{":
            body = self.parse_brace_group()
            if body is not None:
                return Coproc(command=body, name=name, kind="coproc")
        if ch == "(":
            if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                body = self.parse_arithmetic_command()
                if body is not None:
                    return Coproc(command=body, name=name, kind="coproc")
            body = self.parse_subshell()
            if body is not None:
                return Coproc(command=body, name=name, kind="coproc")
        next_word = self._lex_peek_reserved_word()
        if next_word != "" and (next_word in COMPOUND_KEYWORDS):
            body = self.parse_compound_command()
            if body is not None:
                return Coproc(command=body, name=name, kind="coproc")
        word_start = self.pos
        potential_name = self.peek_word()
        if potential_name:
            while not self.at_end() and not _is_metachar(self.peek()) and not _is_quote(self.peek()):
                self.advance()
            self.skip_whitespace()
            ch = ""
            if not self.at_end():
                ch = self.peek()
            next_word = self._lex_peek_reserved_word()
            if _is_valid_identifier(potential_name):
                if ch == "{":
                    name = potential_name
                    body = self.parse_brace_group()
                    if body is not None:
                        return Coproc(command=body, name=name, kind="coproc")
                elif ch == "(":
                    name = potential_name
                    if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                        body = self.parse_arithmetic_command()
                    else:
                        body = self.parse_subshell()
                    if body is not None:
                        return Coproc(command=body, name=name, kind="coproc")
                elif next_word != "" and (next_word in COMPOUND_KEYWORDS):
                    name = potential_name
                    body = self.parse_compound_command()
                    if body is not None:
                        return Coproc(command=body, name=name, kind="coproc")
            self.pos = word_start
        body = self.parse_command()
        if body is not None:
            return Coproc(command=body, name=name, kind="coproc")
        raise ParseError("Expected command after coproc", self.pos)

    def parse_function(self) -> Function:
        self.skip_whitespace()
        if self.at_end():
            return None
        saved_pos = self.pos
        if self._lex_is_at_reserved_word("function"):
            self._lex_consume_word("function")
            self.skip_whitespace()
            name = self.peek_word()
            if name == "":
                self.pos = saved_pos
                return None
            self.consume_word(name)
            self.skip_whitespace()
            if not self.at_end() and self.peek() == "(":
                if self.pos + 1 < self.length and self.source[self.pos + 1] == ")":
                    self.advance()
                    self.advance()
            self.skip_whitespace_and_newlines()
            body = self._parse_compound_command()
            if body is None:
                raise ParseError("Expected function body", self.pos)
            return Function(name=name, body=body, kind="function")
        name = self.peek_word()
        if name == "" or (name in RESERVED_WORDS):
            return None
        if _looks_like_assignment(name):
            return None
        self.skip_whitespace()
        name_start = self.pos
        while not self.at_end() and not _is_metachar(self.peek()) and not _is_quote(self.peek()) and not _is_paren(self.peek()):
            self.advance()
        name = _substring(self.source, name_start, self.pos)
        if not name:
            self.pos = saved_pos
            return None
        brace_depth = 0
        i = 0
        while i < len(name):
            if _is_expansion_start(name, i, "${"):
                brace_depth += 1
                i += 2
                continue
            if name[i] == "}":
                brace_depth -= 1
            i += 1
        if brace_depth > 0:
            self.pos = saved_pos
            return None
        pos_after_name = self.pos
        self.skip_whitespace()
        has_whitespace = self.pos > pos_after_name
        if not has_whitespace and name and (name[-1] in "*?@+!$"):
            self.pos = saved_pos
            return None
        if self.at_end() or self.peek() != "(":
            self.pos = saved_pos
            return None
        self.advance()
        self.skip_whitespace()
        if self.at_end() or self.peek() != ")":
            self.pos = saved_pos
            return None
        self.advance()
        self.skip_whitespace_and_newlines()
        body = self._parse_compound_command()
        if body is None:
            raise ParseError("Expected function body", self.pos)
        return Function(name=name, body=body, kind="function")

    def _parse_compound_command(self) -> Node:
        result = self.parse_brace_group()
        if result is not None:
            return result
        if not self.at_end() and self.peek() == "(" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            result = self.parse_arithmetic_command()
            if result is not None:
                return result
        result = self.parse_subshell()
        if result is not None:
            return result
        result = self.parse_conditional_expr()
        if result is not None:
            return result
        result = self.parse_if()
        if result is not None:
            return result
        result = self.parse_while()
        if result is not None:
            return result
        result = self.parse_until()
        if result is not None:
            return result
        result = self.parse_for()
        if result is not None:
            return result
        result = self.parse_case()
        if result is not None:
            return result
        result = self.parse_select()
        if result is not None:
            return result
        return None

    def _at_list_until_terminator(self, stop_words: set[str]) -> bool:
        if self.at_end():
            return True
        if self.peek() == ")":
            return True
        if self.peek() == "}":
            next_pos = self.pos + 1
            if next_pos >= self.length or _is_word_end_context(self.source[next_pos]):
                return True
        reserved = self._lex_peek_reserved_word()
        if reserved != "" and (reserved in stop_words):
            return True
        if self._lex_peek_case_terminator() != "":
            return True
        return False

    def parse_list_until(self, stop_words: set[str]) -> Node:
        self.skip_whitespace_and_newlines()
        reserved = self._lex_peek_reserved_word()
        if reserved != "" and (reserved in stop_words):
            return None
        pipeline = self.parse_pipeline()
        if pipeline is None:
            return None
        parts = [pipeline]
        while True:
            self.skip_whitespace()
            op = self.parse_list_operator()
            if op == "":
                if not self.at_end() and self.peek() == "\n":
                    self.advance()
                    self._gather_heredoc_bodies()
                    if self._cmdsub_heredoc_end != -1 and self._cmdsub_heredoc_end > self.pos:
                        self.pos = self._cmdsub_heredoc_end
                        self._cmdsub_heredoc_end = -1
                    self.skip_whitespace_and_newlines()
                    if self._at_list_until_terminator(stop_words):
                        break
                    next_op = self._peek_list_operator()
                    if next_op == "&" or next_op == ";":
                        break
                    op = "\n"
                else:
                    break
            if op == "":
                break
            if op == ";":
                self.skip_whitespace_and_newlines()
                if self._at_list_until_terminator(stop_words):
                    break
                parts.append(Operator(op=op, kind="operator"))
            elif op == "&":
                parts.append(Operator(op=op, kind="operator"))
                self.skip_whitespace_and_newlines()
                if self._at_list_until_terminator(stop_words):
                    break
            elif op == "&&" or op == "||":
                parts.append(Operator(op=op, kind="operator"))
                self.skip_whitespace_and_newlines()
            else:
                parts.append(Operator(op=op, kind="operator"))
            if self._at_list_until_terminator(stop_words):
                break
            pipeline = self.parse_pipeline()
            if pipeline is None:
                raise ParseError("Expected command after " + op, self.pos)
            parts.append(pipeline)
        if len(parts) == 1:
            return parts[0]
        return List(parts=parts, kind="list")

    def parse_compound_command(self) -> Node:
        self.skip_whitespace()
        if self.at_end():
            return None
        ch = self.peek()
        if ch == "(" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            result = self.parse_arithmetic_command()
            if result is not None:
                return result
        if ch == "(":
            return self.parse_subshell()
        if ch == "{":
            result = self.parse_brace_group()
            if result is not None:
                return result
        if ch == "[" and self.pos + 1 < self.length and self.source[self.pos + 1] == "[":
            result = self.parse_conditional_expr()
            if result is not None:
                return result
        reserved = self._lex_peek_reserved_word()
        if reserved == "" and self._in_process_sub:
            word = self.peek_word()
            if word != "" and len(word) > 1 and word[0] == "}":
                keyword_word = word[1:]
                if (keyword_word in RESERVED_WORDS) or keyword_word == "{" or keyword_word == "}" or keyword_word == "[[" or keyword_word == "]]" or keyword_word == "!" or keyword_word == "time":
                    reserved = keyword_word
        if reserved == "fi" or reserved == "then" or reserved == "elif" or reserved == "else" or reserved == "done" or reserved == "esac" or reserved == "do" or reserved == "in":
            raise ParseError(f"Unexpected reserved word '{reserved}'", self._lex_peek_token().pos)
        if reserved == "if":
            return self.parse_if()
        if reserved == "while":
            return self.parse_while()
        if reserved == "until":
            return self.parse_until()
        if reserved == "for":
            return self.parse_for()
        if reserved == "select":
            return self.parse_select()
        if reserved == "case":
            return self.parse_case()
        if reserved == "function":
            return self.parse_function()
        if reserved == "coproc":
            return self.parse_coproc()
        func = self.parse_function()
        if func is not None:
            return func
        return self.parse_command()

    def parse_pipeline(self) -> Node:
        self.skip_whitespace()
        prefix_order = ""
        time_posix = False
        if self._lex_is_at_reserved_word("time"):
            self._lex_consume_word("time")
            prefix_order = "time"
            self.skip_whitespace()
            if not self.at_end() and self.peek() == "-":
                saved = self.pos
                self.advance()
                if not self.at_end() and self.peek() == "p":
                    self.advance()
                    if self.at_end() or _is_metachar(self.peek()):
                        time_posix = True
                    else:
                        self.pos = saved
                else:
                    self.pos = saved
            self.skip_whitespace()
            if not self.at_end() and _starts_with_at(self.source, self.pos, "--"):
                if self.pos + 2 >= self.length or _is_whitespace(self.source[self.pos + 2]):
                    self.advance()
                    self.advance()
                    time_posix = True
                    self.skip_whitespace()
            while self._lex_is_at_reserved_word("time"):
                self._lex_consume_word("time")
                self.skip_whitespace()
                if not self.at_end() and self.peek() == "-":
                    saved = self.pos
                    self.advance()
                    if not self.at_end() and self.peek() == "p":
                        self.advance()
                        if self.at_end() or _is_metachar(self.peek()):
                            time_posix = True
                        else:
                            self.pos = saved
                    else:
                        self.pos = saved
            self.skip_whitespace()
            if not self.at_end() and self.peek() == "!":
                if (self.pos + 1 >= self.length or _is_negation_boundary(self.source[self.pos + 1])) and not self._is_bang_followed_by_procsub():
                    self.advance()
                    prefix_order = "time_negation"
                    self.skip_whitespace()
        elif not self.at_end() and self.peek() == "!":
            if (self.pos + 1 >= self.length or _is_negation_boundary(self.source[self.pos + 1])) and not self._is_bang_followed_by_procsub():
                self.advance()
                self.skip_whitespace()
                inner = self.parse_pipeline()
                if inner is not None and inner.kind == "negation":
                    if inner.pipeline is not None:
                        return inner.pipeline
                    else:
                        return Command(words=[], kind="command")
                return Negation(pipeline=inner, kind="negation")
        result = self._parse_simple_pipeline()
        if prefix_order == "time":
            result = Time(pipeline=result, posix=time_posix, kind="time")
        elif prefix_order == "negation":
            result = Negation(pipeline=result, kind="negation")
        elif prefix_order == "time_negation":
            result = Time(pipeline=result, posix=time_posix, kind="time")
            result = Negation(pipeline=result, kind="negation")
        elif prefix_order == "negation_time":
            result = Time(pipeline=result, posix=time_posix, kind="time")
            result = Negation(pipeline=result, kind="negation")
        elif result is None:
            return None
        return result

    def _parse_simple_pipeline(self) -> Node:
        cmd = self.parse_compound_command()
        if cmd is None:
            return None
        commands = [cmd]
        while True:
            self.skip_whitespace()
            token_type, value = self._lex_peek_operator()
            if token_type == 0:
                break
            if token_type != TokenType_PIPE and token_type != TokenType_PIPE_AMP:
                break
            self._lex_next_token()
            is_pipe_both = token_type == TokenType_PIPE_AMP
            self.skip_whitespace_and_newlines()
            if is_pipe_both:
                commands.append(PipeBoth(kind="pipe-both"))
            cmd = self.parse_compound_command()
            if cmd is None:
                raise ParseError("Expected command after |", self.pos)
            commands.append(cmd)
        if len(commands) == 1:
            return commands[0]
        return Pipeline(commands=commands, kind="pipeline")

    def parse_list_operator(self) -> str:
        self.skip_whitespace()
        token_type, _ = self._lex_peek_operator()
        if token_type == 0:
            return ""
        if token_type == TokenType_AND_AND:
            self._lex_next_token()
            return "&&"
        if token_type == TokenType_OR_OR:
            self._lex_next_token()
            return "||"
        if token_type == TokenType_SEMI:
            self._lex_next_token()
            return ";"
        if token_type == TokenType_AMP:
            self._lex_next_token()
            return "&"
        return ""

    def _peek_list_operator(self) -> str:
        saved_pos = self.pos
        op = self.parse_list_operator()
        self.pos = saved_pos
        return op

    def parse_list(self, newline_as_separator: bool) -> Node:
        if newline_as_separator:
            self.skip_whitespace_and_newlines()
        else:
            self.skip_whitespace()
        pipeline = self.parse_pipeline()
        if pipeline is None:
            return None
        parts = [pipeline]
        if self._in_state(ParserStateFlags_PST_EOFTOKEN) and self._at_eof_token():
            return parts[0] if len(parts) == 1 else List(parts=parts, kind="list")
        while True:
            self.skip_whitespace()
            op = self.parse_list_operator()
            if op == "":
                if not self.at_end() and self.peek() == "\n":
                    if not newline_as_separator:
                        break
                    self.advance()
                    self._gather_heredoc_bodies()
                    if self._cmdsub_heredoc_end != -1 and self._cmdsub_heredoc_end > self.pos:
                        self.pos = self._cmdsub_heredoc_end
                        self._cmdsub_heredoc_end = -1
                    self.skip_whitespace_and_newlines()
                    if self.at_end() or self._at_list_terminating_bracket():
                        break
                    next_op = self._peek_list_operator()
                    if next_op == "&" or next_op == ";":
                        break
                    op = "\n"
                else:
                    break
            if op == "":
                break
            parts.append(Operator(op=op, kind="operator"))
            if op == "&&" or op == "||":
                self.skip_whitespace_and_newlines()
            elif op == "&":
                self.skip_whitespace()
                if self.at_end() or self._at_list_terminating_bracket():
                    break
                if self.peek() == "\n":
                    if newline_as_separator:
                        self.skip_whitespace_and_newlines()
                        if self.at_end() or self._at_list_terminating_bracket():
                            break
                    else:
                        break
            elif op == ";":
                self.skip_whitespace()
                if self.at_end() or self._at_list_terminating_bracket():
                    break
                if self.peek() == "\n":
                    if newline_as_separator:
                        self.skip_whitespace_and_newlines()
                        if self.at_end() or self._at_list_terminating_bracket():
                            break
                    else:
                        break
            pipeline = self.parse_pipeline()
            if pipeline is None:
                raise ParseError("Expected command after " + op, self.pos)
            parts.append(pipeline)
            if self._in_state(ParserStateFlags_PST_EOFTOKEN) and self._at_eof_token():
                break
        if len(parts) == 1:
            return parts[0]
        return List(parts=parts, kind="list")

    def parse_comment(self) -> Node:
        if self.at_end() or self.peek() != "#":
            return None
        start = self.pos
        while not self.at_end() and self.peek() != "\n":
            self.advance()
        text = _substring(self.source, start, self.pos)
        return Comment(text=text, kind="comment")

    def parse(self) -> list[Node]:
        source = self.source.strip(" \t\n\r")
        if not source:
            return [Empty(kind="empty")]
        results = []
        while True:
            self.skip_whitespace()
            while not self.at_end() and self.peek() == "\n":
                self.advance()
            if self.at_end():
                break
            comment = self.parse_comment()
            if not comment is not None:
                break
        while not self.at_end():
            result = self.parse_list(False)
            if result is not None:
                results.append(result)
            self.skip_whitespace()
            found_newline = False
            while not self.at_end() and self.peek() == "\n":
                found_newline = True
                self.advance()
                self._gather_heredoc_bodies()
                if self._cmdsub_heredoc_end != -1 and self._cmdsub_heredoc_end > self.pos:
                    self.pos = self._cmdsub_heredoc_end
                    self._cmdsub_heredoc_end = -1
                self.skip_whitespace()
            if not found_newline and not self.at_end():
                raise ParseError("Syntax error", self.pos)
        if not results:
            return [Empty(kind="empty")]
        if self._saw_newline_in_single_quote and self.source and self.source[-1] == "\\" and not (len(self.source) >= 3 and self.source[-3:-1] == "\\\n"):
            if not self._last_word_on_own_line(results):
                self._strip_trailing_backslash_from_last_word(results)
        return results

    def _last_word_on_own_line(self, nodes: list[Node]) -> bool:
        return len(nodes) >= 2

    def _strip_trailing_backslash_from_last_word(self, nodes: list[Node]) -> None:
        if not nodes:
            return
        last_node = nodes[-1]
        last_word = self._find_last_word(last_node)
        if last_word is not None and last_word.value.endswith("\\"):
            last_word.value = _substring(last_word.value, 0, len(last_word.value) - 1)
            if not last_word.value and isinstance(last_node, Command) and last_node.words:
                last_node.words.pop()

    def _find_last_word(self, node: Node) -> Word:
        if isinstance(node, Word):
            node = node
            return node
        if isinstance(node, Command):
            node = node
            if node.words:
                last_word = node.words[-1]
                if last_word.value.endswith("\\"):
                    return last_word
            if node.redirects:
                last_redirect = node.redirects[-1]
                if isinstance(last_redirect, Redirect):
                    last_redirect = last_redirect
                    return last_redirect.target
            if node.words:
                return node.words[-1]
        if isinstance(node, Pipeline):
            node = node
            if node.commands:
                return self._find_last_word(node.commands[-1])
        if isinstance(node, List):
            node = node
            if node.parts:
                return self._find_last_word(node.parts[-1])
        return None


def _is_hex_digit(c: str) -> bool:
    return c >= "0" and c <= "9" or c >= "a" and c <= "f" or c >= "A" and c <= "F"


def _is_octal_digit(c: str) -> bool:
    return c >= "0" and c <= "7"


def _get_ansi_escape(c: str) -> int:
    return ANSI_C_ESCAPES.get(c, -1)


def _is_whitespace(c: str) -> bool:
    return c == " " or c == "\t" or c == "\n"


def _string_to_bytes(s: str) -> list[int]:
    return s.encode("utf-8").copy()


def _is_whitespace_no_newline(c: str) -> bool:
    return c == " " or c == "\t"


def _substring(s: str, start: int, end: int) -> str:
    return s[start:end]


def _starts_with_at(s: str, pos: int, prefix: str) -> bool:
    return s.startswith(prefix, pos)


def _count_consecutive_dollars_before(s: str, pos: int) -> int:
    count = 0
    k = pos - 1
    while k >= 0 and s[k] == "$":
        bs_count = 0
        j = k - 1
        while j >= 0 and s[j] == "\\":
            bs_count += 1
            j -= 1
        if bs_count % 2 == 1:
            break
        count += 1
        k -= 1
    return count


def _is_expansion_start(s: str, pos: int, delimiter: str) -> bool:
    if not _starts_with_at(s, pos, delimiter):
        return False
    return _count_consecutive_dollars_before(s, pos) % 2 == 0


def _sublist(lst: list[Node], start: int, end: int) -> list[Node]:
    return lst[start:end]


def _repeat_str(s: str, n: int) -> str:
    result = []
    i = 0
    while i < n:
        result.append(s)
        i += 1
    return "".join(result)


def _strip_line_continuations_comment_aware(text: str) -> str:
    result = []
    i = 0
    in_comment = False
    quote = NewQuoteState()
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text) and text[i + 1] == "\n":
            num_preceding_backslashes = 0
            j = i - 1
            while j >= 0 and text[j] == "\\":
                num_preceding_backslashes += 1
                j -= 1
            if num_preceding_backslashes % 2 == 0:
                if in_comment:
                    result.append("\n")
                i += 2
                in_comment = False
                continue
        if c == "\n":
            in_comment = False
            result.append(c)
            i += 1
            continue
        if c == "'" and not quote.double and not in_comment:
            quote.single = not quote.single
        elif c == "\"" and not quote.single and not in_comment:
            quote.double = not quote.double
        elif c == "#" and not quote.single and not in_comment:
            in_comment = True
        result.append(c)
        i += 1
    return "".join(result)


def _append_redirects(base: str, redirects: list[Node]) -> str:
    if redirects:
        parts = []
        for r in redirects:
            parts.append(r.to_sexp())
        return base + " " + " ".join(parts)
    return base


def _format_arith_val(s: str) -> str:
    w = Word(value=s, parts=[], kind="word")
    val = w._expand_all_ansi_c_quotes(s)
    val = w._strip_locale_string_dollars(val)
    val = w._format_command_substitutions(val, False)
    val = val.replace("\\", "\\\\").replace("\"", "\\\"")
    val = val.replace("\n", "\\n").replace("\t", "\\t")
    return val


def _consume_single_quote(s: str, start: int) -> tuple[int, list[str]]:
    chars = ["'"]
    i = start + 1
    while i < len(s) and s[i] != "'":
        chars.append(s[i])
        i += 1
    if i < len(s):
        chars.append(s[i])
        i += 1
    return (i, chars)


def _consume_double_quote(s: str, start: int) -> tuple[int, list[str]]:
    chars = ["\""]
    i = start + 1
    while i < len(s) and s[i] != "\"":
        if s[i] == "\\" and i + 1 < len(s):
            chars.append(s[i])
            i += 1
        chars.append(s[i])
        i += 1
    if i < len(s):
        chars.append(s[i])
        i += 1
    return (i, chars)


def _has_bracket_close(s: str, start: int, depth: int) -> bool:
    i = start
    while i < len(s):
        if s[i] == "]":
            return True
        if (s[i] == "|" or s[i] == ")") and depth == 0:
            return False
        i += 1
    return False


def _consume_bracket_class(s: str, start: int, depth: int) -> tuple[int, list[str], bool]:
    scan_pos = start + 1
    if scan_pos < len(s) and (s[scan_pos] == "!" or s[scan_pos] == "^"):
        scan_pos += 1
    if scan_pos < len(s) and s[scan_pos] == "]":
        if _has_bracket_close(s, scan_pos + 1, depth):
            scan_pos += 1
    is_bracket = False
    while scan_pos < len(s):
        if s[scan_pos] == "]":
            is_bracket = True
            break
        if s[scan_pos] == ")" and depth == 0:
            break
        if s[scan_pos] == "|" and depth == 0:
            break
        scan_pos += 1
    if not is_bracket:
        return (start + 1, ["["], False)
    chars = ["["]
    i = start + 1
    if i < len(s) and (s[i] == "!" or s[i] == "^"):
        chars.append(s[i])
        i += 1
    if i < len(s) and s[i] == "]":
        if _has_bracket_close(s, i + 1, depth):
            chars.append(s[i])
            i += 1
    while i < len(s) and s[i] != "]":
        chars.append(s[i])
        i += 1
    if i < len(s):
        chars.append(s[i])
        i += 1
    return (i, chars, True)


def _format_cond_body(node: Node) -> str:
    kind = node.kind
    if kind == "unary-test":
        operand_val = node.operand.get_cond_formatted_value()
        return node.op + " " + operand_val
    if kind == "binary-test":
        left_val = node.left.get_cond_formatted_value()
        right_val = node.right.get_cond_formatted_value()
        return left_val + " " + node.op + " " + right_val
    if kind == "cond-and":
        return _format_cond_body(node.left) + " && " + _format_cond_body(node.right)
    if kind == "cond-or":
        return _format_cond_body(node.left) + " || " + _format_cond_body(node.right)
    if kind == "cond-not":
        return "! " + _format_cond_body(node.operand)
    if kind == "cond-paren":
        return "( " + _format_cond_body(node.inner) + " )"
    return ""


def _starts_with_subshell(node: Node) -> bool:
    if isinstance(node, Subshell):
        node = node
        return True
    if isinstance(node, List):
        node = node
        for p in (node.parts or []):
            if p.kind != "operator":
                return _starts_with_subshell(p)
        return False
    if isinstance(node, Pipeline):
        node = node
        if node.commands:
            return _starts_with_subshell(node.commands[0])
        return False
    return False


def _format_cmdsub_node(node: Node, indent: int, in_procsub: bool, compact_redirects: bool, procsub_first: bool) -> str:
    if node is None:
        return ""
    sp = _repeat_str(" ", indent)
    inner_sp = _repeat_str(" ", indent + 4)
    if isinstance(node, ArithEmpty):
        node = node
        return ""
    if isinstance(node, Command):
        node = node
        parts = []
        for w in (node.words or []):
            val = w._expand_all_ansi_c_quotes(w.value)
            val = w._strip_locale_string_dollars(val)
            val = w._normalize_array_whitespace(val)
            val = w._format_command_substitutions(val, False)
            parts.append(val)
        heredocs: list[HereDoc] = []
        for r in (node.redirects or []):
            if isinstance(r, HereDoc):
                r = r
                heredocs.append(r)
        for r in (node.redirects or []):
            parts.append(_format_redirect(r, compact_redirects, True))
        if compact_redirects and node.words and node.redirects:
            word_parts = parts[:len(node.words)]
            redirect_parts = parts[len(node.words):]
            result = " ".join(word_parts) + "".join(redirect_parts)
        else:
            result = " ".join(parts)
        for h in heredocs:
            result = result + _format_heredoc_body(h)
        return result
    if isinstance(node, Pipeline):
        node = node
        cmds: list[tuple[Node, bool]] = []
        i = 0
        while i < len(node.commands):
            cmd = node.commands[i]
            if isinstance(cmd, PipeBoth):
                cmd = cmd
                i += 1
                continue
            needs_redirect = i + 1 < len(node.commands) and node.commands[i + 1].kind == "pipe-both"
            cmds.append((cmd, needs_redirect))
            i += 1
        result_parts = []
        idx = 0
        while idx < len(cmds):
            _entry: tuple[Node, bool] = cmds[idx]
            cmd = _entry[0]
            needs_redirect = _entry[1]
            formatted = _format_cmdsub_node(cmd, indent, in_procsub, False, procsub_first and idx == 0)
            is_last = idx == len(cmds) - 1
            has_heredoc = False
            if cmd.kind == "command" and cmd.redirects:
                for r in (cmd.redirects or []):
                    if isinstance(r, HereDoc):
                        r = r
                        has_heredoc = True
                        break
            if needs_redirect:
                if has_heredoc:
                    first_nl = formatted.find("\n")
                    if first_nl != -1:
                        formatted = formatted[:first_nl] + " 2>&1" + formatted[first_nl:]
                    else:
                        formatted = formatted + " 2>&1"
                else:
                    formatted = formatted + " 2>&1"
            if not is_last and has_heredoc:
                first_nl = formatted.find("\n")
                if first_nl != -1:
                    formatted = formatted[:first_nl] + " |" + formatted[first_nl:]
                result_parts.append(formatted)
            else:
                result_parts.append(formatted)
            idx += 1
        compact_pipe = in_procsub and cmds and cmds[0][0].kind == "subshell"
        result = ""
        idx = 0
        while idx < len(result_parts):
            part = result_parts[idx]
            if idx > 0:
                if result.endswith("\n"):
                    result = result + "  " + part
                elif compact_pipe:
                    result = result + "|" + part
                else:
                    result = result + " | " + part
            else:
                result = part
            idx += 1
        return result
    if isinstance(node, List):
        node = node
        has_heredoc = False
        for p in (node.parts or []):
            if p.kind == "command" and p.redirects:
                for r in (p.redirects or []):
                    if isinstance(r, HereDoc):
                        r = r
                        has_heredoc = True
                        break
            else:
                if isinstance(p, Pipeline):
                    p = p
                    for cmd in (p.commands or []):
                        if cmd.kind == "command" and cmd.redirects:
                            for r in (cmd.redirects or []):
                                if isinstance(r, HereDoc):
                                    r = r
                                    has_heredoc = True
                                    break
                        if has_heredoc:
                            break
        result = []
        skipped_semi = False
        cmd_count = 0
        for p in (node.parts or []):
            if isinstance(p, Operator):
                p = p
                if p.op == ";":
                    if result and result[-1].endswith("\n"):
                        skipped_semi = True
                        continue
                    if len(result) >= 3 and result[-2] == "\n" and result[-3].endswith("\n"):
                        skipped_semi = True
                        continue
                    result.append(";")
                    skipped_semi = False
                elif p.op == "\n":
                    if result and result[-1] == ";":
                        skipped_semi = False
                        continue
                    if result and result[-1].endswith("\n"):
                        result.append(" " if skipped_semi else "\n")
                        skipped_semi = False
                        continue
                    result.append("\n")
                    skipped_semi = False
                elif p.op == "&":
                    if result and ("<<" in result[-1]) and ("\n" in result[-1]):
                        last = result[-1]
                        if (" |" in last) or last.startswith("|"):
                            result[-1] = last + " &"
                        else:
                            first_nl = last.find("\n")
                            result[-1] = last[:first_nl] + " &" + last[first_nl:]
                    else:
                        result.append(" &")
                elif result and ("<<" in result[-1]) and ("\n" in result[-1]):
                    last = result[-1]
                    first_nl = last.find("\n")
                    result[-1] = last[:first_nl] + " " + p.op + " " + last[first_nl:]
                else:
                    result.append(" " + p.op)
            else:
                if result and not result[-1].endswith((" ", "\n")):
                    result.append(" ")
                formatted_cmd = _format_cmdsub_node(p, indent, in_procsub, compact_redirects, procsub_first and cmd_count == 0)
                if len(result) > 0:
                    last = result[-1]
                    if (" || \n" in last) or (" && \n" in last):
                        formatted_cmd = " " + formatted_cmd
                if skipped_semi:
                    formatted_cmd = " " + formatted_cmd
                    skipped_semi = False
                result.append(formatted_cmd)
                cmd_count += 1
        s = "".join(result)
        if (" &\n" in s) and s.endswith("\n"):
            return s + " "
        while s.endswith(";"):
            s = _substring(s, 0, len(s) - 1)
        if not has_heredoc:
            while s.endswith("\n"):
                s = _substring(s, 0, len(s) - 1)
        return s
    if isinstance(node, If):
        node = node
        cond = _format_cmdsub_node(node.condition, indent, False, False, False)
        then_body = _format_cmdsub_node(node.then_body, indent + 4, False, False, False)
        result = "if " + cond + "; then\n" + inner_sp + then_body + ";"
        if node.else_body is not None:
            else_body = _format_cmdsub_node(node.else_body, indent + 4, False, False, False)
            result = result + "\n" + sp + "else\n" + inner_sp + else_body + ";"
        result = result + "\n" + sp + "fi"
        return result
    if isinstance(node, While):
        node = node
        cond = _format_cmdsub_node(node.condition, indent, False, False, False)
        body = _format_cmdsub_node(node.body, indent + 4, False, False, False)
        result = "while " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done"
        if node.redirects:
            for r in (node.redirects or []):
                result = result + " " + _format_redirect(r, False, False)
        return result
    if isinstance(node, Until):
        node = node
        cond = _format_cmdsub_node(node.condition, indent, False, False, False)
        body = _format_cmdsub_node(node.body, indent + 4, False, False, False)
        result = "until " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done"
        if node.redirects:
            for r in (node.redirects or []):
                result = result + " " + _format_redirect(r, False, False)
        return result
    if isinstance(node, For):
        node = node
        var = node.var
        body = _format_cmdsub_node(node.body, indent + 4, False, False, False)
        if node.words is not None:
            word_vals: list[str] = []
            for w in (node.words or []):
                word_vals.append(w.value)
            words = " ".join(word_vals)
            if words:
                result = "for " + var + " in " + words + ";\n" + sp + "do\n" + inner_sp + body + ";\n" + sp + "done"
            else:
                result = "for " + var + " in ;\n" + sp + "do\n" + inner_sp + body + ";\n" + sp + "done"
        else:
            result = "for " + var + " in \"$@\";\n" + sp + "do\n" + inner_sp + body + ";\n" + sp + "done"
        if node.redirects:
            for r in (node.redirects or []):
                result = result + " " + _format_redirect(r, False, False)
        return result
    if isinstance(node, ForArith):
        node = node
        body = _format_cmdsub_node(node.body, indent + 4, False, False, False)
        result = "for ((" + node.init + "; " + node.cond + "; " + node.incr + "))\ndo\n" + inner_sp + body + ";\n" + sp + "done"
        if node.redirects:
            for r in (node.redirects or []):
                result = result + " " + _format_redirect(r, False, False)
        return result
    if isinstance(node, Case):
        node = node
        word = node.word.value
        patterns: list[str] = []
        i = 0
        while i < len(node.patterns):
            p = node.patterns[i]
            pat = p.pattern.replace("|", " | ")
            if p.body is not None:
                body = _format_cmdsub_node(p.body, indent + 8, False, False, False)
            else:
                body = ""
            term = p.terminator
            pat_indent = _repeat_str(" ", indent + 8)
            term_indent = _repeat_str(" ", indent + 4)
            body_part = pat_indent + body + "\n" if body else "\n"
            if i == 0:
                patterns.append(" " + pat + ")\n" + body_part + term_indent + term)
            else:
                patterns.append(pat + ")\n" + body_part + term_indent + term)
            i += 1
        pattern_str = ("\n" + _repeat_str(" ", indent + 4)).join(patterns)
        redirects = ""
        if node.redirects:
            redirect_parts: list[str] = []
            for r in (node.redirects or []):
                redirect_parts.append(_format_redirect(r, False, False))
            redirects = " " + " ".join(redirect_parts)
        return "case " + word + " in" + pattern_str + "\n" + sp + "esac" + redirects
    if isinstance(node, Function):
        node = node
        name = node.name
        inner_body = node.body.body if node.body.kind == "brace-group" else node.body
        body = _format_cmdsub_node(inner_body, indent + 4, False, False, False).rstrip(";")
        return f"""function {name} () 
{{ 
{inner_sp}{body}
}}"""
    if isinstance(node, Subshell):
        node = node
        body = _format_cmdsub_node(node.body, indent, in_procsub, compact_redirects, False)
        redirects = ""
        if node.redirects:
            redirect_parts: list[str] = []
            for r in (node.redirects or []):
                redirect_parts.append(_format_redirect(r, False, False))
            redirects = " ".join(redirect_parts)
        if procsub_first:
            if redirects:
                return "(" + body + ") " + redirects
            return "(" + body + ")"
        if redirects:
            return "( " + body + " ) " + redirects
        return "( " + body + " )"
    if isinstance(node, BraceGroup):
        node = node
        body = _format_cmdsub_node(node.body, indent, False, False, False)
        body = body.rstrip(";")
        terminator = " }" if body.endswith(" &") else "; }"
        redirects = ""
        if node.redirects:
            redirect_parts: list[str] = []
            for r in (node.redirects or []):
                redirect_parts.append(_format_redirect(r, False, False))
            redirects = " ".join(redirect_parts)
        if redirects:
            return "{ " + body + terminator + " " + redirects
        return "{ " + body + terminator
    if isinstance(node, ArithmeticCommand):
        node = node
        return "((" + node.raw_content + "))"
    if isinstance(node, ConditionalExpr):
        node = node
        body = _format_cond_body(node.body)
        return "[[ " + body + " ]]"
    if isinstance(node, Negation):
        node = node
        if node.pipeline is not None:
            return "! " + _format_cmdsub_node(node.pipeline, indent, False, False, False)
        return "! "
    if isinstance(node, Time):
        node = node
        prefix = "time -p " if node.posix else "time "
        if node.pipeline is not None:
            return prefix + _format_cmdsub_node(node.pipeline, indent, False, False, False)
        return prefix
    return ""


def _format_redirect(r: Node, compact: bool, heredoc_op_only: bool) -> str:
    if isinstance(r, HereDoc):
        r = r
        if r.strip_tabs:
            op = "<<-"
        else:
            op = "<<"
        if r.fd > 0:
            op = str(r.fd) + op
        if r.quoted:
            delim = "'" + r.delimiter + "'"
        else:
            delim = r.delimiter
        if heredoc_op_only:
            return op + delim
        return op + delim + "\n" + r.content + r.delimiter + "\n"
    op = r.op
    if op == "1>":
        op = ">"
    elif op == "0<":
        op = "<"
    target = r.target.value
    target = r.target._expand_all_ansi_c_quotes(target)
    target = r.target._strip_locale_string_dollars(target)
    target = r.target._format_command_substitutions(target, False)
    if target.startswith("&"):
        was_input_close = False
        if target == "&-" and op.endswith("<"):
            was_input_close = True
            op = _substring(op, 0, len(op) - 1) + ">"
        after_amp = _substring(target, 1, len(target))
        is_literal_fd = after_amp == "-" or len(after_amp) > 0 and after_amp[0].isdigit()
        if is_literal_fd:
            if op == ">" or op == ">&":
                op = "0>" if was_input_close else "1>"
            elif op == "<" or op == "<&":
                op = "0<"
        elif op == "1>":
            op = ">"
        elif op == "0<":
            op = "<"
        return op + target
    if op.endswith("&"):
        return op + target
    if compact:
        return op + target
    return op + " " + target


def _format_heredoc_body(r: Node) -> str:
    return "\n" + r.content + r.delimiter + "\n"


def _lookahead_for_esac(value: str, start: int, case_depth: int) -> bool:
    i = start
    depth = case_depth
    quote = NewQuoteState()
    while i < len(value):
        c = value[i]
        if c == "\\" and i + 1 < len(value) and quote.double:
            i += 2
            continue
        if c == "'" and not quote.double:
            quote.single = not quote.single
            i += 1
            continue
        if c == "\"" and not quote.single:
            quote.double = not quote.double
            i += 1
            continue
        if quote.single or quote.double:
            i += 1
            continue
        if _starts_with_at(value, i, "case") and _is_word_boundary(value, i, 4):
            depth += 1
            i += 4
        elif _starts_with_at(value, i, "esac") and _is_word_boundary(value, i, 4):
            depth -= 1
            if depth == 0:
                return True
            i += 4
        elif c == "(":
            i += 1
        elif c == ")":
            if depth > 0:
                i += 1
            else:
                break
        else:
            i += 1
    return False


def _skip_backtick(value: str, start: int) -> int:
    i = start + 1
    while i < len(value) and value[i] != "`":
        if value[i] == "\\" and i + 1 < len(value):
            i += 2
        else:
            i += 1
    if i < len(value):
        i += 1
    return i


def _skip_single_quoted(s: str, start: int) -> int:
    i = start
    while i < len(s) and s[i] != "'":
        i += 1
    return i + 1 if i < len(s) else i


def _skip_double_quoted(s: str, start: int) -> int:
    i = start
    n = len(s)
    pass_next = False
    backq = False
    while i < n:
        c = s[i]
        if pass_next:
            pass_next = False
            i += 1
            continue
        if c == "\\":
            pass_next = True
            i += 1
            continue
        if backq:
            if c == "`":
                backq = False
            i += 1
            continue
        if c == "`":
            backq = True
            i += 1
            continue
        if c == "$" and i + 1 < n:
            if s[i + 1] == "(":
                i = _find_cmdsub_end(s, i + 2)
                continue
            if s[i + 1] == "{":
                i = _find_braced_param_end(s, i + 2)
                continue
        if c == "\"":
            return i + 1
        i += 1
    return i


def _is_valid_arithmetic_start(value: str, start: int) -> bool:
    scan_paren = 0
    scan_i = start + 3
    while scan_i < len(value):
        scan_c = value[scan_i]
        if _is_expansion_start(value, scan_i, "$("):
            scan_i = _find_cmdsub_end(value, scan_i + 2)
            continue
        if scan_c == "(":
            scan_paren += 1
        elif scan_c == ")":
            if scan_paren > 0:
                scan_paren -= 1
            elif scan_i + 1 < len(value) and value[scan_i + 1] == ")":
                return True
            else:
                return False
        scan_i += 1
    return False


def _find_funsub_end(value: str, start: int) -> int:
    depth = 1
    i = start
    quote = NewQuoteState()
    while i < len(value) and depth > 0:
        c = value[i]
        if c == "\\" and i + 1 < len(value) and not quote.single:
            i += 2
            continue
        if c == "'" and not quote.double:
            quote.single = not quote.single
            i += 1
            continue
        if c == "\"" and not quote.single:
            quote.double = not quote.double
            i += 1
            continue
        if quote.single or quote.double:
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(value)


def _find_cmdsub_end(value: str, start: int) -> int:
    depth = 1
    i = start
    case_depth = 0
    in_case_patterns = False
    arith_depth = 0
    arith_paren_depth = 0
    while i < len(value) and depth > 0:
        c = value[i]
        if c == "\\" and i + 1 < len(value):
            i += 2
            continue
        if c == "'":
            i = _skip_single_quoted(value, i + 1)
            continue
        if c == "\"":
            i = _skip_double_quoted(value, i + 1)
            continue
        if c == "#" and arith_depth == 0 and (i == start or value[i - 1] == " " or value[i - 1] == "\t" or value[i - 1] == "\n" or value[i - 1] == ";" or value[i - 1] == "|" or value[i - 1] == "&" or value[i - 1] == "(" or value[i - 1] == ")"):
            while i < len(value) and value[i] != "\n":
                i += 1
            continue
        if _starts_with_at(value, i, "<<<"):
            i += 3
            while i < len(value) and (value[i] == " " or value[i] == "\t"):
                i += 1
            if i < len(value) and value[i] == "\"":
                i += 1
                while i < len(value) and value[i] != "\"":
                    if value[i] == "\\" and i + 1 < len(value):
                        i += 2
                    else:
                        i += 1
                if i < len(value):
                    i += 1
            elif i < len(value) and value[i] == "'":
                i += 1
                while i < len(value) and value[i] != "'":
                    i += 1
                if i < len(value):
                    i += 1
            else:
                while i < len(value) and (value[i] not in " \t\n;|&<>()"):
                    i += 1
            continue
        if _is_expansion_start(value, i, "$(("):
            if _is_valid_arithmetic_start(value, i):
                arith_depth += 1
                i += 3
                continue
            j = _find_cmdsub_end(value, i + 2)
            i = j
            continue
        if arith_depth > 0 and arith_paren_depth == 0 and _starts_with_at(value, i, "))"):
            arith_depth -= 1
            i += 2
            continue
        if c == "`":
            i = _skip_backtick(value, i)
            continue
        if arith_depth == 0 and _starts_with_at(value, i, "<<"):
            i = _skip_heredoc(value, i)
            continue
        if _starts_with_at(value, i, "case") and _is_word_boundary(value, i, 4):
            case_depth += 1
            in_case_patterns = False
            i += 4
            continue
        if case_depth > 0 and _starts_with_at(value, i, "in") and _is_word_boundary(value, i, 2):
            in_case_patterns = True
            i += 2
            continue
        if _starts_with_at(value, i, "esac") and _is_word_boundary(value, i, 4):
            if case_depth > 0:
                case_depth -= 1
                in_case_patterns = False
            i += 4
            continue
        if _starts_with_at(value, i, ";;"):
            i += 2
            continue
        if c == "(":
            if not (in_case_patterns and case_depth > 0):
                if arith_depth > 0:
                    arith_paren_depth += 1
                else:
                    depth += 1
        elif c == ")":
            if in_case_patterns and case_depth > 0:
                if not _lookahead_for_esac(value, i + 1, case_depth):
                    depth -= 1
            elif arith_depth > 0:
                if arith_paren_depth > 0:
                    arith_paren_depth -= 1
            else:
                depth -= 1
        i += 1
    return i


def _find_braced_param_end(value: str, start: int) -> int:
    depth = 1
    i = start
    in_double = False
    dolbrace_state = DolbraceState_PARAM
    while i < len(value) and depth > 0:
        c = value[i]
        if c == "\\" and i + 1 < len(value):
            i += 2
            continue
        if c == "'" and dolbrace_state == DolbraceState_QUOTE and not in_double:
            i = _skip_single_quoted(value, i + 1)
            continue
        if c == "\"":
            in_double = not in_double
            i += 1
            continue
        if in_double:
            i += 1
            continue
        if dolbrace_state == DolbraceState_PARAM and (c in "%#^,"):
            dolbrace_state = DolbraceState_QUOTE
        elif dolbrace_state == DolbraceState_PARAM and (c in ":-=?+/"):
            dolbrace_state = DolbraceState_WORD
        if c == "[" and dolbrace_state == DolbraceState_PARAM and not in_double:
            end = _skip_subscript(value, i, 0)
            if end != -1:
                i = end
                continue
        if (c == "<" or c == ">") and i + 1 < len(value) and value[i + 1] == "(":
            i = _find_cmdsub_end(value, i + 2)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        if _is_expansion_start(value, i, "$("):
            i = _find_cmdsub_end(value, i + 2)
            continue
        if _is_expansion_start(value, i, "${"):
            i = _find_braced_param_end(value, i + 2)
            continue
        i += 1
    return i


def _skip_heredoc(value: str, start: int) -> int:
    i = start + 2
    if i < len(value) and value[i] == "-":
        i += 1
    while i < len(value) and _is_whitespace_no_newline(value[i]):
        i += 1
    delim_start = i
    quote_char = None
    if i < len(value) and (value[i] == "\"" or value[i] == "'"):
        quote_char = value[i]
        i += 1
        delim_start = i
        while i < len(value) and value[i] != quote_char:
            i += 1
        delimiter = _substring(value, delim_start, i)
        if i < len(value):
            i += 1
    elif i < len(value) and value[i] == "\\":
        i += 1
        delim_start = i
        if i < len(value):
            i += 1
        while i < len(value) and not _is_metachar(value[i]):
            i += 1
        delimiter = _substring(value, delim_start, i)
    else:
        while i < len(value) and not _is_metachar(value[i]):
            i += 1
        delimiter = _substring(value, delim_start, i)
    paren_depth = 0
    quote = NewQuoteState()
    in_backtick = False
    while i < len(value) and value[i] != "\n":
        c = value[i]
        if c == "\\" and i + 1 < len(value) and (quote.double or in_backtick):
            i += 2
            continue
        if c == "'" and not quote.double and not in_backtick:
            quote.single = not quote.single
            i += 1
            continue
        if c == "\"" and not quote.single and not in_backtick:
            quote.double = not quote.double
            i += 1
            continue
        if c == "`" and not quote.single:
            in_backtick = not in_backtick
            i += 1
            continue
        if quote.single or quote.double or in_backtick:
            i += 1
            continue
        if c == "(":
            paren_depth += 1
        elif c == ")":
            if paren_depth == 0:
                break
            paren_depth -= 1
        i += 1
    if i < len(value) and value[i] == ")":
        return i
    if i < len(value) and value[i] == "\n":
        i += 1
    while i < len(value):
        line_start = i
        line_end = i
        while line_end < len(value) and value[line_end] != "\n":
            line_end += 1
        line = _substring(value, line_start, line_end)
        while line_end < len(value):
            trailing_bs = 0
            j: int = len(line) - 1
            while j > -1:
                if line[j] == "\\":
                    trailing_bs += 1
                else:
                    break
                j += -1
            if trailing_bs % 2 == 0:
                break
            line = line[:-1]
            line_end += 1
            next_line_start = line_end
            while line_end < len(value) and value[line_end] != "\n":
                line_end += 1
            line = line + _substring(value, next_line_start, line_end)
        if start + 2 < len(value) and value[start + 2] == "-":
            stripped = line.lstrip("\t")
        else:
            stripped = line
        if stripped == delimiter:
            if line_end < len(value):
                return line_end + 1
            else:
                return line_end
        if stripped.startswith(delimiter) and len(stripped) > len(delimiter):
            tabs_stripped = len(line) - len(stripped)
            return line_start + tabs_stripped + len(delimiter)
        if line_end < len(value):
            i = line_end + 1
        else:
            i = line_end
    return i


def _find_heredoc_content_end(source: str, start: int, delimiters: list[tuple[str, bool]]) -> tuple[int, int]:
    if not delimiters:
        return (start, start)
    pos = start
    while pos < len(source) and source[pos] != "\n":
        pos += 1
    if pos >= len(source):
        return (start, start)
    content_start = pos
    pos += 1
    for _item in delimiters:
        delimiter = _item[0]
        strip_tabs = _item[1]
        while pos < len(source):
            line_start = pos
            line_end = pos
            while line_end < len(source) and source[line_end] != "\n":
                line_end += 1
            line = _substring(source, line_start, line_end)
            while line_end < len(source):
                trailing_bs = 0
                j: int = len(line) - 1
                while j > -1:
                    if line[j] == "\\":
                        trailing_bs += 1
                    else:
                        break
                    j += -1
                if trailing_bs % 2 == 0:
                    break
                line = line[:-1]
                line_end += 1
                next_line_start = line_end
                while line_end < len(source) and source[line_end] != "\n":
                    line_end += 1
                line = line + _substring(source, next_line_start, line_end)
            if strip_tabs:
                line_stripped = line.lstrip("\t")
            else:
                line_stripped = line
            if line_stripped == delimiter:
                pos = line_end + 1 if line_end < len(source) else line_end
                break
            if line_stripped.startswith(delimiter) and len(line_stripped) > len(delimiter):
                tabs_stripped = len(line) - len(line_stripped)
                pos = line_start + tabs_stripped + len(delimiter)
                break
            pos = line_end + 1 if line_end < len(source) else line_end
    return (content_start, pos)


def _is_word_boundary(s: str, pos: int, word_len: int) -> bool:
    if pos > 0:
        prev = s[pos - 1]
        if prev.isalnum() or prev == "_":
            return False
        if prev in "{}!":
            return False
    end = pos + word_len
    if end < len(s) and (s[end].isalnum() or s[end] == "_"):
        return False
    return True


def _is_quote(c: str) -> bool:
    return c == "'" or c == "\""


def _collapse_whitespace(s: str) -> str:
    result = []
    prev_was_ws = False
    for c in s:
        if c == " " or c == "\t":
            if not prev_was_ws:
                result.append(" ")
            prev_was_ws = True
        else:
            result.append(c)
            prev_was_ws = False
    joined = "".join(result)
    return joined.strip(" \t")


def _count_trailing_backslashes(s: str) -> int:
    count = 0
    i: int = len(s) - 1
    while i > -1:
        if s[i] == "\\":
            count += 1
        else:
            break
        i += -1
    return count


def _normalize_heredoc_delimiter(delimiter: str) -> str:
    result = []
    i = 0
    while i < len(delimiter):
        if i + 1 < len(delimiter) and delimiter[i:i + 2] == "$(":
            result.append("$(")
            i += 2
            depth = 1
            inner = []
            while i < len(delimiter) and depth > 0:
                if delimiter[i] == "(":
                    depth += 1
                    inner.append(delimiter[i])
                elif delimiter[i] == ")":
                    depth -= 1
                    if depth == 0:
                        inner_str = "".join(inner)
                        inner_str = _collapse_whitespace(inner_str)
                        result.append(inner_str)
                        result.append(")")
                    else:
                        inner.append(delimiter[i])
                else:
                    inner.append(delimiter[i])
                i += 1
        elif i + 1 < len(delimiter) and delimiter[i:i + 2] == "${":
            result.append("${")
            i += 2
            depth = 1
            inner = []
            while i < len(delimiter) and depth > 0:
                if delimiter[i] == "{":
                    depth += 1
                    inner.append(delimiter[i])
                elif delimiter[i] == "}":
                    depth -= 1
                    if depth == 0:
                        inner_str = "".join(inner)
                        inner_str = _collapse_whitespace(inner_str)
                        result.append(inner_str)
                        result.append("}")
                    else:
                        inner.append(delimiter[i])
                else:
                    inner.append(delimiter[i])
                i += 1
        elif i + 1 < len(delimiter) and (delimiter[i] in "<>") and delimiter[i + 1] == "(":
            result.append(delimiter[i])
            result.append("(")
            i += 2
            depth = 1
            inner = []
            while i < len(delimiter) and depth > 0:
                if delimiter[i] == "(":
                    depth += 1
                    inner.append(delimiter[i])
                elif delimiter[i] == ")":
                    depth -= 1
                    if depth == 0:
                        inner_str = "".join(inner)
                        inner_str = _collapse_whitespace(inner_str)
                        result.append(inner_str)
                        result.append(")")
                    else:
                        inner.append(delimiter[i])
                else:
                    inner.append(delimiter[i])
                i += 1
        else:
            result.append(delimiter[i])
            i += 1
    return "".join(result)


def _is_metachar(c: str) -> bool:
    return c == " " or c == "\t" or c == "\n" or c == "|" or c == "&" or c == ";" or c == "(" or c == ")" or c == "<" or c == ">"


def _is_funsub_char(c: str) -> bool:
    return c == " " or c == "\t" or c == "\n" or c == "|"


def _is_extglob_prefix(c: str) -> bool:
    return c == "@" or c == "?" or c == "*" or c == "+" or c == "!"


def _is_redirect_char(c: str) -> bool:
    return c == "<" or c == ">"


def _is_special_param(c: str) -> bool:
    return c == "?" or c == "$" or c == "!" or c == "#" or c == "@" or c == "*" or c == "-" or c == "&"


def _is_special_param_unbraced(c: str) -> bool:
    return c == "?" or c == "$" or c == "!" or c == "#" or c == "@" or c == "*" or c == "-"


def _is_digit(c: str) -> bool:
    return c >= "0" and c <= "9"


def _is_semicolon_or_newline(c: str) -> bool:
    return c == ";" or c == "\n"


def _is_word_end_context(c: str) -> bool:
    return c == " " or c == "\t" or c == "\n" or c == ";" or c == "|" or c == "&" or c == "<" or c == ">" or c == "(" or c == ")"


def _skip_matched_pair(s: str, start: int, open_: str, close: str, flags: int) -> int:
    n = len(s)
    if flags & _SMP_PAST_OPEN:
        i = start
    else:
        if start >= n or s[start] != open_:
            return -1
        i = start + 1
    depth = 1
    pass_next = False
    backq = False
    while i < n and depth > 0:
        c = s[i]
        if pass_next:
            pass_next = False
            i += 1
            continue
        literal = flags & _SMP_LITERAL
        if not literal and c == "\\":
            pass_next = True
            i += 1
            continue
        if backq:
            if c == "`":
                backq = False
            i += 1
            continue
        if not literal and c == "`":
            backq = True
            i += 1
            continue
        if not literal and c == "'":
            i = _skip_single_quoted(s, i + 1)
            continue
        if not literal and c == "\"":
            i = _skip_double_quoted(s, i + 1)
            continue
        if not literal and _is_expansion_start(s, i, "$("):
            i = _find_cmdsub_end(s, i + 2)
            continue
        if not literal and _is_expansion_start(s, i, "${"):
            i = _find_braced_param_end(s, i + 2)
            continue
        if not literal and c == open_:
            depth += 1
        elif c == close:
            depth -= 1
        i += 1
    return i if depth == 0 else -1


def _skip_subscript(s: str, start: int, flags: int) -> int:
    return _skip_matched_pair(s, start, "[", "]", flags)


def _assignment(s: str, flags: int) -> int:
    if not s:
        return -1
    if not (s[0].isalpha() or s[0] == "_"):
        return -1
    i = 1
    while i < len(s):
        c = s[i]
        if c == "=":
            return i
        if c == "[":
            sub_flags = _SMP_LITERAL if flags & 2 else 0
            end = _skip_subscript(s, i, sub_flags)
            if end == -1:
                return -1
            i = end
            if i < len(s) and s[i] == "+":
                i += 1
            if i < len(s) and s[i] == "=":
                return i
            return -1
        if c == "+":
            if i + 1 < len(s) and s[i + 1] == "=":
                return i + 1
            return -1
        if not (c.isalnum() or c == "_"):
            return -1
        i += 1
    return -1


def _is_array_assignment_prefix(chars: list[str]) -> bool:
    if not chars:
        return False
    if not (chars[0].isalpha() or chars[0] == "_"):
        return False
    s = "".join(chars)
    i = 1
    while i < len(s) and (s[i].isalnum() or s[i] == "_"):
        i += 1
    while i < len(s):
        if s[i] != "[":
            return False
        end = _skip_subscript(s, i, _SMP_LITERAL)
        if end == -1:
            return False
        i = end
    return True


def _is_special_param_or_digit(c: str) -> bool:
    return _is_special_param(c) or _is_digit(c)


def _is_param_expansion_op(c: str) -> bool:
    return c == ":" or c == "-" or c == "=" or c == "+" or c == "?" or c == "#" or c == "%" or c == "/" or c == "^" or c == "," or c == "@" or c == "*" or c == "["


def _is_simple_param_op(c: str) -> bool:
    return c == "-" or c == "=" or c == "?" or c == "+"


def _is_escape_char_in_backtick(c: str) -> bool:
    return c == "$" or c == "`" or c == "\\"


def _is_negation_boundary(c: str) -> bool:
    return _is_whitespace(c) or c == ";" or c == "|" or c == ")" or c == "&" or c == ">" or c == "<"


def _is_backslash_escaped(value: str, idx: int) -> bool:
    bs_count = 0
    j = idx - 1
    while j >= 0 and value[j] == "\\":
        bs_count += 1
        j -= 1
    return bs_count % 2 == 1


def _is_dollar_dollar_paren(value: str, idx: int) -> bool:
    dollar_count = 0
    j = idx - 1
    while j >= 0 and value[j] == "$":
        dollar_count += 1
        j -= 1
    return dollar_count % 2 == 1


def _is_paren(c: str) -> bool:
    return c == "(" or c == ")"


def _is_caret_or_bang(c: str) -> bool:
    return c == "!" or c == "^"


def _is_at_or_star(c: str) -> bool:
    return c == "@" or c == "*"


def _is_digit_or_dash(c: str) -> bool:
    return _is_digit(c) or c == "-"


def _is_newline_or_right_paren(c: str) -> bool:
    return c == "\n" or c == ")"


def _is_semicolon_newline_brace(c: str) -> bool:
    return c == ";" or c == "\n" or c == "{"


def _looks_like_assignment(s: str) -> bool:
    return _assignment(s, 0) != -1


def _is_valid_identifier(name: str) -> bool:
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    for c in name[1:]:
        if not (c.isalnum() or c == "_"):
            return False
    return True


def parse(source: str, extglob: bool) -> list[Node]:
    parser = NewParser(source, False, extglob)
    return parser.parse()


def NewParseError(message: str, pos: int, line: int) -> ParseError:
    self = ParseError()
    self.message = message
    self.pos = pos
    self.line = line
    return self


def NewMatchedPairError(message: str, pos: int, line: int) -> MatchedPairError:
    return MatchedPairError()


def NewQuoteState() -> QuoteState:
    self = QuoteState()
    self.single = False
    self.double = False
    self._stack = []
    return self


def NewParseContext(kind: int) -> ParseContext:
    self = ParseContext()
    self.kind = kind
    self.paren_depth = 0
    self.brace_depth = 0
    self.bracket_depth = 0
    self.case_depth = 0
    self.arith_depth = 0
    self.arith_paren_depth = 0
    self.quote = NewQuoteState()
    return self


def NewContextStack() -> ContextStack:
    self = ContextStack()
    self._stack = [NewParseContext(0)]
    return self


def NewLexer(source: str, extglob: bool) -> Lexer:
    self = Lexer()
    self.source = source
    self.pos = 0
    self.length = len(source)
    self.quote = NewQuoteState()
    self._token_cache = None
    self._parser_state = ParserStateFlags_NONE
    self._dolbrace_state = DolbraceState_NONE
    self._pending_heredocs = []
    self._extglob = extglob
    self._parser = None
    self._eof_token = ""
    self._last_read_token = None
    self._word_context = WORD_CTX_NORMAL
    self._at_command_start = False
    self._in_array_literal = False
    self._in_assign_builtin = False
    self._post_read_pos = 0
    self._cached_word_context = WORD_CTX_NORMAL
    self._cached_at_command_start = False
    self._cached_in_array_literal = False
    self._cached_in_assign_builtin = False
    return self


def NewParser(source: str, in_process_sub: bool, extglob: bool) -> Parser:
    self = Parser()
    self.source = source
    self.pos = 0
    self.length = len(source)
    self._pending_heredocs = []
    self._cmdsub_heredoc_end = -1
    self._saw_newline_in_single_quote = False
    self._in_process_sub = in_process_sub
    self._extglob = extglob
    self._ctx = NewContextStack()
    self._lexer = NewLexer(source, extglob)
    self._lexer._parser = self
    self._token_history = [None, None, None, None]
    self._parser_state = ParserStateFlags_NONE
    self._dolbrace_state = DolbraceState_NONE
    self._eof_token = ""
    self._word_context = WORD_CTX_NORMAL
    self._at_command_start = False
    self._in_array_literal = False
    self._in_assign_builtin = False
    self._arith_src = ""
    self._arith_pos = 0
    self._arith_len = 0
    return self
