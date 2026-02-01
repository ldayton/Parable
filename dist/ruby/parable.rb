# frozen_string_literal: true

require 'set'

ANSI_C_ESCAPES = {"a" => 7, "b" => 8, "e" => 27, "E" => 27, "f" => 12, "n" => 10, "r" => 13, "t" => 9, "v" => 11, "\\" => 92, "\"" => 34, "?" => 63}
TOKENTYPE_EOF = 0
TOKENTYPE_WORD = 1
TOKENTYPE_NEWLINE = 2
TOKENTYPE_SEMI = 10
TOKENTYPE_PIPE = 11
TOKENTYPE_AMP = 12
TOKENTYPE_LPAREN = 13
TOKENTYPE_RPAREN = 14
TOKENTYPE_LBRACE = 15
TOKENTYPE_RBRACE = 16
TOKENTYPE_LESS = 17
TOKENTYPE_GREATER = 18
TOKENTYPE_AND_AND = 30
TOKENTYPE_OR_OR = 31
TOKENTYPE_SEMI_SEMI = 32
TOKENTYPE_SEMI_AMP = 33
TOKENTYPE_SEMI_SEMI_AMP = 34
TOKENTYPE_LESS_LESS = 35
TOKENTYPE_GREATER_GREATER = 36
TOKENTYPE_LESS_AMP = 37
TOKENTYPE_GREATER_AMP = 38
TOKENTYPE_LESS_GREATER = 39
TOKENTYPE_GREATER_PIPE = 40
TOKENTYPE_LESS_LESS_MINUS = 41
TOKENTYPE_LESS_LESS_LESS = 42
TOKENTYPE_AMP_GREATER = 43
TOKENTYPE_AMP_GREATER_GREATER = 44
TOKENTYPE_PIPE_AMP = 45
TOKENTYPE_IF = 50
TOKENTYPE_THEN = 51
TOKENTYPE_ELSE = 52
TOKENTYPE_ELIF = 53
TOKENTYPE_FI = 54
TOKENTYPE_CASE = 55
TOKENTYPE_ESAC = 56
TOKENTYPE_FOR = 57
TOKENTYPE_WHILE = 58
TOKENTYPE_UNTIL = 59
TOKENTYPE_DO = 60
TOKENTYPE_DONE = 61
TOKENTYPE_IN = 62
TOKENTYPE_FUNCTION = 63
TOKENTYPE_SELECT = 64
TOKENTYPE_COPROC = 65
TOKENTYPE_TIME = 66
TOKENTYPE_BANG = 67
TOKENTYPE_LBRACKET_LBRACKET = 68
TOKENTYPE_RBRACKET_RBRACKET = 69
TOKENTYPE_ASSIGNMENT_WORD = 80
TOKENTYPE_NUMBER = 81
PARSERSTATEFLAGS_NONE = 0
PARSERSTATEFLAGS_PST_CASEPAT = 1
PARSERSTATEFLAGS_PST_CMDSUBST = 2
PARSERSTATEFLAGS_PST_CASESTMT = 4
PARSERSTATEFLAGS_PST_CONDEXPR = 8
PARSERSTATEFLAGS_PST_COMPASSIGN = 16
PARSERSTATEFLAGS_PST_ARITH = 32
PARSERSTATEFLAGS_PST_HEREDOC = 64
PARSERSTATEFLAGS_PST_REGEXP = 128
PARSERSTATEFLAGS_PST_EXTPAT = 256
PARSERSTATEFLAGS_PST_SUBSHELL = 512
PARSERSTATEFLAGS_PST_REDIRLIST = 1024
PARSERSTATEFLAGS_PST_COMMENT = 2048
PARSERSTATEFLAGS_PST_EOFTOKEN = 4096
DOLBRACESTATE_NONE = 0
DOLBRACESTATE_PARAM = 1
DOLBRACESTATE_OP = 2
DOLBRACESTATE_WORD = 4
DOLBRACESTATE_QUOTE = 64
DOLBRACESTATE_QUOTE2 = 128
MATCHEDPAIRFLAGS_NONE = 0
MATCHEDPAIRFLAGS_DQUOTE = 1
MATCHEDPAIRFLAGS_DOLBRACE = 2
MATCHEDPAIRFLAGS_COMMAND = 4
MATCHEDPAIRFLAGS_ARITH = 8
MATCHEDPAIRFLAGS_ALLOWESC = 16
MATCHEDPAIRFLAGS_EXTGLOB = 32
MATCHEDPAIRFLAGS_FIRSTCLOSE = 64
MATCHEDPAIRFLAGS_ARRAYSUB = 128
MATCHEDPAIRFLAGS_BACKQUOTE = 256
PARSECONTEXT_NORMAL = 0
PARSECONTEXT_COMMAND_SUB = 1
PARSECONTEXT_ARITHMETIC = 2
PARSECONTEXT_CASE_PATTERN = 3
PARSECONTEXT_BRACE_EXPANSION = 4
RESERVED_WORDS = Set["if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"]
COND_UNARY_OPS = Set["-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"]
COND_BINARY_OPS = Set["==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"]
COMPOUND_KEYWORDS = Set["while", "until", "for", "if", "case", "select"]
ASSIGNMENT_BUILTINS = Set["alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"]
SMP_LITERAL = 1
SMP_PAST_OPEN = 2
WORD_CTX_NORMAL = 0
WORD_CTX_COND = 1
WORD_CTX_REGEX = 2

module Node
  def get_kind()
    raise NotImplementedError
  end
  def to_sexp()
    raise NotImplementedError
  end
end

class ParseError < StandardError
  attr_accessor :message, :pos, :line

  def initialize(message: "", pos: 0, line: 0)
    @message = message
    @pos = pos
    @line = line
  end

  def format_message()
    if self.line != 0 && self.pos != 0
      return "Parse error at line #{self.line}, position #{self.pos}: #{self.message}"
    elsif self.pos != 0
      return "Parse error at position #{self.pos}: #{self.message}"
    end
    return "Parse error: #{self.message}"
  end
end

class MatchedPairError < ParseError
  # Empty class
end


class Token
  attr_accessor :type, :value, :pos, :parts, :word

  def initialize(type: 0, value: "", pos: 0, parts: [], word: nil)
    @type = type
    @value = value
    @pos = pos
    @parts = parts
    @word = word
  end

  def _repr__()
    if !self.word.nil?
      return "Token(#{self.type}, #{self.value}, #{self.pos}, word=#{self.word})"
    end
    if (self.parts && !self.parts.empty?)
      return "Token(#{self.type}, #{self.value}, #{self.pos}, parts=#{self.parts.length})"
    end
    return "Token(#{self.type}, #{self.value}, #{self.pos})"
  end
end




class SavedParserState
  attr_accessor :parser_state, :dolbrace_state, :pending_heredocs, :ctx_stack, :eof_token

  def initialize(parser_state: 0, dolbrace_state: 0, pending_heredocs: [], ctx_stack: [], eof_token: "")
    @parser_state = parser_state
    @dolbrace_state = dolbrace_state
    @pending_heredocs = pending_heredocs
    @ctx_stack = ctx_stack
    @eof_token = eof_token
  end
end

class QuoteState
  attr_accessor :single, :double, :stack

  def initialize(single: false, double: false, stack: [])
    @single = single
    @double = double
    @stack = stack
  end

  def push()
    self.stack.push([self.single, self.double])
    self.single = false
    self.double = false
  end

  def pop()
    if (self.stack && !self.stack.empty?)
      self.single, self.double = self.stack.pop
    end
  end

  def in_quotes()
    return self.single || self.double
  end

  def copy()
    qs = new_quote_state()
    qs.single = self.single
    qs.double = self.double
    qs.stack = self.stack.dup
    return qs
  end

  def outer_double()
    if self.stack.length == 0
      return false
    end
    return self.stack[-1][1]
  end
end

class ParseContext
  attr_accessor :kind, :paren_depth, :brace_depth, :bracket_depth, :case_depth, :arith_depth, :arith_paren_depth, :quote

  def initialize(kind: 0, paren_depth: 0, brace_depth: 0, bracket_depth: 0, case_depth: 0, arith_depth: 0, arith_paren_depth: 0, quote: nil)
    @kind = kind
    @paren_depth = paren_depth
    @brace_depth = brace_depth
    @bracket_depth = bracket_depth
    @case_depth = case_depth
    @arith_depth = arith_depth
    @arith_paren_depth = arith_paren_depth
    @quote = quote
  end

  def copy()
    ctx = new_parse_context(self.kind)
    ctx.paren_depth = self.paren_depth
    ctx.brace_depth = self.brace_depth
    ctx.bracket_depth = self.bracket_depth
    ctx.case_depth = self.case_depth
    ctx.arith_depth = self.arith_depth
    ctx.arith_paren_depth = self.arith_paren_depth
    ctx.quote = self.quote.copy
    return ctx
  end
end

class ContextStack
  attr_accessor :stack

  def initialize(stack: [])
    @stack = stack
  end

  def get_current()
    return self.stack[-1]
  end

  def push(kind)
    self.stack.push(new_parse_context(kind))
  end

  def pop()
    if self.stack.length > 1
      return self.stack.pop
    end
    return self.stack[0]
  end

  def copy_stack()
    result = []
    (self.stack || []).each do |ctx|
      result.push(ctx.copy)
    end
    return result
  end

  def restore_from(saved_stack)
    result = []
    saved_stack.each do |ctx|
      result.push(ctx.copy)
    end
    self.stack = result
  end
end

class Lexer
  attr_accessor :reserved_words, :source, :pos, :length, :quote, :token_cache, :parser_state, :dolbrace_state, :pending_heredocs, :extglob, :parser, :eof_token, :last_read_token, :word_context, :at_command_start, :in_array_literal, :in_assign_builtin, :post_read_pos, :cached_word_context, :cached_at_command_start, :cached_in_array_literal, :cached_in_assign_builtin

  def initialize(reserved_words: {}, source: "", pos: 0, length: 0, quote: nil, token_cache: nil, parser_state: 0, dolbrace_state: 0, pending_heredocs: [], extglob: false, parser: nil, eof_token: "", last_read_token: nil, word_context: 0, at_command_start: false, in_array_literal: false, in_assign_builtin: false, post_read_pos: 0, cached_word_context: 0, cached_at_command_start: false, cached_in_array_literal: false, cached_in_assign_builtin: false)
    @reserved_words = reserved_words
    @source = source
    @pos = pos
    @length = length
    @quote = quote
    @token_cache = token_cache
    @parser_state = parser_state
    @dolbrace_state = dolbrace_state
    @pending_heredocs = pending_heredocs
    @extglob = extglob
    @parser = parser
    @eof_token = eof_token
    @last_read_token = last_read_token
    @word_context = word_context
    @at_command_start = at_command_start
    @in_array_literal = in_array_literal
    @in_assign_builtin = in_assign_builtin
    @post_read_pos = post_read_pos
    @cached_word_context = cached_word_context
    @cached_at_command_start = cached_at_command_start
    @cached_in_array_literal = cached_in_array_literal
    @cached_in_assign_builtin = cached_in_assign_builtin
  end

  def peek()
    if self.pos >= self.length
      return ""
    end
    return self.source[self.pos]
  end

  def advance()
    if self.pos >= self.length
      return ""
    end
    c = self.source[self.pos]
    self.pos += 1
    return c
  end

  def at_end()
    return self.pos >= self.length
  end

  def lookahead(n)
    return substring(self.source, self.pos, self.pos + n)
  end

  def is_metachar(c)
    return "|&;()<> \t\n".include?(c)
  end

  def read_operator()
    start = self.pos
    c = self.peek
    if c == ""
      return nil
    end
    two = self.lookahead(2)
    three = self.lookahead(3)
    if three == ";;&"
      self.pos += 3
      return Token.new(type: TOKENTYPE_SEMI_SEMI_AMP, value: three, pos: start)
    end
    if three == "<<-"
      self.pos += 3
      return Token.new(type: TOKENTYPE_LESS_LESS_MINUS, value: three, pos: start)
    end
    if three == "<<<"
      self.pos += 3
      return Token.new(type: TOKENTYPE_LESS_LESS_LESS, value: three, pos: start)
    end
    if three == "&>>"
      self.pos += 3
      return Token.new(type: TOKENTYPE_AMP_GREATER_GREATER, value: three, pos: start)
    end
    if two == "&&"
      self.pos += 2
      return Token.new(type: TOKENTYPE_AND_AND, value: two, pos: start)
    end
    if two == "||"
      self.pos += 2
      return Token.new(type: TOKENTYPE_OR_OR, value: two, pos: start)
    end
    if two == ";;"
      self.pos += 2
      return Token.new(type: TOKENTYPE_SEMI_SEMI, value: two, pos: start)
    end
    if two == ";&"
      self.pos += 2
      return Token.new(type: TOKENTYPE_SEMI_AMP, value: two, pos: start)
    end
    if two == "<<"
      self.pos += 2
      return Token.new(type: TOKENTYPE_LESS_LESS, value: two, pos: start)
    end
    if two == ">>"
      self.pos += 2
      return Token.new(type: TOKENTYPE_GREATER_GREATER, value: two, pos: start)
    end
    if two == "<&"
      self.pos += 2
      return Token.new(type: TOKENTYPE_LESS_AMP, value: two, pos: start)
    end
    if two == ">&"
      self.pos += 2
      return Token.new(type: TOKENTYPE_GREATER_AMP, value: two, pos: start)
    end
    if two == "<>"
      self.pos += 2
      return Token.new(type: TOKENTYPE_LESS_GREATER, value: two, pos: start)
    end
    if two == ">|"
      self.pos += 2
      return Token.new(type: TOKENTYPE_GREATER_PIPE, value: two, pos: start)
    end
    if two == "&>"
      self.pos += 2
      return Token.new(type: TOKENTYPE_AMP_GREATER, value: two, pos: start)
    end
    if two == "|&"
      self.pos += 2
      return Token.new(type: TOKENTYPE_PIPE_AMP, value: two, pos: start)
    end
    if c == ";"
      self.pos += 1
      return Token.new(type: TOKENTYPE_SEMI, value: c, pos: start)
    end
    if c == "|"
      self.pos += 1
      return Token.new(type: TOKENTYPE_PIPE, value: c, pos: start)
    end
    if c == "&"
      self.pos += 1
      return Token.new(type: TOKENTYPE_AMP, value: c, pos: start)
    end
    if c == "("
      if self.word_context == WORD_CTX_REGEX
        return nil
      end
      self.pos += 1
      return Token.new(type: TOKENTYPE_LPAREN, value: c, pos: start)
    end
    if c == ")"
      if self.word_context == WORD_CTX_REGEX
        return nil
      end
      self.pos += 1
      return Token.new(type: TOKENTYPE_RPAREN, value: c, pos: start)
    end
    if c == "<"
      if self.pos + 1 < self.length && self.source[self.pos + 1] == "("
        return nil
      end
      self.pos += 1
      return Token.new(type: TOKENTYPE_LESS, value: c, pos: start)
    end
    if c == ">"
      if self.pos + 1 < self.length && self.source[self.pos + 1] == "("
        return nil
      end
      self.pos += 1
      return Token.new(type: TOKENTYPE_GREATER, value: c, pos: start)
    end
    if c == "\n"
      self.pos += 1
      return Token.new(type: TOKENTYPE_NEWLINE, value: c, pos: start)
    end
    return nil
  end

  def skip_blanks()
    while self.pos < self.length
      c = self.source[self.pos]
      if c != " " && c != "\t"
        break
      end
      self.pos += 1
    end
  end

  def skip_comment()
    if self.pos >= self.length
      return false
    end
    if self.source[self.pos] != "#"
      return false
    end
    if self.quote.in_quotes
      return false
    end
    if self.pos > 0
      prev = self.source[self.pos - 1]
      if !" \t\n;|&(){}".include?(prev)
        return false
      end
    end
    while self.pos < self.length && self.source[self.pos] != "\n"
      self.pos += 1
    end
    return true
  end

  def read_single_quote(start)
    chars = ["'"]
    saw_newline = false
    while self.pos < self.length
      c = self.source[self.pos]
      if c == "\n"
        saw_newline = true
      end
      chars.push(c)
      self.pos += 1
      if c == "'"
        return [chars.join, saw_newline]
      end
    end
    raise ParseError.new(message: "Unterminated single quote", pos: start)
  end

  def is_word_terminator(ctx, ch, bracket_depth = 0, paren_depth = 0)
    if ctx == WORD_CTX_REGEX
      if ch == "]" && self.pos + 1 < self.length && self.source[self.pos + 1] == "]"
        return true
      end
      if ch == "&" && self.pos + 1 < self.length && self.source[self.pos + 1] == "&"
        return true
      end
      if ch == ")" && paren_depth == 0
        return true
      end
      return is_whitespace(ch) && paren_depth == 0
    end
    if ctx == WORD_CTX_COND
      if ch == "]" && self.pos + 1 < self.length && self.source[self.pos + 1] == "]"
        return true
      end
      if ch == ")"
        return true
      end
      if ch == "&"
        return true
      end
      if ch == "|"
        return true
      end
      if ch == ";"
        return true
      end
      if is_redirect_char(ch) && !(self.pos + 1 < self.length && self.source[self.pos + 1] == "(")
        return true
      end
      return is_whitespace(ch)
    end
    if (self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN) != 0 && self.eof_token != "" && ch == self.eof_token && bracket_depth == 0
      return true
    end
    if is_redirect_char(ch) && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
      return false
    end
    return is_metachar(ch) && bracket_depth == 0
  end

  def read_bracket_expression(chars, parts, for_regex = false, paren_depth = 0)
    if for_regex
      scan = self.pos + 1
      if scan < self.length && self.source[scan] == "^"
        scan += 1
      end
      if scan < self.length && self.source[scan] == "]"
        scan += 1
      end
      bracket_will_close = false
      while scan < self.length
        sc = self.source[scan]
        if sc == "]" && scan + 1 < self.length && self.source[scan + 1] == "]"
          break
        end
        if sc == ")" && paren_depth > 0
          break
        end
        if sc == "&" && scan + 1 < self.length && self.source[scan + 1] == "&"
          break
        end
        if sc == "]"
          bracket_will_close = true
          break
        end
        if sc == "[" && scan + 1 < self.length && self.source[scan + 1] == ":"
          scan += 2
          while scan < self.length && !(self.source[scan] == ":" && scan + 1 < self.length && self.source[scan + 1] == "]")
            scan += 1
          end
          if scan < self.length
            scan += 2
          end
          next
        end
        scan += 1
      end
      if !bracket_will_close
        return false
      end
    else
      if self.pos + 1 >= self.length
        return false
      end
      next_ch = self.source[self.pos + 1]
      if is_whitespace_no_newline(next_ch) || next_ch == "&" || next_ch == "|"
        return false
      end
    end
    chars.append(self.advance)
    if !self.at_end && self.peek == "^"
      chars.append(self.advance)
    end
    if !self.at_end && self.peek == "]"
      chars.append(self.advance)
    end
    while !self.at_end
      c = self.peek
      if c == "]"
        chars.append(self.advance)
        break
      end
      if c == "[" && self.pos + 1 < self.length && self.source[self.pos + 1] == ":"
        chars.append(self.advance)
        chars.append(self.advance)
        while !self.at_end && !(self.peek == ":" && self.pos + 1 < self.length && self.source[self.pos + 1] == "]")
          chars.append(self.advance)
        end
        if !self.at_end
          chars.append(self.advance)
          chars.append(self.advance)
        end
      elsif !for_regex && c == "[" && self.pos + 1 < self.length && self.source[self.pos + 1] == "="
        chars.append(self.advance)
        chars.append(self.advance)
        while !self.at_end && !(self.peek == "=" && self.pos + 1 < self.length && self.source[self.pos + 1] == "]")
          chars.append(self.advance)
        end
        if !self.at_end
          chars.append(self.advance)
          chars.append(self.advance)
        end
      elsif !for_regex && c == "[" && self.pos + 1 < self.length && self.source[self.pos + 1] == "."
        chars.append(self.advance)
        chars.append(self.advance)
        while !self.at_end && !(self.peek == "." && self.pos + 1 < self.length && self.source[self.pos + 1] == "]")
          chars.append(self.advance)
        end
        if !self.at_end
          chars.append(self.advance)
          chars.append(self.advance)
        end
      elsif for_regex && c == "$"
        self.sync_to_parser
        if !self.parser.parse_dollar_expansion(chars, parts, false)
          self.sync_from_parser
          chars.append(self.advance)
        else
          self.sync_from_parser
        end
      else
        chars.append(self.advance)
      end
    end
    return true
  end

  def parse_matched_pair(open_char, close_char, flags = 0, initial_was_dollar = false)
    start = self.pos
    count = 1
    chars = []
    pass_next = false
    was_dollar = initial_was_dollar
    was_gtlt = false
    while count > 0
      if self.at_end
        raise MatchedPairError.new(message: "unexpected EOF while looking for matching `#{close_char}'", pos: start)
      end
      ch = self.advance
      if (flags & MATCHEDPAIRFLAGS_DOLBRACE) != 0 && self.dolbrace_state == DOLBRACESTATE_OP
        if !"#%^,~:-=?+/".include?(ch)
          self.dolbrace_state = DOLBRACESTATE_WORD
        end
      end
      if pass_next
        pass_next = false
        chars.push(ch)
        was_dollar = ch == "$"
        was_gtlt = "<>".include?(ch)
        next
      end
      if open_char == "'"
        if ch == close_char
          count -= 1
          if count == 0
            break
          end
        end
        if ch == "\\" && (flags & MATCHEDPAIRFLAGS_ALLOWESC) != 0
          pass_next = true
        end
        chars.push(ch)
        was_dollar = false
        was_gtlt = false
        next
      end
      if ch == "\\"
        if !self.at_end && self.peek == "\n"
          self.advance
          was_dollar = false
          was_gtlt = false
          next
        end
        pass_next = true
        chars.push(ch)
        was_dollar = false
        was_gtlt = false
        next
      end
      if ch == close_char
        count -= 1
        if count == 0
          break
        end
        chars.push(ch)
        was_dollar = false
        was_gtlt = "<>".include?(ch)
        next
      end
      if ch == open_char && open_char != close_char
        if !((flags & MATCHEDPAIRFLAGS_DOLBRACE) != 0 && open_char == "{")
          count += 1
        end
        chars.push(ch)
        was_dollar = false
        was_gtlt = "<>".include?(ch)
        next
      end
      if ("'\"`".include?(ch)) && open_char != close_char
        if ch == "'"
          chars.push(ch)
          quote_flags = was_dollar ? flags | MATCHEDPAIRFLAGS_ALLOWESC : flags
          nested = self.parse_matched_pair("'", "'", quote_flags, false)
          chars.push(nested)
          chars.push("'")
          was_dollar = false
          was_gtlt = false
          next
        elsif ch == "\""
          chars.push(ch)
          nested = self.parse_matched_pair("\"", "\"", flags | MATCHEDPAIRFLAGS_DQUOTE, false)
          chars.push(nested)
          chars.push("\"")
          was_dollar = false
          was_gtlt = false
          next
        elsif ch == "`"
          chars.push(ch)
          nested = self.parse_matched_pair("`", "`", flags, false)
          chars.push(nested)
          chars.push("`")
          was_dollar = false
          was_gtlt = false
          next
        end
      end
      if ch == "$" && !self.at_end && (flags & MATCHEDPAIRFLAGS_EXTGLOB) == 0
        next_ch = self.peek
        if was_dollar
          chars.push(ch)
          was_dollar = false
          was_gtlt = false
          next
        end
        if next_ch == "{"
          if (flags & MATCHEDPAIRFLAGS_ARITH) != 0
            after_brace_pos = self.pos + 1
            if after_brace_pos >= self.length || !is_funsub_char(self.source[after_brace_pos])
              chars.push(ch)
              was_dollar = true
              was_gtlt = false
              next
            end
          end
          self.pos -= 1
          self.sync_to_parser
          in_dquote = (flags & MATCHEDPAIRFLAGS_DQUOTE) != 0
          param_node, param_text = self.parser.parse_param_expansion(in_dquote)
          self.sync_from_parser
          if !param_node.nil?
            chars.push(param_text)
            was_dollar = false
            was_gtlt = false
          else
            chars.push(self.advance)
            was_dollar = true
            was_gtlt = false
          end
          next
        elsif next_ch == "("
          self.pos -= 1
          self.sync_to_parser
          if self.pos + 2 < self.length && self.source[self.pos + 2] == "("
            arith_node, arith_text = self.parser.parse_arithmetic_expansion
            self.sync_from_parser
            if !arith_node.nil?
              chars.push(arith_text)
              was_dollar = false
              was_gtlt = false
            else
              self.sync_to_parser
              cmd_node, cmd_text = self.parser.parse_command_substitution
              self.sync_from_parser
              if !cmd_node.nil?
                chars.push(cmd_text)
                was_dollar = false
                was_gtlt = false
              else
                chars.push(self.advance)
                chars.push(self.advance)
                was_dollar = false
                was_gtlt = false
              end
            end
          else
            cmd_node, cmd_text = self.parser.parse_command_substitution
            self.sync_from_parser
            if !cmd_node.nil?
              chars.push(cmd_text)
              was_dollar = false
              was_gtlt = false
            else
              chars.push(self.advance)
              chars.push(self.advance)
              was_dollar = false
              was_gtlt = false
            end
          end
          next
        elsif next_ch == "["
          self.pos -= 1
          self.sync_to_parser
          arith_node, arith_text = self.parser.parse_deprecated_arithmetic
          self.sync_from_parser
          if !arith_node.nil?
            chars.push(arith_text)
            was_dollar = false
            was_gtlt = false
          else
            chars.push(self.advance)
            was_dollar = true
            was_gtlt = false
          end
          next
        end
      end
      if ch == "(" && was_gtlt && (flags & MATCHEDPAIRFLAGS_DOLBRACE | MATCHEDPAIRFLAGS_ARRAYSUB) != 0
        direction = chars[-1]
        chars = chars[0...-1]
        self.pos -= 1
        self.sync_to_parser
        procsub_node, procsub_text = self.parser.parse_process_substitution
        self.sync_from_parser
        if !procsub_node.nil?
          chars.push(procsub_text)
          was_dollar = false
          was_gtlt = false
        else
          chars.push(direction)
          chars.push(self.advance)
          was_dollar = false
          was_gtlt = false
        end
        next
      end
      chars.push(ch)
      was_dollar = ch == "$"
      was_gtlt = "<>".include?(ch)
    end
    return chars.join
  end

  def collect_param_argument(flags = matched_pair_flags.none, was_dollar = false)
    return self.parse_matched_pair("{", "}", flags | MATCHEDPAIRFLAGS_DOLBRACE, was_dollar)
  end

  def read_word_internal(ctx, at_command_start = false, in_array_literal = false, in_assign_builtin = false)
    start = self.pos
    chars = []
    parts = []
    bracket_depth = 0
    bracket_start_pos = -1
    seen_equals = false
    paren_depth = 0
    while !self.at_end
      ch = self.peek
      if ctx == WORD_CTX_REGEX
        if ch == "\\" && self.pos + 1 < self.length && self.source[self.pos + 1] == "\n"
          self.advance
          self.advance
          next
        end
      end
      if ctx != WORD_CTX_NORMAL && self.is_word_terminator(ctx, ch, bracket_depth, paren_depth)
        break
      end
      if ctx == WORD_CTX_NORMAL && ch == "["
        if bracket_depth > 0
          bracket_depth += 1
          chars.push(self.advance)
          next
        end
        if (chars && !chars.empty?) && at_command_start && !seen_equals && is_array_assignment_prefix(chars)
          prev_char = chars[-1]
          if (prev_char).match?(/\A[[:alnum:]]+\z/) || prev_char == "_"
            bracket_start_pos = self.pos
            bracket_depth += 1
            chars.push(self.advance)
            next
          end
        end
        if !(chars && !chars.empty?) && !seen_equals && in_array_literal
          bracket_start_pos = self.pos
          bracket_depth += 1
          chars.push(self.advance)
          next
        end
      end
      if ctx == WORD_CTX_NORMAL && ch == "]" && bracket_depth > 0
        bracket_depth -= 1
        chars.push(self.advance)
        next
      end
      if ctx == WORD_CTX_NORMAL && ch == "=" && bracket_depth == 0
        seen_equals = true
      end
      if ctx == WORD_CTX_REGEX && ch == "("
        paren_depth += 1
        chars.push(self.advance)
        next
      end
      if ctx == WORD_CTX_REGEX && ch == ")"
        if paren_depth > 0
          paren_depth -= 1
          chars.push(self.advance)
          next
        end
        break
      end
      if (ctx == WORD_CTX_COND || ctx == WORD_CTX_REGEX) && ch == "["
        for_regex = ctx == WORD_CTX_REGEX
        if self.read_bracket_expression(chars, parts, for_regex, paren_depth)
          next
        end
        chars.push(self.advance)
        next
      end
      if ctx == WORD_CTX_COND && ch == "("
        if self.extglob && (chars && !chars.empty?) && is_extglob_prefix(chars[-1])
          chars.push(self.advance)
          content = self.parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false)
          chars.push(content)
          chars.push(")")
          next
        else
          break
        end
      end
      if ctx == WORD_CTX_REGEX && is_whitespace(ch) && paren_depth > 0
        chars.push(self.advance)
        next
      end
      if ch == "'"
        self.advance
        track_newline = ctx == WORD_CTX_NORMAL
        content, saw_newline = self.read_single_quote(start)
        chars.push(content)
        if track_newline && saw_newline && !self.parser.nil?
          self.parser.saw_newline_in_single_quote = true
        end
        next
      end
      if ch == "\""
        self.advance
        if ctx == WORD_CTX_NORMAL
          chars.push("\"")
          in_single_in_dquote = false
          while !self.at_end && (in_single_in_dquote || self.peek != "\"")
            c = self.peek
            if in_single_in_dquote
              chars.push(self.advance)
              if c == "'"
                in_single_in_dquote = false
              end
              next
            end
            if c == "\\" && self.pos + 1 < self.length
              next_c = self.source[self.pos + 1]
              if next_c == "\n"
                self.advance
                self.advance
              else
                chars.push(self.advance)
                chars.push(self.advance)
              end
            elsif c == "$"
              self.sync_to_parser
              if !self.parser.parse_dollar_expansion(chars, parts, true)
                self.sync_from_parser
                chars.push(self.advance)
              else
                self.sync_from_parser
              end
            elsif c == "`"
              self.sync_to_parser
              cmdsub_result0, cmdsub_result1 = self.parser.parse_backtick_substitution
              self.sync_from_parser
              if !cmdsub_result0.nil?
                parts.push(cmdsub_result0)
                chars.push(cmdsub_result1)
              else
                chars.push(self.advance)
              end
            else
              chars.push(self.advance)
            end
          end
          if self.at_end
            raise ParseError.new(message: "Unterminated double quote", pos: start)
          end
          chars.push(self.advance)
        else
          handle_line_continuation = ctx == WORD_CTX_COND
          self.sync_to_parser
          self.parser.scan_double_quote(chars, parts, start, handle_line_continuation)
          self.sync_from_parser
        end
        next
      end
      if ch == "\\" && self.pos + 1 < self.length
        next_ch = self.source[self.pos + 1]
        if ctx != WORD_CTX_REGEX && next_ch == "\n"
          self.advance
          self.advance
        else
          chars.push(self.advance)
          chars.push(self.advance)
        end
        next
      end
      if ctx != WORD_CTX_REGEX && ch == "$" && self.pos + 1 < self.length && self.source[self.pos + 1] == "'"
        ansi_result0, ansi_result1 = self.read_ansi_c_quote
        if !ansi_result0.nil?
          parts.push(ansi_result0)
          chars.push(ansi_result1)
        else
          chars.push(self.advance)
        end
        next
      end
      if ctx != WORD_CTX_REGEX && ch == "$" && self.pos + 1 < self.length && self.source[self.pos + 1] == "\""
        locale_result0, locale_result1, locale_result2 = self.read_locale_string
        if !locale_result0.nil?
          parts.push(locale_result0)
          parts.concat(locale_result2)
          chars.push(locale_result1)
        else
          chars.push(self.advance)
        end
        next
      end
      if ch == "$"
        self.sync_to_parser
        if !self.parser.parse_dollar_expansion(chars, parts, false)
          self.sync_from_parser
          chars.push(self.advance)
        else
          self.sync_from_parser
          if self.extglob && ctx == WORD_CTX_NORMAL && (chars && !chars.empty?) && chars[-1].length == 2 && chars[-1][0] == "$" && ("?*@".include?(chars[-1][1])) && !self.at_end && self.peek == "("
            chars.push(self.advance)
            content = self.parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false)
            chars.push(content)
            chars.push(")")
          end
        end
        next
      end
      if ctx != WORD_CTX_REGEX && ch == "`"
        self.sync_to_parser
        cmdsub_result0, cmdsub_result1 = self.parser.parse_backtick_substitution
        self.sync_from_parser
        if !cmdsub_result0.nil?
          parts.push(cmdsub_result0)
          chars.push(cmdsub_result1)
        else
          chars.push(self.advance)
        end
        next
      end
      if ctx != WORD_CTX_REGEX && is_redirect_char(ch) && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
        self.sync_to_parser
        procsub_result0, procsub_result1 = self.parser.parse_process_substitution
        self.sync_from_parser
        if !procsub_result0.nil?
          parts.push(procsub_result0)
          chars.push(procsub_result1)
        elsif (procsub_result1 && !procsub_result1.empty?)
          chars.push(procsub_result1)
        else
          chars.push(self.advance)
          if ctx == WORD_CTX_NORMAL
            chars.push(self.advance)
          end
        end
        next
      end
      if ctx == WORD_CTX_NORMAL && ch == "(" && (chars && !chars.empty?) && bracket_depth == 0
        is_array_assign = false
        if chars.length >= 3 && chars[-2] == "+" && chars[-1] == "="
          is_array_assign = is_array_assignment_prefix(chars[0...-2])
        elsif chars[-1] == "=" && chars.length >= 2
          is_array_assign = is_array_assignment_prefix(chars[0...-1])
        end
        if is_array_assign && (at_command_start || in_assign_builtin)
          self.sync_to_parser
          array_result0, array_result1 = self.parser.parse_array_literal
          self.sync_from_parser
          if !array_result0.nil?
            parts.push(array_result0)
            chars.push(array_result1)
          else
            break
          end
          next
        end
      end
      if self.extglob && ctx == WORD_CTX_NORMAL && is_extglob_prefix(ch) && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
        chars.push(self.advance)
        chars.push(self.advance)
        content = self.parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false)
        chars.push(content)
        chars.push(")")
        next
      end
      if ctx == WORD_CTX_NORMAL && (self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN) != 0 && self.eof_token != "" && ch == self.eof_token && bracket_depth == 0
        if !(chars && !chars.empty?)
          chars.push(self.advance)
        end
        break
      end
      if ctx == WORD_CTX_NORMAL && is_metachar(ch) && bracket_depth == 0
        break
      end
      chars.push(self.advance)
    end
    if bracket_depth > 0 && bracket_start_pos != -1 && self.at_end
      raise MatchedPairError.new(message: "unexpected EOF looking for `]'", pos: bracket_start_pos)
    end
    if !(chars && !chars.empty?)
      return nil
    end
    if (parts && !parts.empty?)
      return Word.new(value: chars.join, parts: parts, kind: "word")
    end
    return Word.new(value: chars.join, kind: "word")
  end

  def read_word()
    start = self.pos
    if self.pos >= self.length
      return nil
    end
    c = self.peek
    if c == ""
      return nil
    end
    is_procsub = (c == "<" || c == ">") && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
    is_regex_paren = self.word_context == WORD_CTX_REGEX && (c == "(" || c == ")")
    if self.is_metachar(c) && !is_procsub && !is_regex_paren
      return nil
    end
    word = self.read_word_internal(self.word_context, self.at_command_start, self.in_array_literal, self.in_assign_builtin)
    if word.nil?
      return nil
    end
    return Token.new(type: TOKENTYPE_WORD, value: word.value, pos: start, word: word)
  end

  def next_token()
    if !self.token_cache.nil?
      tok = self.token_cache
      self.token_cache = nil
      self.last_read_token = tok
      return tok
    end
    self.skip_blanks
    if self.at_end
      tok = Token.new(type: TOKENTYPE_EOF, value: "", pos: self.pos)
      self.last_read_token = tok
      return tok
    end
    if self.eof_token != "" && self.peek == self.eof_token && (self.parser_state & PARSERSTATEFLAGS_PST_CASEPAT) == 0 && (self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN) == 0
      tok = Token.new(type: TOKENTYPE_EOF, value: "", pos: self.pos)
      self.last_read_token = tok
      return tok
    end
    while self.skip_comment
      self.skip_blanks
      if self.at_end
        tok = Token.new(type: TOKENTYPE_EOF, value: "", pos: self.pos)
        self.last_read_token = tok
        return tok
      end
      if self.eof_token != "" && self.peek == self.eof_token && (self.parser_state & PARSERSTATEFLAGS_PST_CASEPAT) == 0 && (self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN) == 0
        tok = Token.new(type: TOKENTYPE_EOF, value: "", pos: self.pos)
        self.last_read_token = tok
        return tok
      end
    end
    tok = self.read_operator
    if !tok.nil?
      self.last_read_token = tok
      return tok
    end
    tok = self.read_word
    if !tok.nil?
      self.last_read_token = tok
      return tok
    end
    tok = Token.new(type: TOKENTYPE_EOF, value: "", pos: self.pos)
    self.last_read_token = tok
    return tok
  end

  def peek_token()
    if self.token_cache.nil?
      saved_last = self.last_read_token
      self.token_cache = self.next_token
      self.last_read_token = saved_last
    end
    return self.token_cache
  end

  def read_ansi_c_quote()
    if self.at_end || self.peek != "$"
      return [nil, ""]
    end
    if self.pos + 1 >= self.length || self.source[self.pos + 1] != "'"
      return [nil, ""]
    end
    start = self.pos
    self.advance
    self.advance
    content_chars = []
    found_close = false
    while !self.at_end
      ch = self.peek
      if ch == "'"
        self.advance
        found_close = true
        break
      elsif ch == "\\"
        content_chars.push(self.advance)
        if !self.at_end
          content_chars.push(self.advance)
        end
      else
        content_chars.push(self.advance)
      end
    end
    if !found_close
      raise MatchedPairError.new(message: "unexpected EOF while looking for matching `''", pos: start)
    end
    text = substring(self.source, start, self.pos)
    content = content_chars.join
    node = AnsiCQuote.new(content: content, kind: "ansi-c")
    return [node, text]
  end

  def sync_to_parser()
    if !self.parser.nil?
      self.parser.pos = self.pos
    end
  end

  def sync_from_parser()
    if !self.parser.nil?
      self.pos = self.parser.pos
    end
  end

  def read_locale_string()
    if self.at_end || self.peek != "$"
      return [nil, "", []]
    end
    if self.pos + 1 >= self.length || self.source[self.pos + 1] != "\""
      return [nil, "", []]
    end
    start = self.pos
    self.advance
    self.advance
    content_chars = []
    inner_parts = []
    found_close = false
    while !self.at_end
      ch = self.peek
      if ch == "\""
        self.advance
        found_close = true
        break
      elsif ch == "\\" && self.pos + 1 < self.length
        next_ch = self.source[self.pos + 1]
        if next_ch == "\n"
          self.advance
          self.advance
        else
          content_chars.push(self.advance)
          content_chars.push(self.advance)
        end
      elsif ch == "$" && self.pos + 2 < self.length && self.source[self.pos + 1] == "(" && self.source[self.pos + 2] == "("
        self.sync_to_parser
        arith_node, arith_text = self.parser.parse_arithmetic_expansion
        self.sync_from_parser
        if !arith_node.nil?
          inner_parts.push(arith_node)
          content_chars.push(arith_text)
        else
          self.sync_to_parser
          cmdsub_node, cmdsub_text = self.parser.parse_command_substitution
          self.sync_from_parser
          if !cmdsub_node.nil?
            inner_parts.push(cmdsub_node)
            content_chars.push(cmdsub_text)
          else
            content_chars.push(self.advance)
          end
        end
      elsif is_expansion_start(self.source, self.pos, "$(")
        self.sync_to_parser
        cmdsub_node, cmdsub_text = self.parser.parse_command_substitution
        self.sync_from_parser
        if !cmdsub_node.nil?
          inner_parts.push(cmdsub_node)
          content_chars.push(cmdsub_text)
        else
          content_chars.push(self.advance)
        end
      elsif ch == "$"
        self.sync_to_parser
        param_node, param_text = self.parser.parse_param_expansion(false)
        self.sync_from_parser
        if !param_node.nil?
          inner_parts.push(param_node)
          content_chars.push(param_text)
        else
          content_chars.push(self.advance)
        end
      elsif ch == "`"
        self.sync_to_parser
        cmdsub_node, cmdsub_text = self.parser.parse_backtick_substitution
        self.sync_from_parser
        if !cmdsub_node.nil?
          inner_parts.push(cmdsub_node)
          content_chars.push(cmdsub_text)
        else
          content_chars.push(self.advance)
        end
      else
        content_chars.push(self.advance)
      end
    end
    if !found_close
      self.pos = start
      return [nil, "", []]
    end
    content = content_chars.join
    text = "$\"" + content + "\""
    return [LocaleString.new(content: content, kind: "locale"), text, inner_parts]
  end

  def update_dolbrace_for_op(op, has_param)
    if self.dolbrace_state == DOLBRACESTATE_NONE
      return
    end
    if op == "" || op.length == 0
      return
    end
    first_char = op[0]
    if self.dolbrace_state == DOLBRACESTATE_PARAM && has_param
      if "%#^,".include?(first_char)
        self.dolbrace_state = DOLBRACESTATE_QUOTE
        return
      end
      if first_char == "/"
        self.dolbrace_state = DOLBRACESTATE_QUOTE2
        return
      end
    end
    if self.dolbrace_state == DOLBRACESTATE_PARAM
      if "#%^,~:-=?+/".include?(first_char)
        self.dolbrace_state = DOLBRACESTATE_OP
      end
    end
  end

  def consume_param_operator()
    if self.at_end
      return ""
    end
    ch = self.peek
    if ch == ":"
      self.advance
      if self.at_end
        return ":"
      end
      next_ch = self.peek
      if is_simple_param_op(next_ch)
        self.advance
        return ":" + next_ch
      end
      return ":"
    end
    if is_simple_param_op(ch)
      self.advance
      return ch
    end
    if ch == "#"
      self.advance
      if !self.at_end && self.peek == "#"
        self.advance
        return "##"
      end
      return "#"
    end
    if ch == "%"
      self.advance
      if !self.at_end && self.peek == "%"
        self.advance
        return "%%"
      end
      return "%"
    end
    if ch == "/"
      self.advance
      if !self.at_end
        next_ch = self.peek
        if next_ch == "/"
          self.advance
          return "//"
        elsif next_ch == "#"
          self.advance
          return "/#"
        elsif next_ch == "%"
          self.advance
          return "/%"
        end
      end
      return "/"
    end
    if ch == "^"
      self.advance
      if !self.at_end && self.peek == "^"
        self.advance
        return "^^"
      end
      return "^"
    end
    if ch == ","
      self.advance
      if !self.at_end && self.peek == ","
        self.advance
        return ",,"
      end
      return ","
    end
    if ch == "@"
      self.advance
      return "@"
    end
    return ""
  end

  def param_subscript_has_close(start_pos)
    depth = 1
    i = start_pos + 1
    quote = new_quote_state()
    while i < self.length
      c = self.source[i]
      if quote.single
        if c == "'"
          quote.single = false
        end
        i += 1
        next
      end
      if quote.double
        if c == "\\" && i + 1 < self.length
          i += 2
          next
        end
        if c == "\""
          quote.double = false
        end
        i += 1
        next
      end
      if c == "'"
        quote.single = true
        i += 1
        next
      end
      if c == "\""
        quote.double = true
        i += 1
        next
      end
      if c == "\\"
        i += 2
        next
      end
      if c == "}"
        return false
      end
      if c == "["
        depth += 1
      elsif c == "]"
        depth -= 1
        if depth == 0
          return true
        end
      end
      i += 1
    end
    return false
  end

  def consume_param_name()
    if self.at_end
      return ""
    end
    ch = self.peek
    if is_special_param(ch)
      if ch == "$" && self.pos + 1 < self.length && ("{'\"".include?(self.source[self.pos + 1]))
        return ""
      end
      self.advance
      return ch
    end
    if (ch).match?(/\A\d+\z/)
      name_chars = []
      while !self.at_end && (self.peek).match?(/\A\d+\z/)
        name_chars.push(self.advance)
      end
      return name_chars.join
    end
    if (ch).match?(/\A[[:alpha:]]+\z/) || ch == "_"
      name_chars = []
      while !self.at_end
        c = self.peek
        if (c).match?(/\A[[:alnum:]]+\z/) || c == "_"
          name_chars.push(self.advance)
        elsif c == "["
          if !self.param_subscript_has_close(self.pos)
            break
          end
          name_chars.push(self.advance)
          content = self.parse_matched_pair("[", "]", MATCHEDPAIRFLAGS_ARRAYSUB, false)
          name_chars.push(content)
          name_chars.push("]")
          break
        else
          break
        end
      end
      if (name_chars && !name_chars.empty?)
        return name_chars.join
      else
        return ""
      end
    end
    return ""
  end

  def read_param_expansion(in_dquote = false)
    if self.at_end || self.peek != "$"
      return [nil, ""]
    end
    start = self.pos
    self.advance
    if self.at_end
      self.pos = start
      return [nil, ""]
    end
    ch = self.peek
    if ch == "{"
      self.advance
      return self.read_braced_param(start, in_dquote)
    end
    if is_special_param_unbraced(ch) || is_digit(ch) || ch == "#"
      self.advance
      text = substring(self.source, start, self.pos)
      return [ParamExpansion.new(param: ch, kind: "param"), text]
    end
    if (ch).match?(/\A[[:alpha:]]+\z/) || ch == "_"
      name_start = self.pos
      while !self.at_end
        c = self.peek
        if (c).match?(/\A[[:alnum:]]+\z/) || c == "_"
          self.advance
        else
          break
        end
      end
      name = substring(self.source, name_start, self.pos)
      text = substring(self.source, start, self.pos)
      return [ParamExpansion.new(param: name, kind: "param"), text]
    end
    self.pos = start
    return [nil, ""]
  end

  def read_braced_param(start, in_dquote = false)
    if self.at_end
      raise MatchedPairError.new(message: "unexpected EOF looking for `}'", pos: start)
    end
    saved_dolbrace = self.dolbrace_state
    self.dolbrace_state = DOLBRACESTATE_PARAM
    ch = self.peek
    if is_funsub_char(ch)
      self.dolbrace_state = saved_dolbrace
      return self.read_funsub(start)
    end
    if ch == "#"
      self.advance
      param = self.consume_param_name
      if (param && !param.empty?) && !self.at_end && self.peek == "}"
        self.advance
        text = substring(self.source, start, self.pos)
        self.dolbrace_state = saved_dolbrace
        return [ParamLength.new(param: param, kind: "param-len"), text]
      end
      self.pos = start + 2
    end
    if ch == "!"
      self.advance
      while !self.at_end && is_whitespace_no_newline(self.peek)
        self.advance
      end
      param = self.consume_param_name
      if (param && !param.empty?)
        while !self.at_end && is_whitespace_no_newline(self.peek)
          self.advance
        end
        if !self.at_end && self.peek == "}"
          self.advance
          text = substring(self.source, start, self.pos)
          self.dolbrace_state = saved_dolbrace
          return [ParamIndirect.new(param: param, kind: "param-indirect"), text]
        end
        if !self.at_end && is_at_or_star(self.peek)
          suffix = self.advance
          trailing = self.parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false)
          text = substring(self.source, start, self.pos)
          self.dolbrace_state = saved_dolbrace
          return [ParamIndirect.new(param: param + suffix + trailing, kind: "param-indirect"), text]
        end
        op = self.consume_param_operator
        if op == "" && !self.at_end && (!"}\"'`".include?(self.peek))
          op = self.advance
        end
        if op != "" && (!"\"'`".include?(op))
          arg = self.parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false)
          text = substring(self.source, start, self.pos)
          self.dolbrace_state = saved_dolbrace
          return [ParamIndirect.new(param: param, op: op, arg: arg, kind: "param-indirect"), text]
        end
        if self.at_end
          self.dolbrace_state = saved_dolbrace
          raise MatchedPairError.new(message: "unexpected EOF looking for `}'", pos: start)
        end
        self.pos = start + 2
      else
        self.pos = start + 2
      end
    end
    param = self.consume_param_name
    if !(param && !param.empty?)
      if !self.at_end && (("-=+?".include?(self.peek)) || self.peek == ":" && self.pos + 1 < self.length && is_simple_param_op(self.source[self.pos + 1]))
        param = ""
      else
        content = self.parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false)
        text = "${" + content + "}"
        self.dolbrace_state = saved_dolbrace
        return [ParamExpansion.new(param: content, kind: "param"), text]
      end
    end
    if self.at_end
      self.dolbrace_state = saved_dolbrace
      raise MatchedPairError.new(message: "unexpected EOF looking for `}'", pos: start)
    end
    if self.peek == "}"
      self.advance
      text = substring(self.source, start, self.pos)
      self.dolbrace_state = saved_dolbrace
      return [ParamExpansion.new(param: param, kind: "param"), text]
    end
    op = self.consume_param_operator
    if op == ""
      if !self.at_end && self.peek == "$" && self.pos + 1 < self.length && (self.source[self.pos + 1] == "\"" || self.source[self.pos + 1] == "'")
        dollar_count = 1 + count_consecutive_dollars_before(self.source, self.pos)
        if dollar_count % 2 == 1
          op = ""
        else
          op = self.advance
        end
      elsif !self.at_end && self.peek == "`"
        backtick_pos = self.pos
        self.advance
        while !self.at_end && self.peek != "`"
          bc = self.peek
          if bc == "\\" && self.pos + 1 < self.length
            next_c = self.source[self.pos + 1]
            if is_escape_char_in_backtick(next_c)
              self.advance
            end
          end
          self.advance
        end
        if self.at_end
          self.dolbrace_state = saved_dolbrace
          raise ParseError.new(message: "Unterminated backtick", pos: backtick_pos)
        end
        self.advance
        op = "`"
      elsif !self.at_end && self.peek == "$" && self.pos + 1 < self.length && self.source[self.pos + 1] == "{"
        op = ""
      elsif !self.at_end && (self.peek == "'" || self.peek == "\"")
        op = ""
      elsif !self.at_end && self.peek == "\\"
        op = self.advance
        if !self.at_end
          op += self.advance
        end
      else
        op = self.advance
      end
    end
    self.update_dolbrace_for_op(op, param.length > 0)
    begin
      flags = in_dquote ? MATCHEDPAIRFLAGS_DQUOTE : MATCHEDPAIRFLAGS_NONE
      param_ends_with_dollar = param != "" && param.end_with?("$")
      arg = self.collect_param_argument(flags, param_ends_with_dollar)
    rescue MatchedPairError => e
      self.dolbrace_state = saved_dolbrace
      raise e
    end
    if (op == "<" || op == ">") && arg.start_with?("(") && arg.end_with?(")")
      inner = arg[1...-1]
      begin
        sub_parser = new_parser(inner, true, self.parser.extglob)
        parsed = sub_parser.parse_list(true)
        if !parsed.nil? && sub_parser.at_end
          formatted = format_cmdsub_node(parsed, 0, true, false, true)
          arg = "(" + formatted + ")"
        end
      rescue Exception_ => _e
        nil
      end
    end
    text = "${" + param + op + arg + "}"
    self.dolbrace_state = saved_dolbrace
    return [ParamExpansion.new(param: param, op: op, arg: arg, kind: "param"), text]
  end

  def read_funsub(start)
    return self.parser.parse_funsub(start)
  end
end

class Word
  attr_accessor :value, :parts, :kind

  def initialize(value: "", parts: [], kind: "")
    @value = value
    @parts = parts
    @kind = kind
  end

  def to_sexp()
    value = self.value
    value = self.expand_all_ansi_c_quotes(value)
    value = self.strip_locale_string_dollars(value)
    value = self.normalize_array_whitespace(value)
    value = self.format_command_substitutions(value, false)
    value = self.normalize_param_expansion_newlines(value)
    value = self.strip_arith_line_continuations(value)
    value = self.double_ctlesc_smart(value)
    value = value.gsub("\u007f", "\u0001\u007f")
    value = value.gsub("\\") { "\\\\" }
    if value.end_with?("\\\\") && !value.end_with?("\\\\\\\\")
      value = value + "\\\\"
    end
    escaped = value.gsub("\"") { "\\\"" }.gsub("
") { "\\n" }.gsub("	") { "\\t" }
    return "(word \"" + escaped + "\")"
  end

  def append_with_ctlesc(result, byte_val)
    result.append(byte_val)
  end

  def double_ctlesc_smart(value)
    result = []
    quote = new_quote_state()
    value.each_char do |c|
      if c == "'" && !quote.double
        quote.single = !quote.single
      elsif c == "\"" && !quote.single
        quote.double = !quote.double
      end
      result.push(c)
      if c == "\u0001"
        if quote.double
          bs_count = 0
          j = result.length - 2
          while j > -1
            if result[j] == "\\"
              bs_count += 1
            else
              break
            end
            j += -1
          end
          if bs_count % 2 == 0
            result.push("\u0001")
          end
        else
          result.push("\u0001")
        end
      end
    end
    return result.join
  end

  def normalize_param_expansion_newlines(value)
    result = []
    i = 0
    quote = new_quote_state()
    while i < value.length
      c = value[i]
      if c == "'" && !quote.double
        quote.single = !quote.single
        result.push(c)
        i += 1
      elsif c == "\"" && !quote.single
        quote.double = !quote.double
        result.push(c)
        i += 1
      elsif is_expansion_start(value, i, "${") && !quote.single
        result.push("$")
        result.push("{")
        i += 2
        had_leading_newline = i < value.length && value[i] == "\n"
        if had_leading_newline
          result.push(" ")
          i += 1
        end
        depth = 1
        while i < value.length && depth > 0
          ch = value[i]
          if ch == "\\" && i + 1 < value.length && !quote.single
            if value[i + 1] == "\n"
              i += 2
              next
            end
            result.push(ch)
            result.push(value[i + 1])
            i += 2
            next
          end
          if ch == "'" && !quote.double
            quote.single = !quote.single
          elsif ch == "\"" && !quote.single
            quote.double = !quote.double
          elsif !quote.in_quotes
            if ch == "{"
              depth += 1
            elsif ch == "}"
              depth -= 1
              if depth == 0
                if had_leading_newline
                  result.push(" ")
                end
                result.push(ch)
                i += 1
                break
              end
            end
          end
          result.push(ch)
          i += 1
        end
      else
        result.push(c)
        i += 1
      end
    end
    return result.join
  end

  def sh_single_quote(s)
    if !(s && !s.empty?)
      return "''"
    end
    if s == "'"
      return "\\'"
    end
    result = ["'"]
    s.each_char do |c|
      if c == "'"
        result.push("'\\''")
      else
        result.push(c)
      end
    end
    result.push("'")
    return result.join
  end

  def ansi_c_to_bytes(inner)
    result = []
    i = 0
    while i < inner.length
      if inner[i] == "\\" && i + 1 < inner.length
        c = inner[i + 1]
        simple = get_ansi_escape(c)
        if simple >= 0
          result.push(simple)
          i += 2
        elsif c == "'"
          result.push(39)
          i += 2
        elsif c == "x"
          if i + 2 < inner.length && inner[i + 2] == "{"
            j = i + 3
            while j < inner.length && is_hex_digit(inner[j])
              j += 1
            end
            hex_str = substring(inner, i + 3, j)
            if j < inner.length && inner[j] == "}"
              j += 1
            end
            if !(hex_str && !hex_str.empty?)
              return result
            end
            byte_val = hex_str.to_i(16) & 255
            if byte_val == 0
              return result
            end
            self.append_with_ctlesc(result, byte_val)
            i = j
          else
            j = i + 2
            while j < inner.length && j < i + 4 && is_hex_digit(inner[j])
              j += 1
            end
            if j > i + 2
              byte_val = substring(inner, i + 2, j).to_i(16)
              if byte_val == 0
                return result
              end
              self.append_with_ctlesc(result, byte_val)
              i = j
            else
              result.push(inner[i][0].ord)
              i += 1
            end
          end
        elsif c == "u"
          j = i + 2
          while j < inner.length && j < i + 6 && is_hex_digit(inner[j])
            j += 1
          end
          if j > i + 2
            codepoint = substring(inner, i + 2, j).to_i(16)
            if codepoint == 0
              return result
            end
            result.concat([codepoint].pack('U').bytes)
            i = j
          else
            result.push(inner[i][0].ord)
            i += 1
          end
        elsif c == "U"
          j = i + 2
          while j < inner.length && j < i + 10 && is_hex_digit(inner[j])
            j += 1
          end
          if j > i + 2
            codepoint = substring(inner, i + 2, j).to_i(16)
            if codepoint == 0
              return result
            end
            result.concat([codepoint].pack('U').bytes)
            i = j
          else
            result.push(inner[i][0].ord)
            i += 1
          end
        elsif c == "c"
          if i + 3 <= inner.length
            ctrl_char = inner[i + 2]
            skip_extra = 0
            if ctrl_char == "\\" && i + 4 <= inner.length && inner[i + 3] == "\\"
              skip_extra = 1
            end
            ctrl_val = ctrl_char[0].ord & 31
            if ctrl_val == 0
              return result
            end
            self.append_with_ctlesc(result, ctrl_val)
            i += 3 + skip_extra
          else
            result.push(inner[i][0].ord)
            i += 1
          end
        elsif c == "0"
          j = i + 2
          while j < inner.length && j < i + 4 && is_octal_digit(inner[j])
            j += 1
          end
          if j > i + 2
            byte_val = substring(inner, i + 1, j).to_i(8) & 255
            if byte_val == 0
              return result
            end
            self.append_with_ctlesc(result, byte_val)
            i = j
          else
            return result
          end
        elsif c >= "1" && c <= "7"
          j = i + 1
          while j < inner.length && j < i + 4 && is_octal_digit(inner[j])
            j += 1
          end
          byte_val = substring(inner, i + 1, j).to_i(8) & 255
          if byte_val == 0
            return result
          end
          self.append_with_ctlesc(result, byte_val)
          i = j
        else
          result.push(92)
          result.push(c[0].ord)
          i += 2
        end
      else
        result.concat(inner[i].bytes)
        i += 1
      end
    end
    return result
  end

  def expand_ansi_c_escapes(value)
    if !(value.start_with?("'") && value.end_with?("'"))
      return value
    end
    inner = substring(value, 1, value.length - 1)
    literal_bytes = self.ansi_c_to_bytes(inner)
    literal_str = literal_bytes.pack('C*').force_encoding('UTF-8').scrub("\uFFFD")
    return self.sh_single_quote(literal_str)
  end

  def expand_all_ansi_c_quotes(value)
    result = []
    i = 0
    quote = new_quote_state()
    in_backtick = false
    brace_depth = 0
    while i < value.length
      ch = value[i]
      if ch == "`" && !quote.single
        in_backtick = !in_backtick
        result.push(ch)
        i += 1
        next
      end
      if in_backtick
        if ch == "\\" && i + 1 < value.length
          result.push(ch)
          result.push(value[i + 1])
          i += 2
        else
          result.push(ch)
          i += 1
        end
        next
      end
      if !quote.single
        if is_expansion_start(value, i, "${")
          brace_depth += 1
          quote.push
          result.push("${")
          i += 2
          next
        elsif ch == "}" && brace_depth > 0 && !quote.double
          brace_depth -= 1
          result.push(ch)
          quote.pop
          i += 1
          next
        end
      end
      effective_in_dquote = quote.double
      if ch == "'" && !effective_in_dquote
        is_ansi_c = !quote.single && i > 0 && value[i - 1] == "$" && count_consecutive_dollars_before(value, i - 1) % 2 == 0
        if !is_ansi_c
          quote.single = !quote.single
        end
        result.push(ch)
        i += 1
      elsif ch == "\"" && !quote.single
        quote.double = !quote.double
        result.push(ch)
        i += 1
      elsif ch == "\\" && i + 1 < value.length && !quote.single
        result.push(ch)
        result.push(value[i + 1])
        i += 2
      elsif starts_with_at(value, i, "$'") && !quote.single && !effective_in_dquote && count_consecutive_dollars_before(value, i) % 2 == 0
        j = i + 2
        while j < value.length
          if value[j] == "\\" && j + 1 < value.length
            j += 2
          elsif value[j] == "'"
            j += 1
            break
          else
            j += 1
          end
        end
        ansi_str = substring(value, i, j)
        expanded = self.expand_ansi_c_escapes(substring(ansi_str, 1, ansi_str.length))
        outer_in_dquote = quote.outer_double
        if brace_depth > 0 && outer_in_dquote && expanded.start_with?("'") && expanded.end_with?("'")
          inner = substring(expanded, 1, expanded.length - 1)
          if inner.index("\u0001").nil?
            result_str = result.join
            in_pattern = false
            last_brace_idx = result_str.rindex("${")
            if last_brace_idx >= 0
              after_brace = result_str[last_brace_idx + 2..]
              var_name_len = 0
              if (after_brace && !after_brace.empty?)
                if "@*#?-$!0123456789_".include?(after_brace[0])
                  var_name_len = 1
                elsif (after_brace[0]).match?(/\A[[:alpha:]]+\z/) || after_brace[0] == "_"
                  while var_name_len < after_brace.length
                    c = after_brace[var_name_len]
                    if !((c).match?(/\A[[:alnum:]]+\z/) || c == "_")
                      break
                    end
                    var_name_len += 1
                  end
                end
              end
              if var_name_len > 0 && var_name_len < after_brace.length && (!"#?-".include?(after_brace[0]))
                op_start = after_brace[var_name_len..]
                if op_start.start_with?("@") && op_start.length > 1
                  op_start = op_start[1..]
                end
                ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"].each do |op|
                  if op_start.start_with?(op)
                    in_pattern = true
                    break
                  end
                end
                if !in_pattern && (op_start && !op_start.empty?) && (!"%#/^,~:+-=?".include?(op_start[0]))
                  ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"].each do |op|
                    if op_start.include?(op)
                      in_pattern = true
                      break
                    end
                  end
                end
              elsif var_name_len == 0 && after_brace.length > 1
                first_char = after_brace[0]
                if !"%#/^,".include?(first_char)
                  rest = after_brace[1..]
                  ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"].each do |op|
                    if rest.include?(op)
                      in_pattern = true
                      break
                    end
                  end
                end
              end
            end
            if !in_pattern
              expanded = inner
            end
          end
        end
        result.push(expanded)
        i = j
      else
        result.push(ch)
        i += 1
      end
    end
    return result.join
  end

  def strip_locale_string_dollars(value)
    result = []
    i = 0
    brace_depth = 0
    bracket_depth = 0
    quote = new_quote_state()
    brace_quote = new_quote_state()
    bracket_in_double_quote = false
    while i < value.length
      ch = value[i]
      if ch == "\\" && i + 1 < value.length && !quote.single && !brace_quote.single
        result.push(ch)
        result.push(value[i + 1])
        i += 2
      elsif starts_with_at(value, i, "${") && !quote.single && !brace_quote.single && (i == 0 || value[i - 1] != "$")
        brace_depth += 1
        brace_quote.double = false
        brace_quote.single = false
        result.push("$")
        result.push("{")
        i += 2
      elsif ch == "}" && brace_depth > 0 && !quote.single && !brace_quote.double && !brace_quote.single
        brace_depth -= 1
        result.push(ch)
        i += 1
      elsif ch == "[" && brace_depth > 0 && !quote.single && !brace_quote.double
        bracket_depth += 1
        bracket_in_double_quote = false
        result.push(ch)
        i += 1
      elsif ch == "]" && bracket_depth > 0 && !quote.single && !bracket_in_double_quote
        bracket_depth -= 1
        result.push(ch)
        i += 1
      elsif ch == "'" && !quote.double && brace_depth == 0
        quote.single = !quote.single
        result.push(ch)
        i += 1
      elsif ch == "\"" && !quote.single && brace_depth == 0
        quote.double = !quote.double
        result.push(ch)
        i += 1
      elsif ch == "\"" && !quote.single && bracket_depth > 0
        bracket_in_double_quote = !bracket_in_double_quote
        result.push(ch)
        i += 1
      elsif ch == "\"" && !quote.single && !brace_quote.single && brace_depth > 0
        brace_quote.double = !brace_quote.double
        result.push(ch)
        i += 1
      elsif ch == "'" && !quote.double && !brace_quote.double && brace_depth > 0
        brace_quote.single = !brace_quote.single
        result.push(ch)
        i += 1
      elsif starts_with_at(value, i, "$\"") && !quote.single && !brace_quote.single && (brace_depth > 0 || bracket_depth > 0 || !quote.double) && !brace_quote.double && !bracket_in_double_quote
        dollar_count = 1 + count_consecutive_dollars_before(value, i)
        if dollar_count % 2 == 1
          result.push("\"")
          if bracket_depth > 0
            bracket_in_double_quote = true
          elsif brace_depth > 0
            brace_quote.double = true
          else
            quote.double = true
          end
          i += 2
        else
          result.push(ch)
          i += 1
        end
      else
        result.push(ch)
        i += 1
      end
    end
    return result.join
  end

  def normalize_array_whitespace(value)
    i = 0
    if !(i < value.length && ((value[i]).match?(/\A[[:alpha:]]+\z/) || value[i] == "_"))
      return value
    end
    i += 1
    while i < value.length && ((value[i]).match?(/\A[[:alnum:]]+\z/) || value[i] == "_")
      i += 1
    end
    while i < value.length && value[i] == "["
      depth = 1
      i += 1
      while i < value.length && depth > 0
        if value[i] == "["
          depth += 1
        elsif value[i] == "]"
          depth -= 1
        end
        i += 1
      end
      if depth != 0
        return value
      end
    end
    if i < value.length && value[i] == "+"
      i += 1
    end
    if !(i + 1 < value.length && value[i] == "=" && value[i + 1] == "(")
      return value
    end
    prefix = substring(value, 0, i + 1)
    open_paren_pos = i + 1
    if value.end_with?(")")
      close_paren_pos = value.length - 1
    else
      close_paren_pos = self.find_matching_paren(value, open_paren_pos)
      if close_paren_pos < 0
        return value
      end
    end
    inner = substring(value, open_paren_pos + 1, close_paren_pos)
    suffix = substring(value, close_paren_pos + 1, value.length)
    result = self.normalize_array_inner(inner)
    return prefix + "(" + result + ")" + suffix
  end

  def find_matching_paren(value, open_pos)
    if open_pos >= value.length || value[open_pos] != "("
      return -1
    end
    i = open_pos + 1
    depth = 1
    quote = new_quote_state()
    while i < value.length && depth > 0
      ch = value[i]
      if ch == "\\" && i + 1 < value.length && !quote.single
        i += 2
        next
      end
      if ch == "'" && !quote.double
        quote.single = !quote.single
        i += 1
        next
      end
      if ch == "\"" && !quote.single
        quote.double = !quote.double
        i += 1
        next
      end
      if quote.single || quote.double
        i += 1
        next
      end
      if ch == "#"
        while i < value.length && value[i] != "\n"
          i += 1
        end
        next
      end
      if ch == "("
        depth += 1
      elsif ch == ")"
        depth -= 1
        if depth == 0
          return i
        end
      end
      i += 1
    end
    return -1
  end

  def normalize_array_inner(inner)
    normalized = []
    i = 0
    in_whitespace = true
    brace_depth = 0
    bracket_depth = 0
    while i < inner.length
      ch = inner[i]
      if is_whitespace(ch)
        if !in_whitespace && (normalized && !normalized.empty?) && brace_depth == 0 && bracket_depth == 0
          normalized.push(" ")
          in_whitespace = true
        end
        if brace_depth > 0 || bracket_depth > 0
          normalized.push(ch)
        end
        i += 1
      elsif ch == "'"
        in_whitespace = false
        j = i + 1
        while j < inner.length && inner[j] != "'"
          j += 1
        end
        normalized.push(substring(inner, i, j + 1))
        i = j + 1
      elsif ch == "\""
        in_whitespace = false
        j = i + 1
        dq_content = ["\""]
        dq_brace_depth = 0
        while j < inner.length
          if inner[j] == "\\" && j + 1 < inner.length
            if inner[j + 1] == "\n"
              j += 2
            else
              dq_content.push(inner[j])
              dq_content.push(inner[j + 1])
              j += 2
            end
          elsif is_expansion_start(inner, j, "${")
            dq_content.push("${")
            dq_brace_depth += 1
            j += 2
          elsif inner[j] == "}" && dq_brace_depth > 0
            dq_content.push("}")
            dq_brace_depth -= 1
            j += 1
          elsif inner[j] == "\"" && dq_brace_depth == 0
            dq_content.push("\"")
            j += 1
            break
          else
            dq_content.push(inner[j])
            j += 1
          end
        end
        normalized.push(dq_content.join)
        i = j
      elsif ch == "\\" && i + 1 < inner.length
        if inner[i + 1] == "\n"
          i += 2
        else
          in_whitespace = false
          normalized.push(substring(inner, i, i + 2))
          i += 2
        end
      elsif is_expansion_start(inner, i, "$((")
        in_whitespace = false
        j = i + 3
        depth = 1
        while j < inner.length && depth > 0
          if j + 1 < inner.length && inner[j] == "(" && inner[j + 1] == "("
            depth += 1
            j += 2
          elsif j + 1 < inner.length && inner[j] == ")" && inner[j + 1] == ")"
            depth -= 1
            j += 2
          else
            j += 1
          end
        end
        normalized.push(substring(inner, i, j))
        i = j
      elsif is_expansion_start(inner, i, "$(")
        in_whitespace = false
        j = i + 2
        depth = 1
        while j < inner.length && depth > 0
          if inner[j] == "(" && j > 0 && inner[j - 1] == "$"
            depth += 1
          elsif inner[j] == ")"
            depth -= 1
          elsif inner[j] == "'"
            j += 1
            while j < inner.length && inner[j] != "'"
              j += 1
            end
          elsif inner[j] == "\""
            j += 1
            while j < inner.length
              if inner[j] == "\\" && j + 1 < inner.length
                j += 2
                next
              end
              if inner[j] == "\""
                break
              end
              j += 1
            end
          end
          j += 1
        end
        normalized.push(substring(inner, i, j))
        i = j
      elsif (ch == "<" || ch == ">") && i + 1 < inner.length && inner[i + 1] == "("
        in_whitespace = false
        j = i + 2
        depth = 1
        while j < inner.length && depth > 0
          if inner[j] == "("
            depth += 1
          elsif inner[j] == ")"
            depth -= 1
          elsif inner[j] == "'"
            j += 1
            while j < inner.length && inner[j] != "'"
              j += 1
            end
          elsif inner[j] == "\""
            j += 1
            while j < inner.length
              if inner[j] == "\\" && j + 1 < inner.length
                j += 2
                next
              end
              if inner[j] == "\""
                break
              end
              j += 1
            end
          end
          j += 1
        end
        normalized.push(substring(inner, i, j))
        i = j
      elsif is_expansion_start(inner, i, "${")
        in_whitespace = false
        normalized.push("${")
        brace_depth += 1
        i += 2
      elsif ch == "{" && brace_depth > 0
        normalized.push(ch)
        brace_depth += 1
        i += 1
      elsif ch == "}" && brace_depth > 0
        normalized.push(ch)
        brace_depth -= 1
        i += 1
      elsif ch == "#" && brace_depth == 0 && in_whitespace
        while i < inner.length && inner[i] != "\n"
          i += 1
        end
      elsif ch == "["
        if in_whitespace || bracket_depth > 0
          bracket_depth += 1
        end
        in_whitespace = false
        normalized.push(ch)
        i += 1
      elsif ch == "]" && bracket_depth > 0
        normalized.push(ch)
        bracket_depth -= 1
        i += 1
      else
        in_whitespace = false
        normalized.push(ch)
        i += 1
      end
    end
    return normalized.join.gsub(/[ \t\n\r]+\z/, '')
  end

  def strip_arith_line_continuations(value)
    result = []
    i = 0
    while i < value.length
      if is_expansion_start(value, i, "$((")
        start = i
        i += 3
        depth = 2
        arith_content = []
        first_close_idx = -1
        while i < value.length && depth > 0
          if value[i] == "("
            arith_content.push("(")
            depth += 1
            i += 1
            if depth > 1
              first_close_idx = -1
            end
          elsif value[i] == ")"
            if depth == 2
              first_close_idx = arith_content.length
            end
            depth -= 1
            if depth > 0
              arith_content.push(")")
            end
            i += 1
          elsif value[i] == "\\" && i + 1 < value.length && value[i + 1] == "\n"
            num_backslashes = 0
            j = arith_content.length - 1
            while j >= 0 && arith_content[j] == "\n"
              j -= 1
            end
            while j >= 0 && arith_content[j] == "\\"
              num_backslashes += 1
              j -= 1
            end
            if num_backslashes % 2 == 1
              arith_content.push("\\")
              arith_content.push("\n")
              i += 2
            else
              i += 2
            end
            if depth == 1
              first_close_idx = -1
            end
          else
            arith_content.push(value[i])
            i += 1
            if depth == 1
              first_close_idx = -1
            end
          end
        end
        if depth == 0 || depth == 1 && first_close_idx != -1
          content = arith_content.join
          if first_close_idx != -1
            content = content[0...first_close_idx]
            closing = depth == 0 ? "))" : ")"
            result.push("$((" + content + closing)
          else
            result.push("$((" + content + ")")
          end
        else
          result.push(substring(value, start, i))
        end
      else
        result.push(value[i])
        i += 1
      end
    end
    return result.join
  end

  def collect_cmdsubs(node)
    result = []
    case node
    when CommandSubstitution
      node = node
      result.push(node)
    when Array_
      node = node
      (node.elements || []).each do |elem|
        (elem.parts || []).each do |p_|
          case p_
          when CommandSubstitution
            p_ = p_
            result.push(p_)
          else
            result.concat(self.collect_cmdsubs(p_))
          end
        end
      end
    when ArithmeticExpansion
      node = node
      if !node.expression.nil?
        result.concat(self.collect_cmdsubs(node.expression))
      end
    when ArithBinaryOp
      node = node
      result.concat(self.collect_cmdsubs(node.left))
      result.concat(self.collect_cmdsubs(node.right))
    when ArithComma
      node = node
      result.concat(self.collect_cmdsubs(node.left))
      result.concat(self.collect_cmdsubs(node.right))
    when ArithUnaryOp
      node = node
      result.concat(self.collect_cmdsubs(node.operand))
    when ArithPreIncr
      node = node
      result.concat(self.collect_cmdsubs(node.operand))
    when ArithPostIncr
      node = node
      result.concat(self.collect_cmdsubs(node.operand))
    when ArithPreDecr
      node = node
      result.concat(self.collect_cmdsubs(node.operand))
    when ArithPostDecr
      node = node
      result.concat(self.collect_cmdsubs(node.operand))
    when ArithTernary
      node = node
      result.concat(self.collect_cmdsubs(node.condition))
      result.concat(self.collect_cmdsubs(node.if_true))
      result.concat(self.collect_cmdsubs(node.if_false))
    when ArithAssign
      node = node
      result.concat(self.collect_cmdsubs(node.target))
      result.concat(self.collect_cmdsubs(node.value))
    end
    return result
  end

  def collect_procsubs(node)
    result = []
    case node
    when ProcessSubstitution
      node = node
      result.push(node)
    when Array_
      node = node
      (node.elements || []).each do |elem|
        (elem.parts || []).each do |p_|
          case p_
          when ProcessSubstitution
            p_ = p_
            result.push(p_)
          else
            result.concat(self.collect_procsubs(p_))
          end
        end
      end
    end
    return result
  end

  def format_command_substitutions(value, in_arith = false)
    cmdsub_parts = []
    procsub_parts = []
    has_arith = false
    (self.parts || []).each do |p_|
      case p_
      when CommandSubstitution
        p_ = p_
        cmdsub_parts.push(p_)
      when ProcessSubstitution
        p_ = p_
        procsub_parts.push(p_)
      when ArithmeticExpansion
        p_ = p_
        has_arith = true
      else
        cmdsub_parts.concat(self.collect_cmdsubs(p_))
        procsub_parts.concat(self.collect_procsubs(p_))
      end
    end
    has_brace_cmdsub = !value.index("${ ").nil? || !value.index("${\t").nil? || !value.index("${\n").nil? || !value.index("${|").nil?
    has_untracked_cmdsub = false
    has_untracked_procsub = false
    idx = 0
    scan_quote = new_quote_state()
    while idx < value.length
      if value[idx] == "\""
        scan_quote.double = !scan_quote.double
        idx += 1
      elsif value[idx] == "'" && !scan_quote.double
        idx += 1
        while idx < value.length && value[idx] != "'"
          idx += 1
        end
        if idx < value.length
          idx += 1
        end
      elsif starts_with_at(value, idx, "$(") && !starts_with_at(value, idx, "$((") && !is_backslash_escaped(value, idx) && !is_dollar_dollar_paren(value, idx)
        has_untracked_cmdsub = true
        break
      elsif (starts_with_at(value, idx, "<(") || starts_with_at(value, idx, ">(")) && !scan_quote.double
        if idx == 0 || !(value[idx - 1]).match?(/\A[[:alnum:]]+\z/) && (!"\"'".include?(value[idx - 1]))
          has_untracked_procsub = true
          break
        end
        idx += 1
      else
        idx += 1
      end
    end
    has_param_with_procsub_pattern = (value.include?("${")) && ((value.include?("<(")) || (value.include?(">(")))
    if !(cmdsub_parts && !cmdsub_parts.empty?) && !(procsub_parts && !procsub_parts.empty?) && !has_brace_cmdsub && !has_untracked_cmdsub && !has_untracked_procsub && !has_param_with_procsub_pattern
      return value
    end
    result = []
    i = 0
    cmdsub_idx = 0
    procsub_idx = 0
    main_quote = new_quote_state()
    extglob_depth = 0
    deprecated_arith_depth = 0
    arith_depth = 0
    arith_paren_depth = 0
    while i < value.length
      if i > 0 && is_extglob_prefix(value[i - 1]) && value[i] == "(" && !is_backslash_escaped(value, i - 1)
        extglob_depth += 1
        result.push(value[i])
        i += 1
        next
      end
      if value[i] == ")" && extglob_depth > 0
        extglob_depth -= 1
        result.push(value[i])
        i += 1
        next
      end
      if starts_with_at(value, i, "$[") && !is_backslash_escaped(value, i)
        deprecated_arith_depth += 1
        result.push(value[i])
        i += 1
        next
      end
      if value[i] == "]" && deprecated_arith_depth > 0
        deprecated_arith_depth -= 1
        result.push(value[i])
        i += 1
        next
      end
      if is_expansion_start(value, i, "$((") && !is_backslash_escaped(value, i) && has_arith
        arith_depth += 1
        arith_paren_depth += 2
        result.push("$((")
        i += 3
        next
      end
      if arith_depth > 0 && arith_paren_depth == 2 && starts_with_at(value, i, "))")
        arith_depth -= 1
        arith_paren_depth -= 2
        result.push("))")
        i += 2
        next
      end
      if arith_depth > 0
        if value[i] == "("
          arith_paren_depth += 1
          result.push(value[i])
          i += 1
          next
        elsif value[i] == ")"
          arith_paren_depth -= 1
          result.push(value[i])
          i += 1
          next
        end
      end
      if is_expansion_start(value, i, "$((") && !has_arith
        j = find_cmdsub_end(value, i + 2)
        result.push(substring(value, i, j))
        if cmdsub_idx < cmdsub_parts.length
          cmdsub_idx += 1
        end
        i = j
        next
      end
      if starts_with_at(value, i, "$(") && !starts_with_at(value, i, "$((") && !is_backslash_escaped(value, i) && !is_dollar_dollar_paren(value, i)
        j = find_cmdsub_end(value, i + 2)
        if extglob_depth > 0
          result.push(substring(value, i, j))
          if cmdsub_idx < cmdsub_parts.length
            cmdsub_idx += 1
          end
          i = j
          next
        end
        inner = substring(value, i + 2, j - 1)
        if cmdsub_idx < cmdsub_parts.length
          node = cmdsub_parts[cmdsub_idx]
          formatted = format_cmdsub_node(node.command, 0, false, false, false)
          cmdsub_idx += 1
        else
          begin
            parser = new_parser(inner, false, false)
            parsed = parser.parse_list(true)
            formatted = !parsed.nil? ? format_cmdsub_node(parsed, 0, false, false, false) : ""
          rescue Exception_ => _e
            formatted = inner
          end
        end
        if formatted.start_with?("(")
          result.push("$( " + formatted + ")")
        else
          result.push("$(" + formatted + ")")
        end
        i = j
      elsif value[i] == "`" && cmdsub_idx < cmdsub_parts.length
        j = i + 1
        while j < value.length
          if value[j] == "\\" && j + 1 < value.length
            j += 2
            next
          end
          if value[j] == "`"
            j += 1
            break
          end
          j += 1
        end
        result.push(substring(value, i, j))
        cmdsub_idx += 1
        i = j
      elsif is_expansion_start(value, i, "${") && i + 2 < value.length && is_funsub_char(value[i + 2]) && !is_backslash_escaped(value, i)
        j = find_funsub_end(value, i + 2)
        cmdsub_node = cmdsub_idx < cmdsub_parts.length ? cmdsub_parts[cmdsub_idx] : nil
        if cmdsub_node.is_a?(CommandSubstitution) && cmdsub_node.brace
          node = cmdsub_node
          formatted = format_cmdsub_node(node.command, 0, false, false, false)
          has_pipe = value[i + 2] == "|"
          prefix = has_pipe ? "${|" : "${ "
          orig_inner = substring(value, i + 2, j - 1)
          ends_with_newline = orig_inner.end_with?("\n")
          if !(formatted && !formatted.empty?) || (formatted).match?(/\A\s+\z/)
            suffix = "}"
          elsif formatted.end_with?("&") || formatted.end_with?("& ")
            suffix = formatted.end_with?("&") ? " }" : "}"
          elsif ends_with_newline
            suffix = "\n }"
          else
            suffix = "; }"
          end
          result.push(prefix + formatted + suffix)
          cmdsub_idx += 1
        else
          result.push(substring(value, i, j))
        end
        i = j
      elsif (starts_with_at(value, i, ">(") || starts_with_at(value, i, "<(")) && !main_quote.double && deprecated_arith_depth == 0 && arith_depth == 0
        is_procsub = i == 0 || !(value[i - 1]).match?(/\A[[:alnum:]]+\z/) && (!"\"'".include?(value[i - 1]))
        if extglob_depth > 0
          j = find_cmdsub_end(value, i + 2)
          result.push(substring(value, i, j))
          if procsub_idx < procsub_parts.length
            procsub_idx += 1
          end
          i = j
          next
        end
        if procsub_idx < procsub_parts.length
          direction = value[i]
          j = find_cmdsub_end(value, i + 2)
          node = procsub_parts[procsub_idx]
          compact = starts_with_subshell(node.command)
          formatted = format_cmdsub_node(node.command, 0, true, compact, true)
          raw_content = substring(value, i + 2, j - 1)
          if node.command.kind == "subshell"
            leading_ws_end = 0
            while leading_ws_end < raw_content.length && (" \t\n".include?(raw_content[leading_ws_end]))
              leading_ws_end += 1
            end
            leading_ws = raw_content[0...leading_ws_end]
            stripped = raw_content[leading_ws_end..]
            if stripped.start_with?("(")
              if (leading_ws && !leading_ws.empty?)
                normalized_ws = leading_ws.gsub("\n", " ").gsub("\t", " ")
                spaced = format_cmdsub_node(node.command, 0, false, false, false)
                result.push(direction + "(" + normalized_ws + spaced + ")")
              else
                raw_content = raw_content.gsub("\\
") { "" }
                result.push(direction + "(" + raw_content + ")")
              end
              procsub_idx += 1
              i = j
              next
            end
          end
          raw_content = substring(value, i + 2, j - 1)
          raw_stripped = raw_content.gsub("\\
") { "" }
          if starts_with_subshell(node.command) && formatted != raw_stripped
            result.push(direction + "(" + raw_stripped + ")")
          else
            final_output = direction + "(" + formatted + ")"
            result.push(final_output)
          end
          procsub_idx += 1
          i = j
        elsif is_procsub && self.parts.length > 0
          direction = value[i]
          j = find_cmdsub_end(value, i + 2)
          if j > value.length || j > 0 && j <= value.length && value[j - 1] != ")"
            result.push(value[i])
            i += 1
            next
          end
          inner = substring(value, i + 2, j - 1)
          begin
            parser = new_parser(inner, false, false)
            parsed = parser.parse_list(true)
            if !parsed.nil? && parser.pos == inner.length && (!inner.include?("\n"))
              compact = starts_with_subshell(parsed)
              formatted = format_cmdsub_node(parsed, 0, true, compact, true)
            else
              formatted = inner
            end
          rescue Exception_ => _e
            formatted = inner
          end
          result.push(direction + "(" + formatted + ")")
          i = j
        elsif is_procsub
          direction = value[i]
          j = find_cmdsub_end(value, i + 2)
          if j > value.length || j > 0 && j <= value.length && value[j - 1] != ")"
            result.push(value[i])
            i += 1
            next
          end
          inner = substring(value, i + 2, j - 1)
          if in_arith
            result.push(direction + "(" + inner + ")")
          elsif (inner.gsub(/\A[ \t\n\r]+|[ \t\n\r]+\z/, '') && !inner.gsub(/\A[ \t\n\r]+|[ \t\n\r]+\z/, '').empty?)
            stripped = inner.gsub(/\A[ \t]+/, '')
            result.push(direction + "(" + stripped + ")")
          else
            result.push(direction + "(" + inner + ")")
          end
          i = j
        else
          result.push(value[i])
          i += 1
        end
      elsif (is_expansion_start(value, i, "${ ") || is_expansion_start(value, i, "${\t") || is_expansion_start(value, i, "${\n") || is_expansion_start(value, i, "${|")) && !is_backslash_escaped(value, i)
        prefix = substring(value, i, i + 3).gsub("\t", " ").gsub("\n", " ")
        j = i + 3
        depth = 1
        while j < value.length && depth > 0
          if value[j] == "{"
            depth += 1
          elsif value[j] == "}"
            depth -= 1
          end
          j += 1
        end
        inner = substring(value, i + 2, j - 1)
        if inner.gsub(/\A[ \t\n\r]+|[ \t\n\r]+\z/, '') == ""
          result.push("${ }")
        else
          begin
            parser = new_parser(inner.gsub(/\A[ \t\n|]+/, ''), false, false)
            parsed = parser.parse_list(true)
            if !parsed.nil?
              formatted = format_cmdsub_node(parsed, 0, false, false, false)
              formatted = formatted.gsub(/[;]+\z/, '')
              if inner.gsub(/[ \t]+\z/, '').end_with?("\n")
                terminator = "\n }"
              elsif formatted.end_with?(" &")
                terminator = " }"
              else
                terminator = "; }"
              end
              result.push(prefix + formatted + terminator)
            else
              result.push("${ }")
            end
          rescue Exception_ => _e
            result.push(substring(value, i, j))
          end
        end
        i = j
      elsif is_expansion_start(value, i, "${") && !is_backslash_escaped(value, i)
        j = i + 2
        depth = 1
        brace_quote = new_quote_state()
        while j < value.length && depth > 0
          c = value[j]
          if c == "\\" && j + 1 < value.length && !brace_quote.single
            j += 2
            next
          end
          if c == "'" && !brace_quote.double
            brace_quote.single = !brace_quote.single
          elsif c == "\"" && !brace_quote.single
            brace_quote.double = !brace_quote.double
          elsif !brace_quote.in_quotes
            if is_expansion_start(value, j, "$(") && !starts_with_at(value, j, "$((")
              j = find_cmdsub_end(value, j + 2)
              next
            end
            if c == "{"
              depth += 1
            elsif c == "}"
              depth -= 1
            end
          end
          j += 1
        end
        if depth > 0
          inner = substring(value, i + 2, j)
        else
          inner = substring(value, i + 2, j - 1)
        end
        formatted_inner = self.format_command_substitutions(inner, false)
        formatted_inner = self.normalize_extglob_whitespace(formatted_inner)
        if depth == 0
          result.push("${" + formatted_inner + "}")
        else
          result.push("${" + formatted_inner)
        end
        i = j
      elsif value[i] == "\""
        main_quote.double = !main_quote.double
        result.push(value[i])
        i += 1
      elsif value[i] == "'" && !main_quote.double
        j = i + 1
        while j < value.length && value[j] != "'"
          j += 1
        end
        if j < value.length
          j += 1
        end
        result.push(substring(value, i, j))
        i = j
      else
        result.push(value[i])
        i += 1
      end
    end
    return result.join
  end

  def normalize_extglob_whitespace(value)
    result = []
    i = 0
    extglob_quote = new_quote_state()
    deprecated_arith_depth = 0
    while i < value.length
      if value[i] == "\""
        extglob_quote.double = !extglob_quote.double
        result.push(value[i])
        i += 1
        next
      end
      if starts_with_at(value, i, "$[") && !is_backslash_escaped(value, i)
        deprecated_arith_depth += 1
        result.push(value[i])
        i += 1
        next
      end
      if value[i] == "]" && deprecated_arith_depth > 0
        deprecated_arith_depth -= 1
        result.push(value[i])
        i += 1
        next
      end
      if i + 1 < value.length && value[i + 1] == "("
        prefix_char = value[i]
        if ("><".include?(prefix_char)) && !extglob_quote.double && deprecated_arith_depth == 0
          result.push(prefix_char)
          result.push("(")
          i += 2
          depth = 1
          pattern_parts = []
          current_part = []
          has_pipe = false
          while i < value.length && depth > 0
            if value[i] == "\\" && i + 1 < value.length
              current_part.push(value[i...i + 2])
              i += 2
              next
            elsif value[i] == "("
              depth += 1
              current_part.push(value[i])
              i += 1
            elsif value[i] == ")"
              depth -= 1
              if depth == 0
                part_content = current_part.join
                if part_content.include?("<<")
                  pattern_parts.push(part_content)
                elsif has_pipe
                  pattern_parts.push(part_content.gsub(/\A[ \t\n\r]+|[ \t\n\r]+\z/, ''))
                else
                  pattern_parts.push(part_content)
                end
                break
              end
              current_part.push(value[i])
              i += 1
            elsif value[i] == "|" && depth == 1
              if i + 1 < value.length && value[i + 1] == "|"
                current_part.push("||")
                i += 2
              else
                has_pipe = true
                part_content = current_part.join
                if part_content.include?("<<")
                  pattern_parts.push(part_content)
                else
                  pattern_parts.push(part_content.gsub(/\A[ \t\n\r]+|[ \t\n\r]+\z/, ''))
                end
                current_part = []
                i += 1
              end
            else
              current_part.push(value[i])
              i += 1
            end
          end
          result.push(pattern_parts.join(" | "))
          if depth == 0
            result.push(")")
            i += 1
          end
          next
        end
      end
      result.push(value[i])
      i += 1
    end
    return result.join
  end

  def get_cond_formatted_value()
    value = self.expand_all_ansi_c_quotes(self.value)
    value = self.strip_locale_string_dollars(value)
    value = self.format_command_substitutions(value, false)
    value = self.normalize_extglob_whitespace(value)
    value = value.gsub("\u0001", "\u0001\u0001")
    return value.gsub(/[\n]+\z/, '')
  end

  def get_kind()
    return self.kind
  end
end

class Command
  attr_accessor :words, :redirects, :kind

  def initialize(words: [], redirects: [], kind: "")
    @words = words
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    parts = []
    (self.words || []).each do |w|
      parts.push(w.to_sexp)
    end
    (self.redirects || []).each do |r|
      parts.push(r.to_sexp)
    end
    inner = parts.join(" ")
    if !(inner && !inner.empty?)
      return "(command)"
    end
    return "(command " + inner + ")"
  end

  def get_kind()
    return self.kind
  end
end

class Pipeline
  attr_accessor :commands, :kind

  def initialize(commands: [], kind: "")
    @commands = commands
    @kind = kind
  end

  def to_sexp()
    if self.commands.length == 1
      return self.commands[0].to_sexp
    end
    cmds = []
    i = 0
    while i < self.commands.length
      cmd = self.commands[i]
      case cmd
      when PipeBoth
        cmd = cmd
        i += 1
        next
      end
      needs_redirect = i + 1 < self.commands.length && self.commands[i + 1].kind == "pipe-both"
      cmds.push([cmd, needs_redirect])
      i += 1
    end
    if cmds.length == 1
      pair = cmds[0]
      cmd = pair[0]
      needs = pair[1]
      return self.cmd_sexp(cmd, needs)
    end
    last_pair = cmds[-1]
    last_cmd = last_pair[0]
    last_needs = last_pair[1]
    result = self.cmd_sexp(last_cmd, last_needs)
    j = cmds.length - 2
    while j >= 0
      pair = cmds[j]
      cmd = pair[0]
      needs = pair[1]
      if needs && cmd.kind != "command"
        result = "(pipe " + cmd.to_sexp + " (redirect \">&\" 1) " + result + ")"
      else
        result = "(pipe " + self.cmd_sexp(cmd, needs) + " " + result + ")"
      end
      j -= 1
    end
    return result
  end

  def cmd_sexp(cmd, needs_redirect)
    if !needs_redirect
      return cmd.to_sexp
    end
    case cmd
    when Command
      cmd = cmd
      parts = []
      (cmd.words || []).each do |w|
        parts.push(w.to_sexp)
      end
      (cmd.redirects || []).each do |r|
        parts.push(r.to_sexp)
      end
      parts.push("(redirect \">&\" 1)")
      return "(command " + parts.join(" ") + ")"
    end
    return cmd.to_sexp
  end

  def get_kind()
    return self.kind
  end
end

class List
  attr_accessor :parts, :kind

  def initialize(parts: [], kind: "")
    @parts = parts
    @kind = kind
  end

  def to_sexp()
    parts = self.parts.dup
    op_names = {"&&" => "and", "||" => "or", ";" => "semi", "\n" => "semi", "&" => "background"}
    while parts.length > 1 && parts[-1].kind == "operator" && (parts[-1].op == ";" || parts[-1].op == "\n")
      parts = sublist(parts, 0, parts.length - 1)
    end
    if parts.length == 1
      return parts[0].to_sexp
    end
    if parts[-1].kind == "operator" && parts[-1].op == "&"
      i = parts.length - 3
      while i > 0
        if parts[i].kind == "operator" && (parts[i].op == ";" || parts[i].op == "\n")
          left = sublist(parts, 0, i)
          right = sublist(parts, i + 1, parts.length - 1)
          if left.length > 1
            left_sexp = List.new(parts: left, kind: "list").to_sexp
          else
            left_sexp = left[0].to_sexp
          end
          if right.length > 1
            right_sexp = List.new(parts: right, kind: "list").to_sexp
          else
            right_sexp = right[0].to_sexp
          end
          return "(semi " + left_sexp + " (background " + right_sexp + "))"
        end
        i += -2
      end
      inner_parts = sublist(parts, 0, parts.length - 1)
      if inner_parts.length == 1
        return "(background " + inner_parts[0].to_sexp + ")"
      end
      inner_list = List.new(parts: inner_parts, kind: "list")
      return "(background " + inner_list.to_sexp + ")"
    end
    return self.to_sexp_with_precedence(parts, op_names)
  end

  def to_sexp_with_precedence(parts, op_names)
    semi_positions = []
    (0...parts.length).each do |i|
      if parts[i].kind == "operator" && (parts[i].op == ";" || parts[i].op == "\n")
        semi_positions.push(i)
      end
    end
    if (semi_positions && !semi_positions.empty?)
      segments = []
      start = 0
      semi_positions.each do |pos|
        seg = sublist(parts, start, pos)
        if (seg && !seg.empty?) && seg[0].kind != "operator"
          segments.push(seg)
        end
        start = pos + 1
      end
      seg = sublist(parts, start, parts.length)
      if (seg && !seg.empty?) && seg[0].kind != "operator"
        segments.push(seg)
      end
      if !(segments && !segments.empty?)
        return "()"
      end
      result = self.to_sexp_amp_and_higher(segments[0], op_names)
      i = 1
      while i < segments.length
        result = "(semi " + result + " " + self.to_sexp_amp_and_higher(segments[i], op_names) + ")"
        i += 1
      end
      return result
    end
    return self.to_sexp_amp_and_higher(parts, op_names)
  end

  def to_sexp_amp_and_higher(parts, op_names)
    if parts.length == 1
      return parts[0].to_sexp
    end
    amp_positions = []
    i = 1
    while i < parts.length - 1
      if parts[i].kind == "operator" && parts[i].op == "&"
        amp_positions.push(i)
      end
      i += 2
    end
    if (amp_positions && !amp_positions.empty?)
      segments = []
      start = 0
      amp_positions.each do |pos|
        segments.push(sublist(parts, start, pos))
        start = pos + 1
      end
      segments.push(sublist(parts, start, parts.length))
      result = self.to_sexp_and_or(segments[0], op_names)
      i = 1
      while i < segments.length
        result = "(background " + result + " " + self.to_sexp_and_or(segments[i], op_names) + ")"
        i += 1
      end
      return result
    end
    return self.to_sexp_and_or(parts, op_names)
  end

  def to_sexp_and_or(parts, op_names)
    if parts.length == 1
      return parts[0].to_sexp
    end
    result = parts[0].to_sexp
    i = 1
    while i < parts.length - 1
      op = parts[i]
      cmd = parts[i + 1]
      op_name = op_names.fetch(op.op, op.op)
      result = "(" + op_name + " " + result + " " + cmd.to_sexp + ")"
      i += 2
    end
    return result
  end

  def get_kind()
    return self.kind
  end
end

class Operator
  attr_accessor :op, :kind

  def initialize(op: "", kind: "")
    @op = op
    @kind = kind
  end

  def to_sexp()
    names = {"&&" => "and", "||" => "or", ";" => "semi", "&" => "bg", "|" => "pipe"}
    return "(" + names.fetch(self.op, self.op) + ")"
  end

  def get_kind()
    return self.kind
  end
end

class PipeBoth
  attr_accessor :kind

  def initialize(kind: "")
    @kind = kind
  end

  def to_sexp()
    return "(pipe-both)"
  end

  def get_kind()
    return self.kind
  end
end

class Empty
  attr_accessor :kind

  def initialize(kind: "")
    @kind = kind
  end

  def to_sexp()
    return ""
  end

  def get_kind()
    return self.kind
  end
end

class Comment
  attr_accessor :text, :kind

  def initialize(text: "", kind: "")
    @text = text
    @kind = kind
  end

  def to_sexp()
    return ""
  end

  def get_kind()
    return self.kind
  end
end

class Redirect
  attr_accessor :op, :target, :fd, :kind

  def initialize(op: "", target: nil, fd: nil, kind: "")
    @op = op
    @target = target
    @fd = fd
    @kind = kind
  end

  def to_sexp()
    op = self.op.gsub(/\A[0123456789]+/, '')
    if op.start_with?("{")
      j = 1
      if j < op.length && ((op[j]).match?(/\A[[:alpha:]]+\z/) || op[j] == "_")
        j += 1
        while j < op.length && ((op[j]).match?(/\A[[:alnum:]]+\z/) || op[j] == "_")
          j += 1
        end
        if j < op.length && op[j] == "["
          j += 1
          while j < op.length && op[j] != "]"
            j += 1
          end
          if j < op.length && op[j] == "]"
            j += 1
          end
        end
        if j < op.length && op[j] == "}"
          op = substring(op, j + 1, op.length)
        end
      end
    end
    target_val = self.target.value
    target_val = self.target.expand_all_ansi_c_quotes(target_val)
    target_val = self.target.strip_locale_string_dollars(target_val)
    target_val = self.target.format_command_substitutions(target_val, false)
    target_val = self.target.strip_arith_line_continuations(target_val)
    if target_val.end_with?("\\") && !target_val.end_with?("\\\\")
      target_val = target_val + "\\"
    end
    if target_val.start_with?("&")
      if op == ">"
        op = ">&"
      elsif op == "<"
        op = "<&"
      end
      raw = substring(target_val, 1, target_val.length)
      if (raw).match?(/\A\d+\z/) && raw.to_i <= 2147483647
        return "(redirect \"" + op + "\" " + raw.to_i.to_s + ")"
      end
      if raw.end_with?("-") && (raw[0...-1]).match?(/\A\d+\z/) && raw[0...-1].to_i <= 2147483647
        return "(redirect \"" + op + "\" " + raw[0...-1].to_i.to_s + ")"
      end
      if target_val == "&-"
        return "(redirect \">&-\" 0)"
      end
      fd_target = raw.end_with?("-") ? raw[0...-1] : raw
      return "(redirect \"" + op + "\" \"" + fd_target + "\")"
    end
    if op == ">&" || op == "<&"
      if (target_val).match?(/\A\d+\z/) && target_val.to_i <= 2147483647
        return "(redirect \"" + op + "\" " + target_val.to_i.to_s + ")"
      end
      if target_val == "-"
        return "(redirect \">&-\" 0)"
      end
      if target_val.end_with?("-") && (target_val[0...-1]).match?(/\A\d+\z/) && target_val[0...-1].to_i <= 2147483647
        return "(redirect \"" + op + "\" " + target_val[0...-1].to_i.to_s + ")"
      end
      out_val = target_val.end_with?("-") ? target_val[0...-1] : target_val
      return "(redirect \"" + op + "\" \"" + out_val + "\")"
    end
    return "(redirect \"" + op + "\" \"" + target_val + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class HereDoc
  attr_accessor :delimiter, :content, :strip_tabs, :quoted, :fd, :complete, :start_pos, :kind

  def initialize(delimiter: "", content: "", strip_tabs: false, quoted: false, fd: nil, complete: false, start_pos: 0, kind: "")
    @delimiter = delimiter
    @content = content
    @strip_tabs = strip_tabs
    @quoted = quoted
    @fd = fd
    @complete = complete
    @start_pos = start_pos
    @kind = kind
  end

  def to_sexp()
    op = self.strip_tabs ? "<<-" : "<<"
    content = self.content
    if content.end_with?("\\") && !content.end_with?("\\\\")
      content = content + "\\"
    end
    return "(redirect \"#{op}\" \"#{content}\")"
  end

  def get_kind()
    return self.kind
  end
end

class Subshell
  attr_accessor :body, :redirects, :kind

  def initialize(body: nil, redirects: [], kind: "")
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    base = "(subshell " + self.body.to_sexp + ")"
    return append_redirects(base, self.redirects)
  end

  def get_kind()
    return self.kind
  end
end

class BraceGroup
  attr_accessor :body, :redirects, :kind

  def initialize(body: nil, redirects: [], kind: "")
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    base = "(brace-group " + self.body.to_sexp + ")"
    return append_redirects(base, self.redirects)
  end

  def get_kind()
    return self.kind
  end
end

class If
  attr_accessor :condition, :then_body, :else_body, :redirects, :kind

  def initialize(condition: nil, then_body: nil, else_body: nil, redirects: [], kind: "")
    @condition = condition
    @then_body = then_body
    @else_body = else_body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    result = "(if " + self.condition.to_sexp + " " + self.then_body.to_sexp
    if !self.else_body.nil?
      result = result + " " + self.else_body.to_sexp
    end
    result = result + ")"
    (self.redirects || []).each do |r|
      result = result + " " + r.to_sexp
    end
    return result
  end

  def get_kind()
    return self.kind
  end
end

class While
  attr_accessor :condition, :body, :redirects, :kind

  def initialize(condition: nil, body: nil, redirects: [], kind: "")
    @condition = condition
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    base = "(while " + self.condition.to_sexp + " " + self.body.to_sexp + ")"
    return append_redirects(base, self.redirects)
  end

  def get_kind()
    return self.kind
  end
end

class Until
  attr_accessor :condition, :body, :redirects, :kind

  def initialize(condition: nil, body: nil, redirects: [], kind: "")
    @condition = condition
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    base = "(until " + self.condition.to_sexp + " " + self.body.to_sexp + ")"
    return append_redirects(base, self.redirects)
  end

  def get_kind()
    return self.kind
  end
end

class For
  attr_accessor :var, :words, :body, :redirects, :kind

  def initialize(var: "", words: nil, body: nil, redirects: [], kind: "")
    @var = var
    @words = words
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    suffix = ""
    if (self.redirects && !self.redirects.empty?)
      redirect_parts = []
      (self.redirects || []).each do |r|
        redirect_parts.push(r.to_sexp)
      end
      suffix = " " + redirect_parts.join(" ")
    end
    temp_word = Word.new(value: self.var, parts: [], kind: "word")
    var_formatted = temp_word.format_command_substitutions(self.var, false)
    var_escaped = var_formatted.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
    if self.words.nil?
      return "(for (word \"" + var_escaped + "\") (in (word \"\\\"$@\\\"\")) " + self.body.to_sexp + ")" + suffix
    elsif self.words.length == 0
      return "(for (word \"" + var_escaped + "\") (in) " + self.body.to_sexp + ")" + suffix
    else
      word_parts = []
      (self.words || []).each do |w|
        word_parts.push(w.to_sexp)
      end
      word_strs = word_parts.join(" ")
      return "(for (word \"" + var_escaped + "\") (in " + word_strs + ") " + self.body.to_sexp + ")" + suffix
    end
  end

  def get_kind()
    return self.kind
  end
end

class ForArith
  attr_accessor :init, :cond, :incr, :body, :redirects, :kind

  def initialize(init: "", cond: "", incr: "", body: nil, redirects: [], kind: "")
    @init = init
    @cond = cond
    @incr = incr
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    suffix = ""
    if (self.redirects && !self.redirects.empty?)
      redirect_parts = []
      (self.redirects || []).each do |r|
        redirect_parts.push(r.to_sexp)
      end
      suffix = " " + redirect_parts.join(" ")
    end
    init_val = (self.init && !self.init.empty?) ? self.init : "1"
    cond_val = (self.cond && !self.cond.empty?) ? self.cond : "1"
    incr_val = (self.incr && !self.incr.empty?) ? self.incr : "1"
    init_str = format_arith_val(init_val)
    cond_str = format_arith_val(cond_val)
    incr_str = format_arith_val(incr_val)
    body_str = self.body.to_sexp
    return "(arith-for (init (word \"#{init_str}\")) (test (word \"#{cond_str}\")) (step (word \"#{incr_str}\")) #{body_str})#{suffix}"
  end

  def get_kind()
    return self.kind
  end
end

class Select
  attr_accessor :var, :words, :body, :redirects, :kind

  def initialize(var: "", words: nil, body: nil, redirects: [], kind: "")
    @var = var
    @words = words
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    suffix = ""
    if (self.redirects && !self.redirects.empty?)
      redirect_parts = []
      (self.redirects || []).each do |r|
        redirect_parts.push(r.to_sexp)
      end
      suffix = " " + redirect_parts.join(" ")
    end
    var_escaped = self.var.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
    if !self.words.nil?
      word_parts = []
      (self.words || []).each do |w|
        word_parts.push(w.to_sexp)
      end
      word_strs = word_parts.join(" ")
      if (self.words && !self.words.empty?)
        in_clause = "(in " + word_strs + ")"
      else
        in_clause = "(in)"
      end
    else
      in_clause = "(in (word \"\\\"$@\\\"\"))"
    end
    return "(select (word \"" + var_escaped + "\") " + in_clause + " " + self.body.to_sexp + ")" + suffix
  end

  def get_kind()
    return self.kind
  end
end

class Case
  attr_accessor :word, :patterns, :redirects, :kind

  def initialize(word: nil, patterns: [], redirects: [], kind: "")
    @word = word
    @patterns = patterns
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    parts = []
    parts.push("(case " + self.word.to_sexp)
    (self.patterns || []).each do |p_|
      parts.push(p_.to_sexp)
    end
    base = parts.join(" ") + ")"
    return append_redirects(base, self.redirects)
  end

  def get_kind()
    return self.kind
  end
end

class CasePattern
  attr_accessor :pattern, :body, :terminator, :kind

  def initialize(pattern: "", body: nil, terminator: "", kind: "")
    @pattern = pattern
    @body = body
    @terminator = terminator
    @kind = kind
  end

  def to_sexp()
    alternatives = []
    current = []
    i = 0
    depth = 0
    while i < self.pattern.length
      ch = self.pattern[i]
      if ch == "\\" && i + 1 < self.pattern.length
        current.push(substring(self.pattern, i, i + 2))
        i += 2
      elsif (ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!") && i + 1 < self.pattern.length && self.pattern[i + 1] == "("
        current.push(ch)
        current.push("(")
        depth += 1
        i += 2
      elsif is_expansion_start(self.pattern, i, "$(")
        current.push(ch)
        current.push("(")
        depth += 1
        i += 2
      elsif ch == "(" && depth > 0
        current.push(ch)
        depth += 1
        i += 1
      elsif ch == ")" && depth > 0
        current.push(ch)
        depth -= 1
        i += 1
      elsif ch == "["
        result0, result1, result2 = consume_bracket_class(self.pattern, i, depth)
        i = result0
        current.concat(result1)
      elsif ch == "'" && depth == 0
        result0, result1 = consume_single_quote(self.pattern, i)
        i = result0
        current.concat(result1)
      elsif ch == "\"" && depth == 0
        result0, result1 = consume_double_quote(self.pattern, i)
        i = result0
        current.concat(result1)
      elsif ch == "|" && depth == 0
        alternatives.push(current.join)
        current = []
        i += 1
      else
        current.push(ch)
        i += 1
      end
    end
    alternatives.push(current.join)
    word_list = []
    alternatives.each do |alt|
      word_list.push(Word.new(value: alt, kind: "word").to_sexp)
    end
    pattern_str = word_list.join(" ")
    parts = ["(pattern (" + pattern_str + ")"]
    if !self.body.nil?
      parts.push(" " + self.body.to_sexp)
    else
      parts.push(" ()")
    end
    parts.push(")")
    return parts.join
  end

  def get_kind()
    return self.kind
  end
end

class Function
  attr_accessor :name, :body, :kind

  def initialize(name: "", body: nil, kind: "")
    @name = name
    @body = body
    @kind = kind
  end

  def to_sexp()
    return "(function \"" + self.name + "\" " + self.body.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ParamExpansion
  attr_accessor :param, :op, :arg, :kind

  def initialize(param: "", op: "", arg: "", kind: "")
    @param = param
    @op = op
    @arg = arg
    @kind = kind
  end

  def to_sexp()
    escaped_param = self.param.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
    if self.op != ""
      escaped_op = self.op.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
      if self.arg != ""
        arg_val = self.arg
      else
        arg_val = ""
      end
      escaped_arg = arg_val.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
      return "(param \"" + escaped_param + "\" \"" + escaped_op + "\" \"" + escaped_arg + "\")"
    end
    return "(param \"" + escaped_param + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class ParamLength
  attr_accessor :param, :kind

  def initialize(param: "", kind: "")
    @param = param
    @kind = kind
  end

  def to_sexp()
    escaped = self.param.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
    return "(param-len \"" + escaped + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class ParamIndirect
  attr_accessor :param, :op, :arg, :kind

  def initialize(param: "", op: "", arg: "", kind: "")
    @param = param
    @op = op
    @arg = arg
    @kind = kind
  end

  def to_sexp()
    escaped = self.param.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
    if self.op != ""
      escaped_op = self.op.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
      if self.arg != ""
        arg_val = self.arg
      else
        arg_val = ""
      end
      escaped_arg = arg_val.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
      return "(param-indirect \"" + escaped + "\" \"" + escaped_op + "\" \"" + escaped_arg + "\")"
    end
    return "(param-indirect \"" + escaped + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class CommandSubstitution
  attr_accessor :command, :brace, :kind

  def initialize(command: nil, brace: false, kind: "")
    @command = command
    @brace = brace
    @kind = kind
  end

  def to_sexp()
    if self.brace
      return "(funsub " + self.command.to_sexp + ")"
    end
    return "(cmdsub " + self.command.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithmeticExpansion
  attr_accessor :expression, :kind

  def initialize(expression: nil, kind: "")
    @expression = expression
    @kind = kind
  end

  def to_sexp()
    if self.expression.nil?
      return "(arith)"
    end
    return "(arith " + self.expression.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithmeticCommand
  attr_accessor :expression, :redirects, :raw_content, :kind

  def initialize(expression: nil, redirects: [], raw_content: "", kind: "")
    @expression = expression
    @redirects = redirects
    @raw_content = raw_content
    @kind = kind
  end

  def to_sexp()
    formatted = Word.new(value: self.raw_content, kind: "word").format_command_substitutions(self.raw_content, true)
    escaped = formatted.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }.gsub("
") { "\\n" }.gsub("	") { "\\t" }
    result = "(arith (word \"" + escaped + "\"))"
    if (self.redirects && !self.redirects.empty?)
      redirect_parts = []
      (self.redirects || []).each do |r|
        redirect_parts.push(r.to_sexp)
      end
      redirect_sexps = redirect_parts.join(" ")
      return result + " " + redirect_sexps
    end
    return result
  end

  def get_kind()
    return self.kind
  end
end

class ArithNumber
  attr_accessor :value, :kind

  def initialize(value: "", kind: "")
    @value = value
    @kind = kind
  end

  def to_sexp()
    return "(number \"" + self.value + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithEmpty
  attr_accessor :kind

  def initialize(kind: "")
    @kind = kind
  end

  def to_sexp()
    return "(empty)"
  end

  def get_kind()
    return self.kind
  end
end

class ArithVar
  attr_accessor :name, :kind

  def initialize(name: "", kind: "")
    @name = name
    @kind = kind
  end

  def to_sexp()
    return "(var \"" + self.name + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithBinaryOp
  attr_accessor :op, :left, :right, :kind

  def initialize(op: "", left: nil, right: nil, kind: "")
    @op = op
    @left = left
    @right = right
    @kind = kind
  end

  def to_sexp()
    return "(binary-op \"" + self.op + "\" " + self.left.to_sexp + " " + self.right.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithUnaryOp
  attr_accessor :op, :operand, :kind

  def initialize(op: "", operand: nil, kind: "")
    @op = op
    @operand = operand
    @kind = kind
  end

  def to_sexp()
    return "(unary-op \"" + self.op + "\" " + self.operand.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithPreIncr
  attr_accessor :operand, :kind

  def initialize(operand: nil, kind: "")
    @operand = operand
    @kind = kind
  end

  def to_sexp()
    return "(pre-incr " + self.operand.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithPostIncr
  attr_accessor :operand, :kind

  def initialize(operand: nil, kind: "")
    @operand = operand
    @kind = kind
  end

  def to_sexp()
    return "(post-incr " + self.operand.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithPreDecr
  attr_accessor :operand, :kind

  def initialize(operand: nil, kind: "")
    @operand = operand
    @kind = kind
  end

  def to_sexp()
    return "(pre-decr " + self.operand.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithPostDecr
  attr_accessor :operand, :kind

  def initialize(operand: nil, kind: "")
    @operand = operand
    @kind = kind
  end

  def to_sexp()
    return "(post-decr " + self.operand.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithAssign
  attr_accessor :op, :target, :value, :kind

  def initialize(op: "", target: nil, value: nil, kind: "")
    @op = op
    @target = target
    @value = value
    @kind = kind
  end

  def to_sexp()
    return "(assign \"" + self.op + "\" " + self.target.to_sexp + " " + self.value.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithTernary
  attr_accessor :condition, :if_true, :if_false, :kind

  def initialize(condition: nil, if_true: nil, if_false: nil, kind: "")
    @condition = condition
    @if_true = if_true
    @if_false = if_false
    @kind = kind
  end

  def to_sexp()
    return "(ternary " + self.condition.to_sexp + " " + self.if_true.to_sexp + " " + self.if_false.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithComma
  attr_accessor :left, :right, :kind

  def initialize(left: nil, right: nil, kind: "")
    @left = left
    @right = right
    @kind = kind
  end

  def to_sexp()
    return "(comma " + self.left.to_sexp + " " + self.right.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithSubscript
  attr_accessor :array, :index, :kind

  def initialize(array: "", index: nil, kind: "")
    @array = array
    @index = index
    @kind = kind
  end

  def to_sexp()
    return "(subscript \"" + self.array + "\" " + self.index.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithEscape
  attr_accessor :char, :kind

  def initialize(char: "", kind: "")
    @char = char
    @kind = kind
  end

  def to_sexp()
    return "(escape \"" + self.char + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithDeprecated
  attr_accessor :expression, :kind

  def initialize(expression: "", kind: "")
    @expression = expression
    @kind = kind
  end

  def to_sexp()
    escaped = self.expression.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }.gsub("
") { "\\n" }
    return "(arith-deprecated \"" + escaped + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class ArithConcat
  attr_accessor :parts, :kind

  def initialize(parts: [], kind: "")
    @parts = parts
    @kind = kind
  end

  def to_sexp()
    sexps = []
    (self.parts || []).each do |p_|
      sexps.push(p_.to_sexp)
    end
    return "(arith-concat " + sexps.join(" ") + ")"
  end

  def get_kind()
    return self.kind
  end
end

class AnsiCQuote
  attr_accessor :content, :kind

  def initialize(content: "", kind: "")
    @content = content
    @kind = kind
  end

  def to_sexp()
    escaped = self.content.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }.gsub("
") { "\\n" }
    return "(ansi-c \"" + escaped + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class LocaleString
  attr_accessor :content, :kind

  def initialize(content: "", kind: "")
    @content = content
    @kind = kind
  end

  def to_sexp()
    escaped = self.content.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }.gsub("
") { "\\n" }
    return "(locale \"" + escaped + "\")"
  end

  def get_kind()
    return self.kind
  end
end

class ProcessSubstitution
  attr_accessor :direction, :command, :kind

  def initialize(direction: "", command: nil, kind: "")
    @direction = direction
    @command = command
    @kind = kind
  end

  def to_sexp()
    return "(procsub \"" + self.direction + "\" " + self.command.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class Negation
  attr_accessor :pipeline, :kind

  def initialize(pipeline: nil, kind: "")
    @pipeline = pipeline
    @kind = kind
  end

  def to_sexp()
    if self.pipeline.nil?
      return "(negation (command))"
    end
    return "(negation " + self.pipeline.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class Time_
  attr_accessor :pipeline, :posix, :kind

  def initialize(pipeline: nil, posix: false, kind: "")
    @pipeline = pipeline
    @posix = posix
    @kind = kind
  end

  def to_sexp()
    if self.pipeline.nil?
      if self.posix
        return "(time -p (command))"
      else
        return "(time (command))"
      end
    end
    if self.posix
      return "(time -p " + self.pipeline.to_sexp + ")"
    end
    return "(time " + self.pipeline.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class ConditionalExpr
  attr_accessor :body, :redirects, :kind

  def initialize(body: nil, redirects: [], kind: "")
    @body = body
    @redirects = redirects
    @kind = kind
  end

  def to_sexp()
    body = self.body
    case body
    when String
      body = body
      escaped = body.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }.gsub("
") { "\\n" }
      result = "(cond \"" + escaped + "\")"
    else
      result = "(cond " + body.to_sexp + ")"
    end
    if (self.redirects && !self.redirects.empty?)
      redirect_parts = []
      (self.redirects || []).each do |r|
        redirect_parts.push(r.to_sexp)
      end
      redirect_sexps = redirect_parts.join(" ")
      return result + " " + redirect_sexps
    end
    return result
  end

  def get_kind()
    return self.kind
  end
end

class UnaryTest
  attr_accessor :op, :operand, :kind

  def initialize(op: "", operand: nil, kind: "")
    @op = op
    @operand = operand
    @kind = kind
  end

  def to_sexp()
    operand_val = self.operand.get_cond_formatted_value
    return "(cond-unary \"" + self.op + "\" (cond-term \"" + operand_val + "\"))"
  end

  def get_kind()
    return self.kind
  end
end

class BinaryTest
  attr_accessor :op, :left, :right, :kind

  def initialize(op: "", left: nil, right: nil, kind: "")
    @op = op
    @left = left
    @right = right
    @kind = kind
  end

  def to_sexp()
    left_val = self.left.get_cond_formatted_value
    right_val = self.right.get_cond_formatted_value
    return "(cond-binary \"" + self.op + "\" (cond-term \"" + left_val + "\") (cond-term \"" + right_val + "\"))"
  end

  def get_kind()
    return self.kind
  end
end

class CondAnd
  attr_accessor :left, :right, :kind

  def initialize(left: nil, right: nil, kind: "")
    @left = left
    @right = right
    @kind = kind
  end

  def to_sexp()
    return "(cond-and " + self.left.to_sexp + " " + self.right.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class CondOr
  attr_accessor :left, :right, :kind

  def initialize(left: nil, right: nil, kind: "")
    @left = left
    @right = right
    @kind = kind
  end

  def to_sexp()
    return "(cond-or " + self.left.to_sexp + " " + self.right.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class CondNot
  attr_accessor :operand, :kind

  def initialize(operand: nil, kind: "")
    @operand = operand
    @kind = kind
  end

  def to_sexp()
    return self.operand.to_sexp
  end

  def get_kind()
    return self.kind
  end
end

class CondParen
  attr_accessor :inner, :kind

  def initialize(inner: nil, kind: "")
    @inner = inner
    @kind = kind
  end

  def to_sexp()
    return "(cond-expr " + self.inner.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class Array_
  attr_accessor :elements, :kind

  def initialize(elements: [], kind: "")
    @elements = elements
    @kind = kind
  end

  def to_sexp()
    if !(self.elements && !self.elements.empty?)
      return "(array)"
    end
    parts = []
    (self.elements || []).each do |e|
      parts.push(e.to_sexp)
    end
    inner = parts.join(" ")
    return "(array " + inner + ")"
  end

  def get_kind()
    return self.kind
  end
end

class Coproc
  attr_accessor :command, :name, :kind

  def initialize(command: nil, name: "", kind: "")
    @command = command
    @name = name
    @kind = kind
  end

  def to_sexp()
    if (self.name && !self.name.empty?)
      name = self.name
    else
      name = "COPROC"
    end
    return "(coproc \"" + name + "\" " + self.command.to_sexp + ")"
  end

  def get_kind()
    return self.kind
  end
end

class Parser
  attr_accessor :source, :pos, :length, :pending_heredocs, :cmdsub_heredoc_end, :saw_newline_in_single_quote, :in_process_sub, :extglob, :ctx, :lexer, :token_history, :parser_state, :dolbrace_state, :eof_token, :word_context, :at_command_start, :in_array_literal, :in_assign_builtin, :arith_src, :arith_pos, :arith_len

  def initialize(source: "", pos: 0, length: 0, pending_heredocs: [], cmdsub_heredoc_end: 0, saw_newline_in_single_quote: false, in_process_sub: false, extglob: false, ctx: nil, lexer: nil, token_history: [], parser_state: 0, dolbrace_state: 0, eof_token: "", word_context: 0, at_command_start: false, in_array_literal: false, in_assign_builtin: false, arith_src: "", arith_pos: 0, arith_len: 0)
    @source = source
    @pos = pos
    @length = length
    @pending_heredocs = pending_heredocs
    @cmdsub_heredoc_end = cmdsub_heredoc_end
    @saw_newline_in_single_quote = saw_newline_in_single_quote
    @in_process_sub = in_process_sub
    @extglob = extglob
    @ctx = ctx
    @lexer = lexer
    @token_history = token_history
    @parser_state = parser_state
    @dolbrace_state = dolbrace_state
    @eof_token = eof_token
    @word_context = word_context
    @at_command_start = at_command_start
    @in_array_literal = in_array_literal
    @in_assign_builtin = in_assign_builtin
    @arith_src = arith_src
    @arith_pos = arith_pos
    @arith_len = arith_len
  end

  def set_state(flag)
    self.parser_state = self.parser_state | flag
  end

  def clear_state(flag)
    self.parser_state = self.parser_state & ~flag
  end

  def in_state(flag)
    return (self.parser_state & flag) != 0
  end

  def save_parser_state()
    return SavedParserState.new(parser_state: self.parser_state, dolbrace_state: self.dolbrace_state, pending_heredocs: self.pending_heredocs, ctx_stack: self.ctx.copy_stack, eof_token: self.eof_token)
  end

  def restore_parser_state(saved)
    self.parser_state = saved.parser_state
    self.dolbrace_state = saved.dolbrace_state
    self.eof_token = saved.eof_token
    self.ctx.restore_from(saved.ctx_stack)
  end

  def record_token(tok)
    self.token_history = [tok, self.token_history[0], self.token_history[1], self.token_history[2]]
  end

  def update_dolbrace_for_op(op, has_param)
    if self.dolbrace_state == DOLBRACESTATE_NONE
      return
    end
    if op == "" || op.length == 0
      return
    end
    first_char = op[0]
    if self.dolbrace_state == DOLBRACESTATE_PARAM && has_param
      if "%#^,".include?(first_char)
        self.dolbrace_state = DOLBRACESTATE_QUOTE
        return
      end
      if first_char == "/"
        self.dolbrace_state = DOLBRACESTATE_QUOTE2
        return
      end
    end
    if self.dolbrace_state == DOLBRACESTATE_PARAM
      if "#%^,~:-=?+/".include?(first_char)
        self.dolbrace_state = DOLBRACESTATE_OP
      end
    end
  end

  def sync_lexer()
    if !self.lexer.token_cache.nil?
      if self.lexer.token_cache.pos != self.pos || self.lexer.cached_word_context != self.word_context || self.lexer.cached_at_command_start != self.at_command_start || self.lexer.cached_in_array_literal != self.in_array_literal || self.lexer.cached_in_assign_builtin != self.in_assign_builtin
        self.lexer.token_cache = nil
      end
    end
    if self.lexer.pos != self.pos
      self.lexer.pos = self.pos
    end
    self.lexer.eof_token = self.eof_token
    self.lexer.parser_state = self.parser_state
    self.lexer.last_read_token = self.token_history[0]
    self.lexer.word_context = self.word_context
    self.lexer.at_command_start = self.at_command_start
    self.lexer.in_array_literal = self.in_array_literal
    self.lexer.in_assign_builtin = self.in_assign_builtin
  end

  def sync_parser()
    self.pos = self.lexer.pos
  end

  def lex_peek_token()
    if !self.lexer.token_cache.nil? && self.lexer.token_cache.pos == self.pos && self.lexer.cached_word_context == self.word_context && self.lexer.cached_at_command_start == self.at_command_start && self.lexer.cached_in_array_literal == self.in_array_literal && self.lexer.cached_in_assign_builtin == self.in_assign_builtin
      return self.lexer.token_cache
    end
    saved_pos = self.pos
    self.sync_lexer
    result = self.lexer.peek_token
    self.lexer.cached_word_context = self.word_context
    self.lexer.cached_at_command_start = self.at_command_start
    self.lexer.cached_in_array_literal = self.in_array_literal
    self.lexer.cached_in_assign_builtin = self.in_assign_builtin
    self.lexer.post_read_pos = self.lexer.pos
    self.pos = saved_pos
    return result
  end

  def lex_next_token()
    if !self.lexer.token_cache.nil? && self.lexer.token_cache.pos == self.pos && self.lexer.cached_word_context == self.word_context && self.lexer.cached_at_command_start == self.at_command_start && self.lexer.cached_in_array_literal == self.in_array_literal && self.lexer.cached_in_assign_builtin == self.in_assign_builtin
      tok = self.lexer.next_token
      self.pos = self.lexer.post_read_pos
      self.lexer.pos = self.lexer.post_read_pos
    else
      self.sync_lexer
      tok = self.lexer.next_token
      self.lexer.cached_word_context = self.word_context
      self.lexer.cached_at_command_start = self.at_command_start
      self.lexer.cached_in_array_literal = self.in_array_literal
      self.lexer.cached_in_assign_builtin = self.in_assign_builtin
      self.sync_parser
    end
    self.record_token(tok)
    return tok
  end

  def lex_skip_blanks()
    self.sync_lexer
    self.lexer.skip_blanks
    self.sync_parser
  end

  def lex_skip_comment()
    self.sync_lexer
    result = self.lexer.skip_comment
    self.sync_parser
    return result
  end

  def lex_is_command_terminator()
    tok = self.lex_peek_token
    t = tok.type
    return t == TOKENTYPE_EOF || t == TOKENTYPE_NEWLINE || t == TOKENTYPE_PIPE || t == TOKENTYPE_SEMI || t == TOKENTYPE_LPAREN || t == TOKENTYPE_RPAREN || t == TOKENTYPE_AMP
  end

  def lex_peek_operator()
    tok = self.lex_peek_token
    t = tok.type
    if t >= TOKENTYPE_SEMI && t <= TOKENTYPE_GREATER || t >= TOKENTYPE_AND_AND && t <= TOKENTYPE_PIPE_AMP
      return [t, tok.value]
    end
    return [0, ""]
  end

  def lex_peek_reserved_word()
    tok = self.lex_peek_token
    if tok.type != TOKENTYPE_WORD
      return ""
    end
    word = tok.value
    if word.end_with?("\\\n")
      word = word[0...-2]
    end
    if (RESERVED_WORDS.include?(word)) || word == "{" || word == "}" || word == "[[" || word == "]]" || word == "!" || word == "time"
      return word
    end
    return ""
  end

  def lex_is_at_reserved_word(word)
    reserved = self.lex_peek_reserved_word
    return reserved == word
  end

  def lex_consume_word(expected)
    tok = self.lex_peek_token
    if tok.type != TOKENTYPE_WORD
      return false
    end
    word = tok.value
    if word.end_with?("\\\n")
      word = word[0...-2]
    end
    if word == expected
      self.lex_next_token
      return true
    end
    return false
  end

  def lex_peek_case_terminator()
    tok = self.lex_peek_token
    t = tok.type
    if t == TOKENTYPE_SEMI_SEMI
      return ";;"
    end
    if t == TOKENTYPE_SEMI_AMP
      return ";&"
    end
    if t == TOKENTYPE_SEMI_SEMI_AMP
      return ";;&"
    end
    return ""
  end

  def at_end()
    return self.pos >= self.length
  end

  def peek()
    if self.at_end
      return ""
    end
    return self.source[self.pos]
  end

  def advance()
    if self.at_end
      return ""
    end
    ch = self.source[self.pos]
    self.pos += 1
    return ch
  end

  def peek_at(offset)
    pos = self.pos + offset
    if pos < 0 || pos >= self.length
      return ""
    end
    return self.source[pos]
  end

  def lookahead(n)
    return substring(self.source, self.pos, self.pos + n)
  end

  def is_bang_followed_by_procsub()
    if self.pos + 2 >= self.length
      return false
    end
    next_char = self.source[self.pos + 1]
    if next_char != ">" && next_char != "<"
      return false
    end
    return self.source[self.pos + 2] == "("
  end

  def skip_whitespace()
    while !self.at_end
      self.lex_skip_blanks
      if self.at_end
        break
      end
      ch = self.peek
      if ch == "#"
        self.lex_skip_comment
      elsif ch == "\\" && self.peek_at(1) == "\n"
        self.advance
        self.advance
      else
        break
      end
    end
  end

  def skip_whitespace_and_newlines()
    while !self.at_end
      ch = self.peek
      if is_whitespace(ch)
        self.advance
        if ch == "\n"
          self.gather_heredoc_bodies
          if self.cmdsub_heredoc_end != -1 && self.cmdsub_heredoc_end > self.pos
            self.pos = self.cmdsub_heredoc_end
            self.cmdsub_heredoc_end = -1
          end
        end
      elsif ch == "#"
        while !self.at_end && self.peek != "\n"
          self.advance
        end
      elsif ch == "\\" && self.peek_at(1) == "\n"
        self.advance
        self.advance
      else
        break
      end
    end
  end

  def at_list_terminating_bracket()
    if self.at_end
      return false
    end
    ch = self.peek
    if self.eof_token != "" && ch == self.eof_token
      return true
    end
    if ch == ")"
      return true
    end
    if ch == "}"
      next_pos = self.pos + 1
      if next_pos >= self.length
        return true
      end
      return is_word_end_context(self.source[next_pos])
    end
    return false
  end

  def at_eof_token()
    if self.eof_token == ""
      return false
    end
    tok = self.lex_peek_token
    if self.eof_token == ")"
      return tok.type == TOKENTYPE_RPAREN
    end
    if self.eof_token == "}"
      return tok.type == TOKENTYPE_WORD && tok.value == "}"
    end
    return false
  end

  def collect_redirects()
    redirects = []
    while true
      self.skip_whitespace
      redirect = self.parse_redirect
      if redirect.nil?
        break
      end
      redirects.push(redirect)
    end
    return (redirects && !redirects.empty?) ? redirects : nil
  end

  def parse_loop_body(context)
    if self.peek == "{"
      brace = self.parse_brace_group
      if brace.nil?
        raise ParseError.new(message: "Expected brace group body in #{context}", pos: self.lex_peek_token.pos)
      end
      return brace.body
    end
    if self.lex_consume_word("do")
      body = self.parse_list_until(Set["done"])
      if body.nil?
        raise ParseError.new(message: "Expected commands after 'do'", pos: self.lex_peek_token.pos)
      end
      self.skip_whitespace_and_newlines
      if !self.lex_consume_word("done")
        raise ParseError.new(message: "Expected 'done' to close #{context}", pos: self.lex_peek_token.pos)
      end
      return body
    end
    raise ParseError.new(message: "Expected 'do' or '{' in #{context}", pos: self.lex_peek_token.pos)
  end

  def peek_word()
    saved_pos = self.pos
    self.skip_whitespace
    if self.at_end || is_metachar(self.peek)
      self.pos = saved_pos
      return ""
    end
    chars = []
    while !self.at_end && !is_metachar(self.peek)
      ch = self.peek
      if is_quote(ch)
        break
      end
      if ch == "\\" && self.pos + 1 < self.length && self.source[self.pos + 1] == "\n"
        break
      end
      if ch == "\\" && self.pos + 1 < self.length
        chars.push(self.advance)
        chars.push(self.advance)
        next
      end
      chars.push(self.advance)
    end
    if (chars && !chars.empty?)
      word = chars.join
    else
      word = ""
    end
    self.pos = saved_pos
    return word
  end

  def consume_word(expected)
    saved_pos = self.pos
    self.skip_whitespace
    word = self.peek_word
    keyword_word = word
    has_leading_brace = false
    if word != "" && self.in_process_sub && word.length > 1 && word[0] == "}"
      keyword_word = word[1..]
      has_leading_brace = true
    end
    if keyword_word != expected
      self.pos = saved_pos
      return false
    end
    self.skip_whitespace
    if has_leading_brace
      self.advance
    end
    expected.each_char do
      self.advance
    end
    while self.peek == "\\" && self.pos + 1 < self.length && self.source[self.pos + 1] == "\n"
      self.advance
      self.advance
    end
    return true
  end

  def is_word_terminator(ctx, ch, bracket_depth = 0, paren_depth = 0)
    self.sync_lexer
    return self.lexer.is_word_terminator(ctx, ch, bracket_depth, paren_depth)
  end

  def scan_double_quote(chars, parts, start, handle_line_continuation = true)
    chars.append("\"")
    while !self.at_end && self.peek != "\""
      c = self.peek
      if c == "\\" && self.pos + 1 < self.length
        next_c = self.source[self.pos + 1]
        if handle_line_continuation && next_c == "\n"
          self.advance
          self.advance
        else
          chars.append(self.advance)
          chars.append(self.advance)
        end
      elsif c == "$"
        if !self.parse_dollar_expansion(chars, parts, true)
          chars.append(self.advance)
        end
      else
        chars.append(self.advance)
      end
    end
    if self.at_end
      raise ParseError.new(message: "Unterminated double quote", pos: start)
    end
    chars.append(self.advance)
  end

  def parse_dollar_expansion(chars, parts, in_dquote = false)
    if self.pos + 2 < self.length && self.source[self.pos + 1] == "(" && self.source[self.pos + 2] == "("
      result0, result1 = self.parse_arithmetic_expansion
      if !result0.nil?
        parts.append(result0)
        chars.append(result1)
        return true
      end
      result0, result1 = self.parse_command_substitution
      if !result0.nil?
        parts.append(result0)
        chars.append(result1)
        return true
      end
      return false
    end
    if self.pos + 1 < self.length && self.source[self.pos + 1] == "["
      result0, result1 = self.parse_deprecated_arithmetic
      if !result0.nil?
        parts.append(result0)
        chars.append(result1)
        return true
      end
      return false
    end
    if self.pos + 1 < self.length && self.source[self.pos + 1] == "("
      result0, result1 = self.parse_command_substitution
      if !result0.nil?
        parts.append(result0)
        chars.append(result1)
        return true
      end
      return false
    end
    result0, result1 = self.parse_param_expansion(in_dquote)
    if !result0.nil?
      parts.append(result0)
      chars.append(result1)
      return true
    end
    return false
  end

  def parse_word_internal(ctx, at_command_start = false, in_array_literal = false)
    self.word_context = ctx
    return self.parse_word(at_command_start, in_array_literal, false)
  end

  def parse_word(at_command_start = false, in_array_literal = false, in_assign_builtin = false)
    self.skip_whitespace
    if self.at_end
      return nil
    end
    self.at_command_start = at_command_start
    self.in_array_literal = in_array_literal
    self.in_assign_builtin = in_assign_builtin
    tok = self.lex_peek_token
    if tok.type != TOKENTYPE_WORD
      self.at_command_start = false
      self.in_array_literal = false
      self.in_assign_builtin = false
      return nil
    end
    self.lex_next_token
    self.at_command_start = false
    self.in_array_literal = false
    self.in_assign_builtin = false
    return tok.word
  end

  def parse_command_substitution()
    if self.at_end || self.peek != "$"
      return [nil, ""]
    end
    start = self.pos
    self.advance
    if self.at_end || self.peek != "("
      self.pos = start
      return [nil, ""]
    end
    self.advance
    saved = self.save_parser_state
    self.set_state(PARSERSTATEFLAGS_PST_CMDSUBST | PARSERSTATEFLAGS_PST_EOFTOKEN)
    self.eof_token = ")"
    cmd = self.parse_list(true)
    if cmd.nil?
      cmd = Empty.new(kind: "empty")
    end
    self.skip_whitespace_and_newlines
    if self.at_end || self.peek != ")"
      self.restore_parser_state(saved)
      self.pos = start
      return [nil, ""]
    end
    self.advance
    text_end = self.pos
    text = substring(self.source, start, text_end)
    self.restore_parser_state(saved)
    return [CommandSubstitution.new(command: cmd, kind: "cmdsub"), text]
  end

  def parse_funsub(start)
    self.sync_parser
    if !self.at_end && self.peek == "|"
      self.advance
    end
    saved = self.save_parser_state
    self.set_state(PARSERSTATEFLAGS_PST_CMDSUBST | PARSERSTATEFLAGS_PST_EOFTOKEN)
    self.eof_token = "}"
    cmd = self.parse_list(true)
    if cmd.nil?
      cmd = Empty.new(kind: "empty")
    end
    self.skip_whitespace_and_newlines
    if self.at_end || self.peek != "}"
      self.restore_parser_state(saved)
      raise MatchedPairError.new(message: "unexpected EOF looking for `}'", pos: start)
    end
    self.advance
    text = substring(self.source, start, self.pos)
    self.restore_parser_state(saved)
    self.sync_lexer
    return [CommandSubstitution.new(command: cmd, brace: true, kind: "cmdsub"), text]
  end

  def is_assignment_word(word)
    return assignment(word.value, 0) != -1
  end

  def parse_backtick_substitution()
    if self.at_end || self.peek != "`"
      return [nil, ""]
    end
    start = self.pos
    self.advance
    content_chars = []
    text_chars = ["`"]
    pending_heredocs = []
    in_heredoc_body = false
    current_heredoc_delim = ""
    current_heredoc_strip = false
    while !self.at_end && (in_heredoc_body || self.peek != "`")
      if in_heredoc_body
        line_start = self.pos
        line_end = line_start
        while line_end < self.length && self.source[line_end] != "\n"
          line_end += 1
        end
        line = substring(self.source, line_start, line_end)
        check_line = current_heredoc_strip ? line.gsub(/\A[\t]+/, '') : line
        if check_line == current_heredoc_delim
          line.each_char do |ch|
            content_chars.push(ch)
            text_chars.push(ch)
          end
          self.pos = line_end
          if self.pos < self.length && self.source[self.pos] == "\n"
            content_chars.push("\n")
            text_chars.push("\n")
            self.advance
          end
          in_heredoc_body = false
          if pending_heredocs.length > 0
            current_heredoc_delim, current_heredoc_strip = pending_heredocs.shift
            in_heredoc_body = true
          end
        elsif check_line.start_with?(current_heredoc_delim) && check_line.length > current_heredoc_delim.length
          tabs_stripped = line.length - check_line.length
          end_pos = tabs_stripped + current_heredoc_delim.length
          i = 0
          while i < end_pos
            content_chars.push(line[i])
            text_chars.push(line[i])
            i += 1
          end
          self.pos = line_start + end_pos
          in_heredoc_body = false
          if pending_heredocs.length > 0
            current_heredoc_delim, current_heredoc_strip = pending_heredocs.shift
            in_heredoc_body = true
          end
        else
          line.each_char do |ch|
            content_chars.push(ch)
            text_chars.push(ch)
          end
          self.pos = line_end
          if self.pos < self.length && self.source[self.pos] == "\n"
            content_chars.push("\n")
            text_chars.push("\n")
            self.advance
          end
        end
        next
      end
      c = self.peek
      if c == "\\" && self.pos + 1 < self.length
        next_c = self.source[self.pos + 1]
        if next_c == "\n"
          self.advance
          self.advance
        elsif is_escape_char_in_backtick(next_c)
          self.advance
          escaped = self.advance
          content_chars.push(escaped)
          text_chars.push("\\")
          text_chars.push(escaped)
        else
          ch = self.advance
          content_chars.push(ch)
          text_chars.push(ch)
        end
        next
      end
      if c == "<" && self.pos + 1 < self.length && self.source[self.pos + 1] == "<"
        if self.pos + 2 < self.length && self.source[self.pos + 2] == "<"
          content_chars.push(self.advance)
          text_chars.push("<")
          content_chars.push(self.advance)
          text_chars.push("<")
          content_chars.push(self.advance)
          text_chars.push("<")
          while !self.at_end && is_whitespace_no_newline(self.peek)
            ch = self.advance
            content_chars.push(ch)
            text_chars.push(ch)
          end
          while !self.at_end && !is_whitespace(self.peek) && (!"()".include?(self.peek))
            if self.peek == "\\" && self.pos + 1 < self.length
              ch = self.advance
              content_chars.push(ch)
              text_chars.push(ch)
              ch = self.advance
              content_chars.push(ch)
              text_chars.push(ch)
            elsif "\"'".include?(self.peek)
              quote = self.peek
              ch = self.advance
              content_chars.push(ch)
              text_chars.push(ch)
              while !self.at_end && self.peek != quote
                if quote == "\"" && self.peek == "\\"
                  ch = self.advance
                  content_chars.push(ch)
                  text_chars.push(ch)
                end
                ch = self.advance
                content_chars.push(ch)
                text_chars.push(ch)
              end
              if !self.at_end
                ch = self.advance
                content_chars.push(ch)
                text_chars.push(ch)
              end
            else
              ch = self.advance
              content_chars.push(ch)
              text_chars.push(ch)
            end
          end
          next
        end
        content_chars.push(self.advance)
        text_chars.push("<")
        content_chars.push(self.advance)
        text_chars.push("<")
        strip_tabs = false
        if !self.at_end && self.peek == "-"
          strip_tabs = true
          content_chars.push(self.advance)
          text_chars.push("-")
        end
        while !self.at_end && is_whitespace_no_newline(self.peek)
          ch = self.advance
          content_chars.push(ch)
          text_chars.push(ch)
        end
        delimiter_chars = []
        if !self.at_end
          ch = self.peek
          if is_quote(ch)
            quote = self.advance
            content_chars.push(quote)
            text_chars.push(quote)
            while !self.at_end && self.peek != quote
              dch = self.advance
              content_chars.push(dch)
              text_chars.push(dch)
              delimiter_chars.push(dch)
            end
            if !self.at_end
              closing = self.advance
              content_chars.push(closing)
              text_chars.push(closing)
            end
          elsif ch == "\\"
            esc = self.advance
            content_chars.push(esc)
            text_chars.push(esc)
            if !self.at_end
              dch = self.advance
              content_chars.push(dch)
              text_chars.push(dch)
              delimiter_chars.push(dch)
            end
            while !self.at_end && !is_metachar(self.peek)
              dch = self.advance
              content_chars.push(dch)
              text_chars.push(dch)
              delimiter_chars.push(dch)
            end
          else
            while !self.at_end && !is_metachar(self.peek) && self.peek != "`"
              ch = self.peek
              if is_quote(ch)
                quote = self.advance
                content_chars.push(quote)
                text_chars.push(quote)
                while !self.at_end && self.peek != quote
                  dch = self.advance
                  content_chars.push(dch)
                  text_chars.push(dch)
                  delimiter_chars.push(dch)
                end
                if !self.at_end
                  closing = self.advance
                  content_chars.push(closing)
                  text_chars.push(closing)
                end
              elsif ch == "\\"
                esc = self.advance
                content_chars.push(esc)
                text_chars.push(esc)
                if !self.at_end
                  dch = self.advance
                  content_chars.push(dch)
                  text_chars.push(dch)
                  delimiter_chars.push(dch)
                end
              else
                dch = self.advance
                content_chars.push(dch)
                text_chars.push(dch)
                delimiter_chars.push(dch)
              end
            end
          end
        end
        delimiter = delimiter_chars.join
        if (delimiter && !delimiter.empty?)
          pending_heredocs.push([delimiter, strip_tabs])
        end
        next
      end
      if c == "\n"
        ch = self.advance
        content_chars.push(ch)
        text_chars.push(ch)
        if pending_heredocs.length > 0
          current_heredoc_delim, current_heredoc_strip = pending_heredocs.shift
          in_heredoc_body = true
        end
        next
      end
      ch = self.advance
      content_chars.push(ch)
      text_chars.push(ch)
    end
    if self.at_end
      raise ParseError.new(message: "Unterminated backtick", pos: start)
    end
    self.advance
    text_chars.push("`")
    text = text_chars.join
    content = content_chars.join
    if pending_heredocs.length > 0
      heredoc_start, heredoc_end = find_heredoc_content_end(self.source, self.pos, pending_heredocs)
      if heredoc_end > heredoc_start
        content = content + substring(self.source, heredoc_start, heredoc_end)
        if self.cmdsub_heredoc_end == -1
          self.cmdsub_heredoc_end = heredoc_end
        else
          self.cmdsub_heredoc_end = self.cmdsub_heredoc_end > heredoc_end ? self.cmdsub_heredoc_end : heredoc_end
        end
      end
    end
    sub_parser = new_parser(content, false, self.extglob)
    cmd = sub_parser.parse_list(true)
    if cmd.nil?
      cmd = Empty.new(kind: "empty")
    end
    return [CommandSubstitution.new(command: cmd, kind: "cmdsub"), text]
  end

  def parse_process_substitution()
    if self.at_end || !is_redirect_char(self.peek)
      return [nil, ""]
    end
    start = self.pos
    direction = self.advance
    if self.at_end || self.peek != "("
      self.pos = start
      return [nil, ""]
    end
    self.advance
    saved = self.save_parser_state
    old_in_process_sub = self.in_process_sub
    self.in_process_sub = true
    self.set_state(PARSERSTATEFLAGS_PST_EOFTOKEN)
    self.eof_token = ")"
    begin
      cmd = self.parse_list(true)
      if cmd.nil?
        cmd = Empty.new(kind: "empty")
      end
      self.skip_whitespace_and_newlines
      if self.at_end || self.peek != ")"
        raise ParseError.new(message: "Invalid process substitution", pos: start)
      end
      self.advance
      text_end = self.pos
      text = substring(self.source, start, text_end)
      text = strip_line_continuations_comment_aware(text)
      self.restore_parser_state(saved)
      self.in_process_sub = old_in_process_sub
      return [ProcessSubstitution.new(direction: direction, command: cmd, kind: "procsub"), text]
    rescue ParseError => e
      self.restore_parser_state(saved)
      self.in_process_sub = old_in_process_sub
      content_start_char = start + 2 < self.length ? self.source[start + 2] : ""
      if " \t\n".include?(content_start_char)
        raise e
      end
      self.pos = start + 2
      self.lexer.pos = self.pos
      self.lexer.parse_matched_pair("(", ")", 0, false)
      self.pos = self.lexer.pos
      text = substring(self.source, start, self.pos)
      text = strip_line_continuations_comment_aware(text)
      return [nil, text]
    end
  end

  def parse_array_literal()
    if self.at_end || self.peek != "("
      return [nil, ""]
    end
    start = self.pos
    self.advance
    self.set_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
    elements = []
    while true
      self.skip_whitespace_and_newlines
      if self.at_end
        self.clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
        raise ParseError.new(message: "Unterminated array literal", pos: start)
      end
      if self.peek == ")"
        break
      end
      word = self.parse_word(false, true, false)
      if word.nil?
        if self.peek == ")"
          break
        end
        self.clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
        raise ParseError.new(message: "Expected word in array literal", pos: self.pos)
      end
      elements.push(word)
    end
    if self.at_end || self.peek != ")"
      self.clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
      raise ParseError.new(message: "Expected ) to close array literal", pos: self.pos)
    end
    self.advance
    text = substring(self.source, start, self.pos)
    self.clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
    return [Array_.new(elements: elements, kind: "array"), text]
  end

  def parse_arithmetic_expansion()
    if self.at_end || self.peek != "$"
      return [nil, ""]
    end
    start = self.pos
    if self.pos + 2 >= self.length || self.source[self.pos + 1] != "(" || self.source[self.pos + 2] != "("
      return [nil, ""]
    end
    self.advance
    self.advance
    self.advance
    content_start = self.pos
    depth = 2
    first_close_pos = -1
    while !self.at_end && depth > 0
      c = self.peek
      if c == "'"
        self.advance
        while !self.at_end && self.peek != "'"
          self.advance
        end
        if !self.at_end
          self.advance
        end
      elsif c == "\""
        self.advance
        while !self.at_end
          if self.peek == "\\" && self.pos + 1 < self.length
            self.advance
            self.advance
          elsif self.peek == "\""
            self.advance
            break
          else
            self.advance
          end
        end
      elsif c == "\\" && self.pos + 1 < self.length
        self.advance
        self.advance
      elsif c == "("
        depth += 1
        self.advance
      elsif c == ")"
        if depth == 2
          first_close_pos = self.pos
        end
        depth -= 1
        if depth == 0
          break
        end
        self.advance
      else
        if depth == 1
          first_close_pos = -1
        end
        self.advance
      end
    end
    if depth != 0
      if self.at_end
        raise MatchedPairError.new(message: "unexpected EOF looking for `))'", pos: start)
      end
      self.pos = start
      return [nil, ""]
    end
    if first_close_pos != -1
      content = substring(self.source, content_start, first_close_pos)
    else
      content = substring(self.source, content_start, self.pos)
    end
    self.advance
    text = substring(self.source, start, self.pos)
    begin
      expr = self.parse_arith_expr(content)
    rescue ParseError => _e
      self.pos = start
      return [nil, ""]
    end
    return [ArithmeticExpansion.new(expression: expr, kind: "arith"), text]
  end

  def parse_arith_expr(content)
    saved_arith_src = self.arith_src
    saved_arith_pos = self.arith_pos
    saved_arith_len = self.arith_len
    saved_parser_state = self.parser_state
    self.set_state(PARSERSTATEFLAGS_PST_ARITH)
    self.arith_src = content
    self.arith_pos = 0
    self.arith_len = content.length
    self.arith_skip_ws
    if self.arith_at_end
      result = nil
    else
      result = self.arith_parse_comma
    end
    self.parser_state = saved_parser_state
    if saved_arith_src != ""
      self.arith_src = saved_arith_src
      self.arith_pos = saved_arith_pos
      self.arith_len = saved_arith_len
    end
    return result
  end

  def arith_at_end()
    return self.arith_pos >= self.arith_len
  end

  def arith_peek(offset = 0)
    pos = self.arith_pos + offset
    if pos >= self.arith_len
      return ""
    end
    return self.arith_src[pos]
  end

  def arith_advance()
    if self.arith_at_end
      return ""
    end
    c = self.arith_src[self.arith_pos]
    self.arith_pos += 1
    return c
  end

  def arith_skip_ws()
    while !self.arith_at_end
      c = self.arith_src[self.arith_pos]
      if is_whitespace(c)
        self.arith_pos += 1
      elsif c == "\\" && self.arith_pos + 1 < self.arith_len && self.arith_src[self.arith_pos + 1] == "\n"
        self.arith_pos += 2
      else
        break
      end
    end
  end

  def arith_match(s)
    return starts_with_at(self.arith_src, self.arith_pos, s)
  end

  def arith_consume(s)
    if self.arith_match(s)
      self.arith_pos += s.length
      return true
    end
    return false
  end

  def arith_parse_comma()
    left = self.arith_parse_assign
    while true
      self.arith_skip_ws
      if self.arith_consume(",")
        self.arith_skip_ws
        right = self.arith_parse_assign
        left = ArithComma.new(left: left, right: right, kind: "comma")
      else
        break
      end
    end
    return left
  end

  def arith_parse_assign()
    left = self.arith_parse_ternary
    self.arith_skip_ws
    assign_ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="]
    assign_ops.each do |op|
      if self.arith_match(op)
        if op == "=" && self.arith_peek(1) == "="
          break
        end
        self.arith_consume(op)
        self.arith_skip_ws
        right = self.arith_parse_assign
        return ArithAssign.new(op: op, target: left, value: right, kind: "assign")
      end
    end
    return left
  end

  def arith_parse_ternary()
    cond = self.arith_parse_logical_or
    self.arith_skip_ws
    if self.arith_consume("?")
      self.arith_skip_ws
      if self.arith_match(":")
        if_true = nil
      else
        if_true = self.arith_parse_assign
      end
      self.arith_skip_ws
      if self.arith_consume(":")
        self.arith_skip_ws
        if self.arith_at_end || self.arith_peek(0) == ")"
          if_false = nil
        else
          if_false = self.arith_parse_ternary
        end
      else
        if_false = nil
      end
      return ArithTernary.new(condition: cond, if_true: if_true, if_false: if_false, kind: "ternary")
    end
    return cond
  end

  def arith_parse_left_assoc(ops, parsefn)
    left = parsefn.call
    while true
      self.arith_skip_ws
      matched = false
      ops.each do |op|
        if self.arith_match(op)
          self.arith_consume(op)
          self.arith_skip_ws
          left = ArithBinaryOp.new(op: op, left: left, right: parsefn.call, kind: "binary-op")
          matched = true
          break
        end
      end
      if !matched
        break
      end
    end
    return left
  end

  def arith_parse_logical_or()
    return self.arith_parse_left_assoc(["||"], self.method(:arith_parse_logical_and))
  end

  def arith_parse_logical_and()
    return self.arith_parse_left_assoc(["&&"], self.method(:arith_parse_bitwise_or))
  end

  def arith_parse_bitwise_or()
    left = self.arith_parse_bitwise_xor
    while true
      self.arith_skip_ws
      if self.arith_peek(0) == "|" && self.arith_peek(1) != "|" && self.arith_peek(1) != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_bitwise_xor
        left = ArithBinaryOp.new(op: "|", left: left, right: right, kind: "binary-op")
      else
        break
      end
    end
    return left
  end

  def arith_parse_bitwise_xor()
    left = self.arith_parse_bitwise_and
    while true
      self.arith_skip_ws
      if self.arith_peek(0) == "^" && self.arith_peek(1) != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_bitwise_and
        left = ArithBinaryOp.new(op: "^", left: left, right: right, kind: "binary-op")
      else
        break
      end
    end
    return left
  end

  def arith_parse_bitwise_and()
    left = self.arith_parse_equality
    while true
      self.arith_skip_ws
      if self.arith_peek(0) == "&" && self.arith_peek(1) != "&" && self.arith_peek(1) != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_equality
        left = ArithBinaryOp.new(op: "&", left: left, right: right, kind: "binary-op")
      else
        break
      end
    end
    return left
  end

  def arith_parse_equality()
    return self.arith_parse_left_assoc(["==", "!="], self.method(:arith_parse_comparison))
  end

  def arith_parse_comparison()
    left = self.arith_parse_shift
    while true
      self.arith_skip_ws
      if self.arith_match("<=")
        self.arith_consume("<=")
        self.arith_skip_ws
        right = self.arith_parse_shift
        left = ArithBinaryOp.new(op: "<=", left: left, right: right, kind: "binary-op")
      elsif self.arith_match(">=")
        self.arith_consume(">=")
        self.arith_skip_ws
        right = self.arith_parse_shift
        left = ArithBinaryOp.new(op: ">=", left: left, right: right, kind: "binary-op")
      elsif self.arith_peek(0) == "<" && self.arith_peek(1) != "<" && self.arith_peek(1) != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_shift
        left = ArithBinaryOp.new(op: "<", left: left, right: right, kind: "binary-op")
      elsif self.arith_peek(0) == ">" && self.arith_peek(1) != ">" && self.arith_peek(1) != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_shift
        left = ArithBinaryOp.new(op: ">", left: left, right: right, kind: "binary-op")
      else
        break
      end
    end
    return left
  end

  def arith_parse_shift()
    left = self.arith_parse_additive
    while true
      self.arith_skip_ws
      if self.arith_match("<<=")
        break
      end
      if self.arith_match(">>=")
        break
      end
      if self.arith_match("<<")
        self.arith_consume("<<")
        self.arith_skip_ws
        right = self.arith_parse_additive
        left = ArithBinaryOp.new(op: "<<", left: left, right: right, kind: "binary-op")
      elsif self.arith_match(">>")
        self.arith_consume(">>")
        self.arith_skip_ws
        right = self.arith_parse_additive
        left = ArithBinaryOp.new(op: ">>", left: left, right: right, kind: "binary-op")
      else
        break
      end
    end
    return left
  end

  def arith_parse_additive()
    left = self.arith_parse_multiplicative
    while true
      self.arith_skip_ws
      c = self.arith_peek(0)
      c2 = self.arith_peek(1)
      if c == "+" && c2 != "+" && c2 != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_multiplicative
        left = ArithBinaryOp.new(op: "+", left: left, right: right, kind: "binary-op")
      elsif c == "-" && c2 != "-" && c2 != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_multiplicative
        left = ArithBinaryOp.new(op: "-", left: left, right: right, kind: "binary-op")
      else
        break
      end
    end
    return left
  end

  def arith_parse_multiplicative()
    left = self.arith_parse_exponentiation
    while true
      self.arith_skip_ws
      c = self.arith_peek(0)
      c2 = self.arith_peek(1)
      if c == "*" && c2 != "*" && c2 != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_exponentiation
        left = ArithBinaryOp.new(op: "*", left: left, right: right, kind: "binary-op")
      elsif c == "/" && c2 != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_exponentiation
        left = ArithBinaryOp.new(op: "/", left: left, right: right, kind: "binary-op")
      elsif c == "%" && c2 != "="
        self.arith_advance
        self.arith_skip_ws
        right = self.arith_parse_exponentiation
        left = ArithBinaryOp.new(op: "%", left: left, right: right, kind: "binary-op")
      else
        break
      end
    end
    return left
  end

  def arith_parse_exponentiation()
    left = self.arith_parse_unary
    self.arith_skip_ws
    if self.arith_match("**")
      self.arith_consume("**")
      self.arith_skip_ws
      right = self.arith_parse_exponentiation
      return ArithBinaryOp.new(op: "**", left: left, right: right, kind: "binary-op")
    end
    return left
  end

  def arith_parse_unary()
    self.arith_skip_ws
    if self.arith_match("++")
      self.arith_consume("++")
      self.arith_skip_ws
      operand = self.arith_parse_unary
      return ArithPreIncr.new(operand: operand, kind: "pre-incr")
    end
    if self.arith_match("--")
      self.arith_consume("--")
      self.arith_skip_ws
      operand = self.arith_parse_unary
      return ArithPreDecr.new(operand: operand, kind: "pre-decr")
    end
    c = self.arith_peek(0)
    if c == "!"
      self.arith_advance
      self.arith_skip_ws
      operand = self.arith_parse_unary
      return ArithUnaryOp.new(op: "!", operand: operand, kind: "unary-op")
    end
    if c == "~"
      self.arith_advance
      self.arith_skip_ws
      operand = self.arith_parse_unary
      return ArithUnaryOp.new(op: "~", operand: operand, kind: "unary-op")
    end
    if c == "+" && self.arith_peek(1) != "+"
      self.arith_advance
      self.arith_skip_ws
      operand = self.arith_parse_unary
      return ArithUnaryOp.new(op: "+", operand: operand, kind: "unary-op")
    end
    if c == "-" && self.arith_peek(1) != "-"
      self.arith_advance
      self.arith_skip_ws
      operand = self.arith_parse_unary
      return ArithUnaryOp.new(op: "-", operand: operand, kind: "unary-op")
    end
    return self.arith_parse_postfix
  end

  def arith_parse_postfix()
    left = self.arith_parse_primary
    while true
      self.arith_skip_ws
      if self.arith_match("++")
        self.arith_consume("++")
        left = ArithPostIncr.new(operand: left, kind: "post-incr")
      elsif self.arith_match("--")
        self.arith_consume("--")
        left = ArithPostDecr.new(operand: left, kind: "post-decr")
      elsif self.arith_peek(0) == "["
        case left
        when ArithVar
          left = left
          self.arith_advance
          self.arith_skip_ws
          index = self.arith_parse_comma
          self.arith_skip_ws
          if !self.arith_consume("]")
            raise ParseError.new(message: "Expected ']' in array subscript", pos: self.arith_pos)
          end
          left = ArithSubscript.new(array: left.name, index: index, kind: "subscript")
        else
          break
        end
      else
        break
      end
    end
    return left
  end

  def arith_parse_primary()
    self.arith_skip_ws
    c = self.arith_peek(0)
    if c == "("
      self.arith_advance
      self.arith_skip_ws
      expr = self.arith_parse_comma
      self.arith_skip_ws
      if !self.arith_consume(")")
        raise ParseError.new(message: "Expected ')' in arithmetic expression", pos: self.arith_pos)
      end
      return expr
    end
    if c == "#" && self.arith_peek(1) == "$"
      self.arith_advance
      return self.arith_parse_expansion
    end
    if c == "$"
      return self.arith_parse_expansion
    end
    if c == "'"
      return self.arith_parse_single_quote
    end
    if c == "\""
      return self.arith_parse_double_quote
    end
    if c == "`"
      return self.arith_parse_backtick
    end
    if c == "\\"
      self.arith_advance
      if self.arith_at_end
        raise ParseError.new(message: "Unexpected end after backslash in arithmetic", pos: self.arith_pos)
      end
      escaped_char = self.arith_advance
      return ArithEscape.new(char: escaped_char, kind: "escape")
    end
    if self.arith_at_end || (")]:,;?|&<>=!+-*/%^~\#{}".include?(c))
      return ArithEmpty.new(kind: "empty")
    end
    return self.arith_parse_number_or_var
  end

  def arith_parse_expansion()
    if !self.arith_consume("$")
      raise ParseError.new(message: "Expected '$'", pos: self.arith_pos)
    end
    c = self.arith_peek(0)
    if c == "("
      return self.arith_parse_cmdsub
    end
    if c == "{"
      return self.arith_parse_braced_param
    end
    name_chars = []
    while !self.arith_at_end
      ch = self.arith_peek(0)
      if (ch).match?(/\A[[:alnum:]]+\z/) || ch == "_"
        name_chars.push(self.arith_advance)
      elsif (is_special_param_or_digit(ch) || ch == "#") && !(name_chars && !name_chars.empty?)
        name_chars.push(self.arith_advance)
        break
      else
        break
      end
    end
    if !(name_chars && !name_chars.empty?)
      raise ParseError.new(message: "Expected variable name after $", pos: self.arith_pos)
    end
    return ParamExpansion.new(param: name_chars.join, kind: "param")
  end

  def arith_parse_cmdsub()
    self.arith_advance
    if self.arith_peek(0) == "("
      self.arith_advance
      depth = 1
      content_start = self.arith_pos
      while !self.arith_at_end && depth > 0
        ch = self.arith_peek(0)
        if ch == "("
          depth += 1
          self.arith_advance
        elsif ch == ")"
          if depth == 1 && self.arith_peek(1) == ")"
            break
          end
          depth -= 1
          self.arith_advance
        else
          self.arith_advance
        end
      end
      content = substring(self.arith_src, content_start, self.arith_pos)
      self.arith_advance
      self.arith_advance
      inner_expr = self.parse_arith_expr(content)
      return ArithmeticExpansion.new(expression: inner_expr, kind: "arith")
    end
    depth = 1
    content_start = self.arith_pos
    while !self.arith_at_end && depth > 0
      ch = self.arith_peek(0)
      if ch == "("
        depth += 1
        self.arith_advance
      elsif ch == ")"
        depth -= 1
        if depth == 0
          break
        end
        self.arith_advance
      else
        self.arith_advance
      end
    end
    content = substring(self.arith_src, content_start, self.arith_pos)
    self.arith_advance
    sub_parser = new_parser(content, false, self.extglob)
    cmd = sub_parser.parse_list(true)
    return CommandSubstitution.new(command: cmd, kind: "cmdsub")
  end

  def arith_parse_braced_param()
    self.arith_advance
    if self.arith_peek(0) == "!"
      self.arith_advance
      name_chars = []
      while !self.arith_at_end && self.arith_peek(0) != "}"
        name_chars.push(self.arith_advance)
      end
      self.arith_consume("}")
      return ParamIndirect.new(param: name_chars.join, kind: "param-indirect")
    end
    if self.arith_peek(0) == "#"
      self.arith_advance
      name_chars = []
      while !self.arith_at_end && self.arith_peek(0) != "}"
        name_chars.push(self.arith_advance)
      end
      self.arith_consume("}")
      return ParamLength.new(param: name_chars.join, kind: "param-len")
    end
    name_chars = []
    while !self.arith_at_end
      ch = self.arith_peek(0)
      if ch == "}"
        self.arith_advance
        return ParamExpansion.new(param: name_chars.join, kind: "param")
      end
      if is_param_expansion_op(ch)
        break
      end
      name_chars.push(self.arith_advance)
    end
    name = name_chars.join
    op_chars = []
    depth = 1
    while !self.arith_at_end && depth > 0
      ch = self.arith_peek(0)
      if ch == "{"
        depth += 1
        op_chars.push(self.arith_advance)
      elsif ch == "}"
        depth -= 1
        if depth == 0
          break
        end
        op_chars.push(self.arith_advance)
      else
        op_chars.push(self.arith_advance)
      end
    end
    self.arith_consume("}")
    op_str = op_chars.join
    if op_str.start_with?(":-")
      return ParamExpansion.new(param: name, op: ":-", arg: substring(op_str, 2, op_str.length), kind: "param")
    end
    if op_str.start_with?(":=")
      return ParamExpansion.new(param: name, op: ":=", arg: substring(op_str, 2, op_str.length), kind: "param")
    end
    if op_str.start_with?(":+")
      return ParamExpansion.new(param: name, op: ":+", arg: substring(op_str, 2, op_str.length), kind: "param")
    end
    if op_str.start_with?(":?")
      return ParamExpansion.new(param: name, op: ":?", arg: substring(op_str, 2, op_str.length), kind: "param")
    end
    if op_str.start_with?(":")
      return ParamExpansion.new(param: name, op: ":", arg: substring(op_str, 1, op_str.length), kind: "param")
    end
    if op_str.start_with?("##")
      return ParamExpansion.new(param: name, op: "##", arg: substring(op_str, 2, op_str.length), kind: "param")
    end
    if op_str.start_with?("#")
      return ParamExpansion.new(param: name, op: "#", arg: substring(op_str, 1, op_str.length), kind: "param")
    end
    if op_str.start_with?("%%")
      return ParamExpansion.new(param: name, op: "%%", arg: substring(op_str, 2, op_str.length), kind: "param")
    end
    if op_str.start_with?("%")
      return ParamExpansion.new(param: name, op: "%", arg: substring(op_str, 1, op_str.length), kind: "param")
    end
    if op_str.start_with?("//")
      return ParamExpansion.new(param: name, op: "//", arg: substring(op_str, 2, op_str.length), kind: "param")
    end
    if op_str.start_with?("/")
      return ParamExpansion.new(param: name, op: "/", arg: substring(op_str, 1, op_str.length), kind: "param")
    end
    return ParamExpansion.new(param: name, op: "", arg: op_str, kind: "param")
  end

  def arith_parse_single_quote()
    self.arith_advance
    content_start = self.arith_pos
    while !self.arith_at_end && self.arith_peek(0) != "'"
      self.arith_advance
    end
    content = substring(self.arith_src, content_start, self.arith_pos)
    if !self.arith_consume("'")
      raise ParseError.new(message: "Unterminated single quote in arithmetic", pos: self.arith_pos)
    end
    return ArithNumber.new(value: content, kind: "number")
  end

  def arith_parse_double_quote()
    self.arith_advance
    content_start = self.arith_pos
    while !self.arith_at_end && self.arith_peek(0) != "\""
      c = self.arith_peek(0)
      if c == "\\" && !self.arith_at_end
        self.arith_advance
        self.arith_advance
      else
        self.arith_advance
      end
    end
    content = substring(self.arith_src, content_start, self.arith_pos)
    if !self.arith_consume("\"")
      raise ParseError.new(message: "Unterminated double quote in arithmetic", pos: self.arith_pos)
    end
    return ArithNumber.new(value: content, kind: "number")
  end

  def arith_parse_backtick()
    self.arith_advance
    content_start = self.arith_pos
    while !self.arith_at_end && self.arith_peek(0) != "`"
      c = self.arith_peek(0)
      if c == "\\" && !self.arith_at_end
        self.arith_advance
        self.arith_advance
      else
        self.arith_advance
      end
    end
    content = substring(self.arith_src, content_start, self.arith_pos)
    if !self.arith_consume("`")
      raise ParseError.new(message: "Unterminated backtick in arithmetic", pos: self.arith_pos)
    end
    sub_parser = new_parser(content, false, self.extglob)
    cmd = sub_parser.parse_list(true)
    return CommandSubstitution.new(command: cmd, kind: "cmdsub")
  end

  def arith_parse_number_or_var()
    self.arith_skip_ws
    chars = []
    c = self.arith_peek(0)
    if (c).match?(/\A\d+\z/)
      while !self.arith_at_end
        ch = self.arith_peek(0)
        if (ch).match?(/\A[[:alnum:]]+\z/) || ch == "#" || ch == "_"
          chars.push(self.arith_advance)
        else
          break
        end
      end
      prefix = chars.join
      if !self.arith_at_end && self.arith_peek(0) == "$"
        expansion = self.arith_parse_expansion
        return ArithConcat.new(parts: [ArithNumber.new(value: prefix, kind: "number"), expansion], kind: "arith-concat")
      end
      return ArithNumber.new(value: prefix, kind: "number")
    end
    if (c).match?(/\A[[:alpha:]]+\z/) || c == "_"
      while !self.arith_at_end
        ch = self.arith_peek(0)
        if (ch).match?(/\A[[:alnum:]]+\z/) || ch == "_"
          chars.push(self.arith_advance)
        else
          break
        end
      end
      return ArithVar.new(name: chars.join, kind: "var")
    end
    raise ParseError.new(message: "Unexpected character '" + c + "' in arithmetic expression", pos: self.arith_pos)
  end

  def parse_deprecated_arithmetic()
    if self.at_end || self.peek != "$"
      return [nil, ""]
    end
    start = self.pos
    if self.pos + 1 >= self.length || self.source[self.pos + 1] != "["
      return [nil, ""]
    end
    self.advance
    self.advance
    self.lexer.pos = self.pos
    content = self.lexer.parse_matched_pair("[", "]", MATCHEDPAIRFLAGS_ARITH, false)
    self.pos = self.lexer.pos
    text = substring(self.source, start, self.pos)
    return [ArithDeprecated.new(expression: content, kind: "arith-deprecated"), text]
  end

  def parse_param_expansion(in_dquote = false)
    self.sync_lexer
    result0, result1 = self.lexer.read_param_expansion(in_dquote)
    self.sync_parser
    return [result0, result1]
  end

  def parse_redirect()
    self.skip_whitespace
    if self.at_end
      return nil
    end
    start = self.pos
    fd = -1
    varfd = ""
    if self.peek == "{"
      saved = self.pos
      self.advance
      varname_chars = []
      in_bracket = false
      while !self.at_end && !is_redirect_char(self.peek)
        ch = self.peek
        if ch == "}" && !in_bracket
          break
        elsif ch == "["
          in_bracket = true
          varname_chars.push(self.advance)
        elsif ch == "]"
          in_bracket = false
          varname_chars.push(self.advance)
        elsif (ch).match?(/\A[[:alnum:]]+\z/) || ch == "_"
          varname_chars.push(self.advance)
        elsif in_bracket && !is_metachar(ch)
          varname_chars.push(self.advance)
        else
          break
        end
      end
      varname = varname_chars.join
      is_valid_varfd = false
      if (varname && !varname.empty?)
        if (varname[0]).match?(/\A[[:alpha:]]+\z/) || varname[0] == "_"
          if (varname.include?("[")) || (varname.include?("]"))
            left = varname.index("[")
            right = varname.rindex("]")
            if left != -1 && right == varname.length - 1 && right > left + 1
              base = varname[0...left]
              if (base && !base.empty?) && ((base[0]).match?(/\A[[:alpha:]]+\z/) || base[0] == "_")
                is_valid_varfd = true
                base[1..].each_char do |c|
                  if !((c).match?(/\A[[:alnum:]]+\z/) || c == "_")
                    is_valid_varfd = false
                    break
                  end
                end
              end
            end
          else
            is_valid_varfd = true
            varname[1..].each_char do |c|
              if !((c).match?(/\A[[:alnum:]]+\z/) || c == "_")
                is_valid_varfd = false
                break
              end
            end
          end
        end
      end
      if !self.at_end && self.peek == "}" && is_valid_varfd
        self.advance
        varfd = varname
      else
        self.pos = saved
      end
    end
    if varfd == "" && (self.peek && !self.peek.empty?) && (self.peek).match?(/\A\d+\z/)
      fd_chars = []
      while !self.at_end && (self.peek).match?(/\A\d+\z/)
        fd_chars.push(self.advance)
      end
      fd = fd_chars.join.to_i
    end
    ch = self.peek
    if ch == "&" && self.pos + 1 < self.length && self.source[self.pos + 1] == ">"
      if fd != -1 || varfd != ""
        self.pos = start
        return nil
      end
      self.advance
      self.advance
      if !self.at_end && self.peek == ">"
        self.advance
        op = "&>>"
      else
        op = "&>"
      end
      self.skip_whitespace
      target = self.parse_word(false, false, false)
      if target.nil?
        raise ParseError.new(message: "Expected target for redirect " + op, pos: self.pos)
      end
      return Redirect.new(op: op, target: target, kind: "redirect")
    end
    if ch == "" || !is_redirect_char(ch)
      self.pos = start
      return nil
    end
    if fd == -1 && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
      self.pos = start
      return nil
    end
    op = self.advance
    strip_tabs = false
    if !self.at_end
      next_ch = self.peek
      if op == ">" && next_ch == ">"
        self.advance
        op = ">>"
      elsif op == "<" && next_ch == "<"
        self.advance
        if !self.at_end && self.peek == "<"
          self.advance
          op = "<<<"
        elsif !self.at_end && self.peek == "-"
          self.advance
          op = "<<"
          strip_tabs = true
        else
          op = "<<"
        end
      elsif op == "<" && next_ch == ">"
        self.advance
        op = "<>"
      elsif op == ">" && next_ch == "|"
        self.advance
        op = ">|"
      elsif fd == -1 && varfd == "" && op == ">" && next_ch == "&"
        if self.pos + 1 >= self.length || !is_digit_or_dash(self.source[self.pos + 1])
          self.advance
          op = ">&"
        end
      elsif fd == -1 && varfd == "" && op == "<" && next_ch == "&"
        if self.pos + 1 >= self.length || !is_digit_or_dash(self.source[self.pos + 1])
          self.advance
          op = "<&"
        end
      end
    end
    if op == "<<"
      return self.parse_heredoc((fd == -1 ? nil : fd), strip_tabs)
    end
    if varfd != ""
      op = "{" + varfd + "}" + op
    elsif fd != -1
      op = fd.to_s + op
    end
    if !self.at_end && self.peek == "&"
      self.advance
      self.skip_whitespace
      if !self.at_end && self.peek == "-"
        if self.pos + 1 < self.length && !is_metachar(self.source[self.pos + 1])
          self.advance
          target = Word.new(value: "&-", kind: "word")
        else
          target = nil
        end
      else
        target = nil
      end
      if target.nil?
        if !self.at_end && ((self.peek).match?(/\A\d+\z/) || self.peek == "-")
          word_start = self.pos
          fd_chars = []
          while !self.at_end && (self.peek).match?(/\A\d+\z/)
            fd_chars.push(self.advance)
          end
          if (fd_chars && !fd_chars.empty?)
            fd_target = fd_chars.join
          else
            fd_target = ""
          end
          if !self.at_end && self.peek == "-"
            fd_target += self.advance
          end
          if fd_target != "-" && !self.at_end && !is_metachar(self.peek)
            self.pos = word_start
            inner_word = self.parse_word(false, false, false)
            if !inner_word.nil?
              target = Word.new(value: "&" + inner_word.value, kind: "word")
              target.parts = inner_word.parts
            else
              raise ParseError.new(message: "Expected target for redirect " + op, pos: self.pos)
            end
          else
            target = Word.new(value: "&" + fd_target, kind: "word")
          end
        else
          inner_word = self.parse_word(false, false, false)
          if !inner_word.nil?
            target = Word.new(value: "&" + inner_word.value, kind: "word")
            target.parts = inner_word.parts
          else
            raise ParseError.new(message: "Expected target for redirect " + op, pos: self.pos)
          end
        end
      end
    else
      self.skip_whitespace
      if (op == ">&" || op == "<&") && !self.at_end && self.peek == "-"
        if self.pos + 1 < self.length && !is_metachar(self.source[self.pos + 1])
          self.advance
          target = Word.new(value: "&-", kind: "word")
        else
          target = self.parse_word(false, false, false)
        end
      else
        target = self.parse_word(false, false, false)
      end
    end
    if target.nil?
      raise ParseError.new(message: "Expected target for redirect " + op, pos: self.pos)
    end
    return Redirect.new(op: op, target: target, kind: "redirect")
  end

  def parse_heredoc_delimiter()
    self.skip_whitespace
    quoted = false
    delimiter_chars = []
    while true
      while !self.at_end && !is_metachar(self.peek)
        ch = self.peek
        if ch == "\""
          quoted = true
          self.advance
          while !self.at_end && self.peek != "\""
            delimiter_chars.push(self.advance)
          end
          if !self.at_end
            self.advance
          end
        elsif ch == "'"
          quoted = true
          self.advance
          while !self.at_end && self.peek != "'"
            c = self.advance
            if c == "\n"
              self.saw_newline_in_single_quote = true
            end
            delimiter_chars.push(c)
          end
          if !self.at_end
            self.advance
          end
        elsif ch == "\\"
          self.advance
          if !self.at_end
            next_ch = self.peek
            if next_ch == "\n"
              self.advance
            else
              quoted = true
              delimiter_chars.push(self.advance)
            end
          end
        elsif ch == "$" && self.pos + 1 < self.length && self.source[self.pos + 1] == "'"
          quoted = true
          self.advance
          self.advance
          while !self.at_end && self.peek != "'"
            c = self.peek
            if c == "\\" && self.pos + 1 < self.length
              self.advance
              esc = self.peek
              esc_val = get_ansi_escape(esc)
              if esc_val >= 0
                delimiter_chars.push([esc_val].pack('U'))
                self.advance
              elsif esc == "'"
                delimiter_chars.push(self.advance)
              else
                delimiter_chars.push(self.advance)
              end
            else
              delimiter_chars.push(self.advance)
            end
          end
          if !self.at_end
            self.advance
          end
        elsif is_expansion_start(self.source, self.pos, "$(")
          delimiter_chars.push(self.advance)
          delimiter_chars.push(self.advance)
          depth = 1
          while !self.at_end && depth > 0
            c = self.peek
            if c == "("
              depth += 1
            elsif c == ")"
              depth -= 1
            end
            delimiter_chars.push(self.advance)
          end
        elsif ch == "$" && self.pos + 1 < self.length && self.source[self.pos + 1] == "{"
          dollar_count = 0
          j = self.pos - 1
          while j >= 0 && self.source[j] == "$"
            dollar_count += 1
            j -= 1
          end
          if j >= 0 && self.source[j] == "\\"
            dollar_count -= 1
          end
          if dollar_count % 2 == 1
            delimiter_chars.push(self.advance)
          else
            delimiter_chars.push(self.advance)
            delimiter_chars.push(self.advance)
            depth = 0
            while !self.at_end
              c = self.peek
              if c == "{"
                depth += 1
              elsif c == "}"
                delimiter_chars.push(self.advance)
                if depth == 0
                  break
                end
                depth -= 1
                if depth == 0 && !self.at_end && is_metachar(self.peek)
                  break
                end
                next
              end
              delimiter_chars.push(self.advance)
            end
          end
        elsif ch == "$" && self.pos + 1 < self.length && self.source[self.pos + 1] == "["
          dollar_count = 0
          j = self.pos - 1
          while j >= 0 && self.source[j] == "$"
            dollar_count += 1
            j -= 1
          end
          if j >= 0 && self.source[j] == "\\"
            dollar_count -= 1
          end
          if dollar_count % 2 == 1
            delimiter_chars.push(self.advance)
          else
            delimiter_chars.push(self.advance)
            delimiter_chars.push(self.advance)
            depth = 1
            while !self.at_end && depth > 0
              c = self.peek
              if c == "["
                depth += 1
              elsif c == "]"
                depth -= 1
              end
              delimiter_chars.push(self.advance)
            end
          end
        elsif ch == "`"
          delimiter_chars.push(self.advance)
          while !self.at_end && self.peek != "`"
            c = self.peek
            if c == "'"
              delimiter_chars.push(self.advance)
              while !self.at_end && self.peek != "'" && self.peek != "`"
                delimiter_chars.push(self.advance)
              end
              if !self.at_end && self.peek == "'"
                delimiter_chars.push(self.advance)
              end
            elsif c == "\""
              delimiter_chars.push(self.advance)
              while !self.at_end && self.peek != "\"" && self.peek != "`"
                if self.peek == "\\" && self.pos + 1 < self.length
                  delimiter_chars.push(self.advance)
                end
                delimiter_chars.push(self.advance)
              end
              if !self.at_end && self.peek == "\""
                delimiter_chars.push(self.advance)
              end
            elsif c == "\\" && self.pos + 1 < self.length
              delimiter_chars.push(self.advance)
              delimiter_chars.push(self.advance)
            else
              delimiter_chars.push(self.advance)
            end
          end
          if !self.at_end
            delimiter_chars.push(self.advance)
          end
        else
          delimiter_chars.push(self.advance)
        end
      end
      if !self.at_end && ("<>".include?(self.peek)) && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
        delimiter_chars.push(self.advance)
        delimiter_chars.push(self.advance)
        depth = 1
        while !self.at_end && depth > 0
          c = self.peek
          if c == "("
            depth += 1
          elsif c == ")"
            depth -= 1
          end
          delimiter_chars.push(self.advance)
        end
        next
      end
      break
    end
    return [delimiter_chars.join, quoted]
  end

  def read_heredoc_line(quoted)
    line_start = self.pos
    line_end = self.pos
    while line_end < self.length && self.source[line_end] != "\n"
      line_end += 1
    end
    line = substring(self.source, line_start, line_end)
    if !quoted
      while line_end < self.length
        trailing_bs = count_trailing_backslashes(line)
        if trailing_bs % 2 == 0
          break
        end
        line = substring(line, 0, line.length - 1)
        line_end += 1
        next_line_start = line_end
        while line_end < self.length && self.source[line_end] != "\n"
          line_end += 1
        end
        line = line + substring(self.source, next_line_start, line_end)
      end
    end
    return [line, line_end]
  end

  def line_matches_delimiter(line, delimiter, strip_tabs)
    check_line = strip_tabs ? line.gsub(/\A[\t]+/, '') : line
    normalized_check = normalize_heredoc_delimiter(check_line)
    normalized_delim = normalize_heredoc_delimiter(delimiter)
    return [normalized_check == normalized_delim, check_line]
  end

  def gather_heredoc_bodies()
    (self.pending_heredocs || []).each do |heredoc|
      content_lines = []
      line_start = self.pos
      while self.pos < self.length
        line_start = self.pos
        line, line_end = self.read_heredoc_line(heredoc.quoted)
        matches, check_line = self.line_matches_delimiter(line, heredoc.delimiter, heredoc.strip_tabs)
        if matches
          self.pos = line_end < self.length ? line_end + 1 : line_end
          break
        end
        normalized_check = normalize_heredoc_delimiter(check_line)
        normalized_delim = normalize_heredoc_delimiter(heredoc.delimiter)
        if self.eof_token == ")" && normalized_check.start_with?(normalized_delim)
          tabs_stripped = line.length - check_line.length
          self.pos = line_start + tabs_stripped + heredoc.delimiter.length
          break
        end
        if line_end >= self.length && normalized_check.start_with?(normalized_delim) && self.in_process_sub
          tabs_stripped = line.length - check_line.length
          self.pos = line_start + tabs_stripped + heredoc.delimiter.length
          break
        end
        if heredoc.strip_tabs
          line = line.gsub(/\A[\t]+/, '')
        end
        if line_end < self.length
          content_lines.push(line + "\n")
          self.pos = line_end + 1
        else
          add_newline = true
          if !heredoc.quoted && count_trailing_backslashes(line) % 2 == 1
            add_newline = false
          end
          content_lines.push(line + (add_newline ? "\n" : ""))
          self.pos = self.length
        end
      end
      heredoc.content = content_lines.join
    end
    self.pending_heredocs = []
  end

  def parse_heredoc(fd, strip_tabs)
    start_pos = self.pos
    self.set_state(PARSERSTATEFLAGS_PST_HEREDOC)
    delimiter, quoted = self.parse_heredoc_delimiter
    (self.pending_heredocs || []).each do |existing|
      if existing.start_pos == start_pos && existing.delimiter == delimiter
        self.clear_state(PARSERSTATEFLAGS_PST_HEREDOC)
        return existing
      end
    end
    heredoc = HereDoc.new(delimiter: delimiter, content: "", strip_tabs: strip_tabs, quoted: quoted, fd: fd, complete: false, kind: "heredoc")
    heredoc.start_pos = start_pos
    self.pending_heredocs.push(heredoc)
    self.clear_state(PARSERSTATEFLAGS_PST_HEREDOC)
    return heredoc
  end

  def parse_command()
    words = []
    redirects = []
    while true
      self.skip_whitespace
      if self.lex_is_command_terminator
        break
      end
      if words.length == 0
        reserved = self.lex_peek_reserved_word
        if reserved == "}" || reserved == "]]"
          break
        end
      end
      redirect = self.parse_redirect
      if !redirect.nil?
        redirects.push(redirect)
        next
      end
      all_assignments = true
      words.each do |w|
        if !self.is_assignment_word(w)
          all_assignments = false
          break
        end
      end
      in_assign_builtin = words.length > 0 && (ASSIGNMENT_BUILTINS.include?(words[0].value))
      word = self.parse_word(!(words && !words.empty?) || all_assignments && redirects.length == 0, false, in_assign_builtin)
      if word.nil?
        break
      end
      words.push(word)
    end
    if !(words && !words.empty?) && !(redirects && !redirects.empty?)
      return nil
    end
    return Command.new(words: words, redirects: redirects, kind: "command")
  end

  def parse_subshell()
    self.skip_whitespace
    if self.at_end || self.peek != "("
      return nil
    end
    self.advance
    self.set_state(PARSERSTATEFLAGS_PST_SUBSHELL)
    body = self.parse_list(true)
    if body.nil?
      self.clear_state(PARSERSTATEFLAGS_PST_SUBSHELL)
      raise ParseError.new(message: "Expected command in subshell", pos: self.pos)
    end
    self.skip_whitespace
    if self.at_end || self.peek != ")"
      self.clear_state(PARSERSTATEFLAGS_PST_SUBSHELL)
      raise ParseError.new(message: "Expected ) to close subshell", pos: self.pos)
    end
    self.advance
    self.clear_state(PARSERSTATEFLAGS_PST_SUBSHELL)
    return Subshell.new(body: body, redirects: self.collect_redirects, kind: "subshell")
  end

  def parse_arithmetic_command()
    self.skip_whitespace
    if self.at_end || self.peek != "(" || self.pos + 1 >= self.length || self.source[self.pos + 1] != "("
      return nil
    end
    saved_pos = self.pos
    self.advance
    self.advance
    content_start = self.pos
    depth = 1
    while !self.at_end && depth > 0
      c = self.peek
      if c == "'"
        self.advance
        while !self.at_end && self.peek != "'"
          self.advance
        end
        if !self.at_end
          self.advance
        end
      elsif c == "\""
        self.advance
        while !self.at_end
          if self.peek == "\\" && self.pos + 1 < self.length
            self.advance
            self.advance
          elsif self.peek == "\""
            self.advance
            break
          else
            self.advance
          end
        end
      elsif c == "\\" && self.pos + 1 < self.length
        self.advance
        self.advance
      elsif c == "("
        depth += 1
        self.advance
      elsif c == ")"
        if depth == 1 && self.pos + 1 < self.length && self.source[self.pos + 1] == ")"
          break
        end
        depth -= 1
        if depth == 0
          self.pos = saved_pos
          return nil
        end
        self.advance
      else
        self.advance
      end
    end
    if self.at_end
      raise MatchedPairError.new(message: "unexpected EOF looking for `))'", pos: saved_pos)
    end
    if depth != 1
      self.pos = saved_pos
      return nil
    end
    content = substring(self.source, content_start, self.pos)
    content = content.gsub("\\
") { "" }
    self.advance
    self.advance
    expr = self.parse_arith_expr(content)
    return ArithmeticCommand.new(expression: expr, redirects: self.collect_redirects, raw_content: content, kind: "arith-cmd")
  end

  def parse_conditional_expr()
    self.skip_whitespace
    if self.at_end || self.peek != "[" || self.pos + 1 >= self.length || self.source[self.pos + 1] != "["
      return nil
    end
    next_pos = self.pos + 2
    if next_pos < self.length && !(is_whitespace(self.source[next_pos]) || self.source[next_pos] == "\\" && next_pos + 1 < self.length && self.source[next_pos + 1] == "\n")
      return nil
    end
    self.advance
    self.advance
    self.set_state(PARSERSTATEFLAGS_PST_CONDEXPR)
    self.word_context = WORD_CTX_COND
    body = self.parse_cond_or
    while !self.at_end && is_whitespace_no_newline(self.peek)
      self.advance
    end
    if self.at_end || self.peek != "]" || self.pos + 1 >= self.length || self.source[self.pos + 1] != "]"
      self.clear_state(PARSERSTATEFLAGS_PST_CONDEXPR)
      self.word_context = WORD_CTX_NORMAL
      raise ParseError.new(message: "Expected ]] to close conditional expression", pos: self.pos)
    end
    self.advance
    self.advance
    self.clear_state(PARSERSTATEFLAGS_PST_CONDEXPR)
    self.word_context = WORD_CTX_NORMAL
    return ConditionalExpr.new(body: body, redirects: self.collect_redirects, kind: "cond-expr")
  end

  def cond_skip_whitespace()
    while !self.at_end
      if is_whitespace_no_newline(self.peek)
        self.advance
      elsif self.peek == "\\" && self.pos + 1 < self.length && self.source[self.pos + 1] == "\n"
        self.advance
        self.advance
      elsif self.peek == "\n"
        self.advance
      else
        break
      end
    end
  end

  def cond_at_end()
    return self.at_end || self.peek == "]" && self.pos + 1 < self.length && self.source[self.pos + 1] == "]"
  end

  def parse_cond_or()
    self.cond_skip_whitespace
    left = self.parse_cond_and
    self.cond_skip_whitespace
    if !self.cond_at_end && self.peek == "|" && self.pos + 1 < self.length && self.source[self.pos + 1] == "|"
      self.advance
      self.advance
      right = self.parse_cond_or
      return CondOr.new(left: left, right: right, kind: "cond-or")
    end
    return left
  end

  def parse_cond_and()
    self.cond_skip_whitespace
    left = self.parse_cond_term
    self.cond_skip_whitespace
    if !self.cond_at_end && self.peek == "&" && self.pos + 1 < self.length && self.source[self.pos + 1] == "&"
      self.advance
      self.advance
      right = self.parse_cond_and
      return CondAnd.new(left: left, right: right, kind: "cond-and")
    end
    return left
  end

  def parse_cond_term()
    self.cond_skip_whitespace
    if self.cond_at_end
      raise ParseError.new(message: "Unexpected end of conditional expression", pos: self.pos)
    end
    if self.peek == "!"
      if self.pos + 1 < self.length && !is_whitespace_no_newline(self.source[self.pos + 1])
        nil
      else
        self.advance
        operand = self.parse_cond_term
        return CondNot.new(operand: operand, kind: "cond-not")
      end
    end
    if self.peek == "("
      self.advance
      inner = self.parse_cond_or
      self.cond_skip_whitespace
      if self.at_end || self.peek != ")"
        raise ParseError.new(message: "Expected ) in conditional expression", pos: self.pos)
      end
      self.advance
      return CondParen.new(inner: inner, kind: "cond-paren")
    end
    word1 = self.parse_cond_word
    if word1.nil?
      raise ParseError.new(message: "Expected word in conditional expression", pos: self.pos)
    end
    self.cond_skip_whitespace
    if COND_UNARY_OPS.include?(word1.value)
      operand = self.parse_cond_word
      if operand.nil?
        raise ParseError.new(message: "Expected operand after " + word1.value, pos: self.pos)
      end
      return UnaryTest.new(op: word1.value, operand: operand, kind: "unary-test")
    end
    if !self.cond_at_end && self.peek != "&" && self.peek != "|" && self.peek != ")"
      if is_redirect_char(self.peek) && !(self.pos + 1 < self.length && self.source[self.pos + 1] == "(")
        op = self.advance
        self.cond_skip_whitespace
        word2 = self.parse_cond_word
        if word2.nil?
          raise ParseError.new(message: "Expected operand after " + op, pos: self.pos)
        end
        return BinaryTest.new(op: op, left: word1, right: word2, kind: "binary-test")
      end
      saved_pos = self.pos
      op_word = self.parse_cond_word
      if !op_word.nil? && (COND_BINARY_OPS.include?(op_word.value))
        self.cond_skip_whitespace
        if op_word.value == "=~"
          word2 = self.parse_cond_regex_word
        else
          word2 = self.parse_cond_word
        end
        if word2.nil?
          raise ParseError.new(message: "Expected operand after " + op_word.value, pos: self.pos)
        end
        return BinaryTest.new(op: op_word.value, left: word1, right: word2, kind: "binary-test")
      else
        self.pos = saved_pos
      end
    end
    return UnaryTest.new(op: "-n", operand: word1, kind: "unary-test")
  end

  def parse_cond_word()
    self.cond_skip_whitespace
    if self.cond_at_end
      return nil
    end
    c = self.peek
    if is_paren(c)
      return nil
    end
    if c == "&" && self.pos + 1 < self.length && self.source[self.pos + 1] == "&"
      return nil
    end
    if c == "|" && self.pos + 1 < self.length && self.source[self.pos + 1] == "|"
      return nil
    end
    return self.parse_word_internal(WORD_CTX_COND, false, false)
  end

  def parse_cond_regex_word()
    self.cond_skip_whitespace
    if self.cond_at_end
      return nil
    end
    self.set_state(PARSERSTATEFLAGS_PST_REGEXP)
    result = self.parse_word_internal(WORD_CTX_REGEX, false, false)
    self.clear_state(PARSERSTATEFLAGS_PST_REGEXP)
    self.word_context = WORD_CTX_COND
    return result
  end

  def parse_brace_group()
    self.skip_whitespace
    if !self.lex_consume_word("{")
      return nil
    end
    self.skip_whitespace_and_newlines
    body = self.parse_list(true)
    if body.nil?
      raise ParseError.new(message: "Expected command in brace group", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace
    if !self.lex_consume_word("}")
      raise ParseError.new(message: "Expected } to close brace group", pos: self.lex_peek_token.pos)
    end
    return BraceGroup.new(body: body, redirects: self.collect_redirects, kind: "brace-group")
  end

  def parse_if()
    self.skip_whitespace
    if !self.lex_consume_word("if")
      return nil
    end
    condition = self.parse_list_until(Set["then"])
    if condition.nil?
      raise ParseError.new(message: "Expected condition after 'if'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("then")
      raise ParseError.new(message: "Expected 'then' after if condition", pos: self.lex_peek_token.pos)
    end
    then_body = self.parse_list_until(Set["elif", "else", "fi"])
    if then_body.nil?
      raise ParseError.new(message: "Expected commands after 'then'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    else_body = nil
    if self.lex_is_at_reserved_word("elif")
      self.lex_consume_word("elif")
      elif_condition = self.parse_list_until(Set["then"])
      if elif_condition.nil?
        raise ParseError.new(message: "Expected condition after 'elif'", pos: self.lex_peek_token.pos)
      end
      self.skip_whitespace_and_newlines
      if !self.lex_consume_word("then")
        raise ParseError.new(message: "Expected 'then' after elif condition", pos: self.lex_peek_token.pos)
      end
      elif_then_body = self.parse_list_until(Set["elif", "else", "fi"])
      if elif_then_body.nil?
        raise ParseError.new(message: "Expected commands after 'then'", pos: self.lex_peek_token.pos)
      end
      self.skip_whitespace_and_newlines
      inner_else = nil
      if self.lex_is_at_reserved_word("elif")
        inner_else = self.parse_elif_chain
      elsif self.lex_is_at_reserved_word("else")
        self.lex_consume_word("else")
        inner_else = self.parse_list_until(Set["fi"])
        if inner_else.nil?
          raise ParseError.new(message: "Expected commands after 'else'", pos: self.lex_peek_token.pos)
        end
      end
      else_body = If.new(condition: elif_condition, then_body: elif_then_body, else_body: inner_else, kind: "if")
    elsif self.lex_is_at_reserved_word("else")
      self.lex_consume_word("else")
      else_body = self.parse_list_until(Set["fi"])
      if else_body.nil?
        raise ParseError.new(message: "Expected commands after 'else'", pos: self.lex_peek_token.pos)
      end
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("fi")
      raise ParseError.new(message: "Expected 'fi' to close if statement", pos: self.lex_peek_token.pos)
    end
    return If.new(condition: condition, then_body: then_body, else_body: else_body, redirects: self.collect_redirects, kind: "if")
  end

  def parse_elif_chain()
    self.lex_consume_word("elif")
    condition = self.parse_list_until(Set["then"])
    if condition.nil?
      raise ParseError.new(message: "Expected condition after 'elif'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("then")
      raise ParseError.new(message: "Expected 'then' after elif condition", pos: self.lex_peek_token.pos)
    end
    then_body = self.parse_list_until(Set["elif", "else", "fi"])
    if then_body.nil?
      raise ParseError.new(message: "Expected commands after 'then'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    else_body = nil
    if self.lex_is_at_reserved_word("elif")
      else_body = self.parse_elif_chain
    elsif self.lex_is_at_reserved_word("else")
      self.lex_consume_word("else")
      else_body = self.parse_list_until(Set["fi"])
      if else_body.nil?
        raise ParseError.new(message: "Expected commands after 'else'", pos: self.lex_peek_token.pos)
      end
    end
    return If.new(condition: condition, then_body: then_body, else_body: else_body, kind: "if")
  end

  def parse_while()
    self.skip_whitespace
    if !self.lex_consume_word("while")
      return nil
    end
    condition = self.parse_list_until(Set["do"])
    if condition.nil?
      raise ParseError.new(message: "Expected condition after 'while'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("do")
      raise ParseError.new(message: "Expected 'do' after while condition", pos: self.lex_peek_token.pos)
    end
    body = self.parse_list_until(Set["done"])
    if body.nil?
      raise ParseError.new(message: "Expected commands after 'do'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("done")
      raise ParseError.new(message: "Expected 'done' to close while loop", pos: self.lex_peek_token.pos)
    end
    return While.new(condition: condition, body: body, redirects: self.collect_redirects, kind: "while")
  end

  def parse_until()
    self.skip_whitespace
    if !self.lex_consume_word("until")
      return nil
    end
    condition = self.parse_list_until(Set["do"])
    if condition.nil?
      raise ParseError.new(message: "Expected condition after 'until'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("do")
      raise ParseError.new(message: "Expected 'do' after until condition", pos: self.lex_peek_token.pos)
    end
    body = self.parse_list_until(Set["done"])
    if body.nil?
      raise ParseError.new(message: "Expected commands after 'do'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("done")
      raise ParseError.new(message: "Expected 'done' to close until loop", pos: self.lex_peek_token.pos)
    end
    return Until.new(condition: condition, body: body, redirects: self.collect_redirects, kind: "until")
  end

  def parse_for()
    self.skip_whitespace
    if !self.lex_consume_word("for")
      return nil
    end
    self.skip_whitespace
    if self.peek == "(" && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
      return self.parse_for_arith
    end
    if self.peek == "$"
      var_word = self.parse_word(false, false, false)
      if var_word.nil?
        raise ParseError.new(message: "Expected variable name after 'for'", pos: self.lex_peek_token.pos)
      end
      var_name = var_word.value
    else
      var_name = self.peek_word
      if var_name == ""
        raise ParseError.new(message: "Expected variable name after 'for'", pos: self.lex_peek_token.pos)
      end
      self.consume_word(var_name)
    end
    self.skip_whitespace
    if self.peek == ";"
      self.advance
    end
    self.skip_whitespace_and_newlines
    words = nil
    if self.lex_is_at_reserved_word("in")
      self.lex_consume_word("in")
      self.skip_whitespace
      saw_delimiter = is_semicolon_or_newline(self.peek)
      if self.peek == ";"
        self.advance
      end
      self.skip_whitespace_and_newlines
      words = []
      while true
        self.skip_whitespace
        if self.at_end
          break
        end
        if is_semicolon_or_newline(self.peek)
          saw_delimiter = true
          if self.peek == ";"
            self.advance
          end
          break
        end
        if self.lex_is_at_reserved_word("do")
          if saw_delimiter
            break
          end
          raise ParseError.new(message: "Expected ';' or newline before 'do'", pos: self.lex_peek_token.pos)
        end
        word = self.parse_word(false, false, false)
        if word.nil?
          break
        end
        words.push(word)
      end
    end
    self.skip_whitespace_and_newlines
    if self.peek == "{"
      brace_group = self.parse_brace_group
      if brace_group.nil?
        raise ParseError.new(message: "Expected brace group in for loop", pos: self.lex_peek_token.pos)
      end
      return For.new(var: var_name, words: words, body: brace_group.body, redirects: self.collect_redirects, kind: "for")
    end
    if !self.lex_consume_word("do")
      raise ParseError.new(message: "Expected 'do' in for loop", pos: self.lex_peek_token.pos)
    end
    body = self.parse_list_until(Set["done"])
    if body.nil?
      raise ParseError.new(message: "Expected commands after 'do'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("done")
      raise ParseError.new(message: "Expected 'done' to close for loop", pos: self.lex_peek_token.pos)
    end
    return For.new(var: var_name, words: words, body: body, redirects: self.collect_redirects, kind: "for")
  end

  def parse_for_arith()
    self.advance
    self.advance
    parts = []
    current = []
    paren_depth = 0
    while !self.at_end
      ch = self.peek
      if ch == "("
        paren_depth += 1
        current.push(self.advance)
      elsif ch == ")"
        if paren_depth > 0
          paren_depth -= 1
          current.push(self.advance)
        elsif self.pos + 1 < self.length && self.source[self.pos + 1] == ")"
          parts.push(current.join.gsub(/\A[ \t]+/, ''))
          self.advance
          self.advance
          break
        else
          current.push(self.advance)
        end
      elsif ch == ";" && paren_depth == 0
        parts.push(current.join.gsub(/\A[ \t]+/, ''))
        current = []
        self.advance
      else
        current.push(self.advance)
      end
    end
    if parts.length != 3
      raise ParseError.new(message: "Expected three expressions in for ((;;))", pos: self.pos)
    end
    init = parts[0]
    cond = parts[1]
    incr = parts[2]
    self.skip_whitespace
    if !self.at_end && self.peek == ";"
      self.advance
    end
    self.skip_whitespace_and_newlines
    body = self.parse_loop_body("for loop")
    return ForArith.new(init: init, cond: cond, incr: incr, body: body, redirects: self.collect_redirects, kind: "for-arith")
  end

  def parse_select()
    self.skip_whitespace
    if !self.lex_consume_word("select")
      return nil
    end
    self.skip_whitespace
    var_name = self.peek_word
    if var_name == ""
      raise ParseError.new(message: "Expected variable name after 'select'", pos: self.lex_peek_token.pos)
    end
    self.consume_word(var_name)
    self.skip_whitespace
    if self.peek == ";"
      self.advance
    end
    self.skip_whitespace_and_newlines
    words = nil
    if self.lex_is_at_reserved_word("in")
      self.lex_consume_word("in")
      self.skip_whitespace_and_newlines
      words = []
      while true
        self.skip_whitespace
        if self.at_end
          break
        end
        if is_semicolon_newline_brace(self.peek)
          if self.peek == ";"
            self.advance
          end
          break
        end
        if self.lex_is_at_reserved_word("do")
          break
        end
        word = self.parse_word(false, false, false)
        if word.nil?
          break
        end
        words.push(word)
      end
    end
    self.skip_whitespace_and_newlines
    body = self.parse_loop_body("select")
    return Select.new(var: var_name, words: words, body: body, redirects: self.collect_redirects, kind: "select")
  end

  def consume_case_terminator()
    term = self.lex_peek_case_terminator
    if term != ""
      self.lex_next_token
      return term
    end
    return ";;"
  end

  def parse_case()
    if !self.consume_word("case")
      return nil
    end
    self.set_state(PARSERSTATEFLAGS_PST_CASESTMT)
    self.skip_whitespace
    word = self.parse_word(false, false, false)
    if word.nil?
      raise ParseError.new(message: "Expected word after 'case'", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("in")
      raise ParseError.new(message: "Expected 'in' after case word", pos: self.lex_peek_token.pos)
    end
    self.skip_whitespace_and_newlines
    patterns = []
    self.set_state(PARSERSTATEFLAGS_PST_CASEPAT)
    while true
      self.skip_whitespace_and_newlines
      if self.lex_is_at_reserved_word("esac")
        saved = self.pos
        self.skip_whitespace
        while !self.at_end && !is_metachar(self.peek) && !is_quote(self.peek)
          self.advance
        end
        self.skip_whitespace
        is_pattern = false
        if !self.at_end && self.peek == ")"
          if self.eof_token == ")"
            is_pattern = false
          else
            self.advance
            self.skip_whitespace
            if !self.at_end
              next_ch = self.peek
              if next_ch == ";"
                is_pattern = true
              elsif !is_newline_or_right_paren(next_ch)
                is_pattern = true
              end
            end
          end
        end
        self.pos = saved
        if !is_pattern
          break
        end
      end
      self.skip_whitespace_and_newlines
      if !self.at_end && self.peek == "("
        self.advance
        self.skip_whitespace_and_newlines
      end
      pattern_chars = []
      extglob_depth = 0
      while !self.at_end
        ch = self.peek
        if ch == ")"
          if extglob_depth > 0
            pattern_chars.push(self.advance)
            extglob_depth -= 1
          else
            self.advance
            break
          end
        elsif ch == "\\"
          if self.pos + 1 < self.length && self.source[self.pos + 1] == "\n"
            self.advance
            self.advance
          else
            pattern_chars.push(self.advance)
            if !self.at_end
              pattern_chars.push(self.advance)
            end
          end
        elsif is_expansion_start(self.source, self.pos, "$(")
          pattern_chars.push(self.advance)
          pattern_chars.push(self.advance)
          if !self.at_end && self.peek == "("
            pattern_chars.push(self.advance)
            paren_depth = 2
            while !self.at_end && paren_depth > 0
              c = self.peek
              if c == "("
                paren_depth += 1
              elsif c == ")"
                paren_depth -= 1
              end
              pattern_chars.push(self.advance)
            end
          else
            extglob_depth += 1
          end
        elsif ch == "(" && extglob_depth > 0
          pattern_chars.push(self.advance)
          extglob_depth += 1
        elsif self.extglob && is_extglob_prefix(ch) && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
          pattern_chars.push(self.advance)
          pattern_chars.push(self.advance)
          extglob_depth += 1
        elsif ch == "["
          is_char_class = false
          scan_pos = self.pos + 1
          scan_depth = 0
          has_first_bracket_literal = false
          if scan_pos < self.length && is_caret_or_bang(self.source[scan_pos])
            scan_pos += 1
          end
          if scan_pos < self.length && self.source[scan_pos] == "]"
            if !self.source.index("]", scan_pos + 1).nil?
              scan_pos += 1
              has_first_bracket_literal = true
            end
          end
          while scan_pos < self.length
            sc = self.source[scan_pos]
            if sc == "]" && scan_depth == 0
              is_char_class = true
              break
            elsif sc == "["
              scan_depth += 1
            elsif sc == ")" && scan_depth == 0
              break
            elsif sc == "|" && scan_depth == 0
              break
            end
            scan_pos += 1
          end
          if is_char_class
            pattern_chars.push(self.advance)
            if !self.at_end && is_caret_or_bang(self.peek)
              pattern_chars.push(self.advance)
            end
            if has_first_bracket_literal && !self.at_end && self.peek == "]"
              pattern_chars.push(self.advance)
            end
            while !self.at_end && self.peek != "]"
              pattern_chars.push(self.advance)
            end
            if !self.at_end
              pattern_chars.push(self.advance)
            end
          else
            pattern_chars.push(self.advance)
          end
        elsif ch == "'"
          pattern_chars.push(self.advance)
          while !self.at_end && self.peek != "'"
            pattern_chars.push(self.advance)
          end
          if !self.at_end
            pattern_chars.push(self.advance)
          end
        elsif ch == "\""
          pattern_chars.push(self.advance)
          while !self.at_end && self.peek != "\""
            if self.peek == "\\" && self.pos + 1 < self.length
              pattern_chars.push(self.advance)
            end
            pattern_chars.push(self.advance)
          end
          if !self.at_end
            pattern_chars.push(self.advance)
          end
        elsif is_whitespace(ch)
          if extglob_depth > 0
            pattern_chars.push(self.advance)
          else
            self.advance
          end
        else
          pattern_chars.push(self.advance)
        end
      end
      pattern = pattern_chars.join
      if !(pattern && !pattern.empty?)
        raise ParseError.new(message: "Expected pattern in case statement", pos: self.lex_peek_token.pos)
      end
      self.skip_whitespace
      body = nil
      is_empty_body = self.lex_peek_case_terminator != ""
      if !is_empty_body
        self.skip_whitespace_and_newlines
        if !self.at_end && !self.lex_is_at_reserved_word("esac")
          is_at_terminator = self.lex_peek_case_terminator != ""
          if !is_at_terminator
            body = self.parse_list_until(Set["esac"])
            self.skip_whitespace
          end
        end
      end
      terminator = self.consume_case_terminator
      self.skip_whitespace_and_newlines
      patterns.push(CasePattern.new(pattern: pattern, body: body, terminator: terminator, kind: "pattern"))
    end
    self.clear_state(PARSERSTATEFLAGS_PST_CASEPAT)
    self.skip_whitespace_and_newlines
    if !self.lex_consume_word("esac")
      self.clear_state(PARSERSTATEFLAGS_PST_CASESTMT)
      raise ParseError.new(message: "Expected 'esac' to close case statement", pos: self.lex_peek_token.pos)
    end
    self.clear_state(PARSERSTATEFLAGS_PST_CASESTMT)
    return Case.new(word: word, patterns: patterns, redirects: self.collect_redirects, kind: "case")
  end

  def parse_coproc()
    self.skip_whitespace
    if !self.lex_consume_word("coproc")
      return nil
    end
    self.skip_whitespace
    name = ""
    ch = ""
    if !self.at_end
      ch = self.peek
    end
    if ch == "{"
      body = self.parse_brace_group
      if !body.nil?
        return Coproc.new(command: body, name: name, kind: "coproc")
      end
    end
    if ch == "("
      if self.pos + 1 < self.length && self.source[self.pos + 1] == "("
        body = self.parse_arithmetic_command
        if !body.nil?
          return Coproc.new(command: body, name: name, kind: "coproc")
        end
      end
      body = self.parse_subshell
      if !body.nil?
        return Coproc.new(command: body, name: name, kind: "coproc")
      end
    end
    next_word = self.lex_peek_reserved_word
    if next_word != "" && (COMPOUND_KEYWORDS.include?(next_word))
      body = self.parse_compound_command
      if !body.nil?
        return Coproc.new(command: body, name: name, kind: "coproc")
      end
    end
    word_start = self.pos
    potential_name = self.peek_word
    if (potential_name && !potential_name.empty?)
      while !self.at_end && !is_metachar(self.peek) && !is_quote(self.peek)
        self.advance
      end
      self.skip_whitespace
      ch = ""
      if !self.at_end
        ch = self.peek
      end
      next_word = self.lex_peek_reserved_word
      if is_valid_identifier(potential_name)
        if ch == "{"
          name = potential_name
          body = self.parse_brace_group
          if !body.nil?
            return Coproc.new(command: body, name: name, kind: "coproc")
          end
        elsif ch == "("
          name = potential_name
          if self.pos + 1 < self.length && self.source[self.pos + 1] == "("
            body = self.parse_arithmetic_command
          else
            body = self.parse_subshell
          end
          if !body.nil?
            return Coproc.new(command: body, name: name, kind: "coproc")
          end
        elsif next_word != "" && (COMPOUND_KEYWORDS.include?(next_word))
          name = potential_name
          body = self.parse_compound_command
          if !body.nil?
            return Coproc.new(command: body, name: name, kind: "coproc")
          end
        end
      end
      self.pos = word_start
    end
    body = self.parse_command
    if !body.nil?
      return Coproc.new(command: body, name: name, kind: "coproc")
    end
    raise ParseError.new(message: "Expected command after coproc", pos: self.pos)
  end

  def parse_function()
    self.skip_whitespace
    if self.at_end
      return nil
    end
    saved_pos = self.pos
    if self.lex_is_at_reserved_word("function")
      self.lex_consume_word("function")
      self.skip_whitespace
      name = self.peek_word
      if name == ""
        self.pos = saved_pos
        return nil
      end
      self.consume_word(name)
      self.skip_whitespace
      if !self.at_end && self.peek == "("
        if self.pos + 1 < self.length && self.source[self.pos + 1] == ")"
          self.advance
          self.advance
        end
      end
      self.skip_whitespace_and_newlines
      body = self.parse_compound_command
      if body.nil?
        raise ParseError.new(message: "Expected function body", pos: self.pos)
      end
      return Function.new(name: name, body: body, kind: "function")
    end
    name = self.peek_word
    if name == "" || (RESERVED_WORDS.include?(name))
      return nil
    end
    if looks_like_assignment(name)
      return nil
    end
    self.skip_whitespace
    name_start = self.pos
    while !self.at_end && !is_metachar(self.peek) && !is_quote(self.peek) && !is_paren(self.peek)
      self.advance
    end
    name = substring(self.source, name_start, self.pos)
    if !(name && !name.empty?)
      self.pos = saved_pos
      return nil
    end
    brace_depth = 0
    i = 0
    while i < name.length
      if is_expansion_start(name, i, "${")
        brace_depth += 1
        i += 2
        next
      end
      if name[i] == "}"
        brace_depth -= 1
      end
      i += 1
    end
    if brace_depth > 0
      self.pos = saved_pos
      return nil
    end
    pos_after_name = self.pos
    self.skip_whitespace
    has_whitespace = self.pos > pos_after_name
    if !has_whitespace && (name && !name.empty?) && ("*?@+!$".include?(name[-1]))
      self.pos = saved_pos
      return nil
    end
    if self.at_end || self.peek != "("
      self.pos = saved_pos
      return nil
    end
    self.advance
    self.skip_whitespace
    if self.at_end || self.peek != ")"
      self.pos = saved_pos
      return nil
    end
    self.advance
    self.skip_whitespace_and_newlines
    body = self.parse_compound_command
    if body.nil?
      raise ParseError.new(message: "Expected function body", pos: self.pos)
    end
    return Function.new(name: name, body: body, kind: "function")
  end

  def parse_compound_command()
    result = self.parse_brace_group
    if !result.nil?
      return result
    end
    if !self.at_end && self.peek == "(" && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
      result = self.parse_arithmetic_command
      if !result.nil?
        return result
      end
    end
    result = self.parse_subshell
    if !result.nil?
      return result
    end
    result = self.parse_conditional_expr
    if !result.nil?
      return result
    end
    result = self.parse_if
    if !result.nil?
      return result
    end
    result = self.parse_while
    if !result.nil?
      return result
    end
    result = self.parse_until
    if !result.nil?
      return result
    end
    result = self.parse_for
    if !result.nil?
      return result
    end
    result = self.parse_case
    if !result.nil?
      return result
    end
    result = self.parse_select
    if !result.nil?
      return result
    end
    return nil
  end

  def at_list_until_terminator(stop_words)
    if self.at_end
      return true
    end
    if self.peek == ")"
      return true
    end
    if self.peek == "}"
      next_pos = self.pos + 1
      if next_pos >= self.length || is_word_end_context(self.source[next_pos])
        return true
      end
    end
    reserved = self.lex_peek_reserved_word
    if reserved != "" && (stop_words.include?(reserved))
      return true
    end
    if self.lex_peek_case_terminator != ""
      return true
    end
    return false
  end

  def parse_list_until(stop_words)
    self.skip_whitespace_and_newlines
    reserved = self.lex_peek_reserved_word
    if reserved != "" && (stop_words.include?(reserved))
      return nil
    end
    pipeline = self.parse_pipeline
    if pipeline.nil?
      return nil
    end
    parts = [pipeline]
    while true
      self.skip_whitespace
      op = self.parse_list_operator
      if op == ""
        if !self.at_end && self.peek == "\n"
          self.advance
          self.gather_heredoc_bodies
          if self.cmdsub_heredoc_end != -1 && self.cmdsub_heredoc_end > self.pos
            self.pos = self.cmdsub_heredoc_end
            self.cmdsub_heredoc_end = -1
          end
          self.skip_whitespace_and_newlines
          if self.at_list_until_terminator(stop_words)
            break
          end
          next_op = self.peek_list_operator
          if next_op == "&" || next_op == ";"
            break
          end
          op = "\n"
        else
          break
        end
      end
      if op == ""
        break
      end
      if op == ";"
        self.skip_whitespace_and_newlines
        if self.at_list_until_terminator(stop_words)
          break
        end
        parts.push(Operator.new(op: op, kind: "operator"))
      elsif op == "&"
        parts.push(Operator.new(op: op, kind: "operator"))
        self.skip_whitespace_and_newlines
        if self.at_list_until_terminator(stop_words)
          break
        end
      elsif op == "&&" || op == "||"
        parts.push(Operator.new(op: op, kind: "operator"))
        self.skip_whitespace_and_newlines
      else
        parts.push(Operator.new(op: op, kind: "operator"))
      end
      if self.at_list_until_terminator(stop_words)
        break
      end
      pipeline = self.parse_pipeline
      if pipeline.nil?
        raise ParseError.new(message: "Expected command after " + op, pos: self.pos)
      end
      parts.push(pipeline)
    end
    if parts.length == 1
      return parts[0]
    end
    return List.new(parts: parts, kind: "list")
  end

  def parse_compound_command()
    self.skip_whitespace
    if self.at_end
      return nil
    end
    ch = self.peek
    if ch == "(" && self.pos + 1 < self.length && self.source[self.pos + 1] == "("
      result = self.parse_arithmetic_command
      if !result.nil?
        return result
      end
    end
    if ch == "("
      return self.parse_subshell
    end
    if ch == "{"
      result = self.parse_brace_group
      if !result.nil?
        return result
      end
    end
    if ch == "[" && self.pos + 1 < self.length && self.source[self.pos + 1] == "["
      result = self.parse_conditional_expr
      if !result.nil?
        return result
      end
    end
    reserved = self.lex_peek_reserved_word
    if reserved == "" && self.in_process_sub
      word = self.peek_word
      if word != "" && word.length > 1 && word[0] == "}"
        keyword_word = word[1..]
        if (RESERVED_WORDS.include?(keyword_word)) || keyword_word == "{" || keyword_word == "}" || keyword_word == "[[" || keyword_word == "]]" || keyword_word == "!" || keyword_word == "time"
          reserved = keyword_word
        end
      end
    end
    if reserved == "fi" || reserved == "then" || reserved == "elif" || reserved == "else" || reserved == "done" || reserved == "esac" || reserved == "do" || reserved == "in"
      raise ParseError.new(message: "Unexpected reserved word '#{reserved}'", pos: self.lex_peek_token.pos)
    end
    if reserved == "if"
      return self.parse_if
    end
    if reserved == "while"
      return self.parse_while
    end
    if reserved == "until"
      return self.parse_until
    end
    if reserved == "for"
      return self.parse_for
    end
    if reserved == "select"
      return self.parse_select
    end
    if reserved == "case"
      return self.parse_case
    end
    if reserved == "function"
      return self.parse_function
    end
    if reserved == "coproc"
      return self.parse_coproc
    end
    func = self.parse_function
    if !func.nil?
      return func
    end
    return self.parse_command
  end

  def parse_pipeline()
    self.skip_whitespace
    prefix_order = ""
    time_posix = false
    if self.lex_is_at_reserved_word("time")
      self.lex_consume_word("time")
      prefix_order = "time"
      self.skip_whitespace
      if !self.at_end && self.peek == "-"
        saved = self.pos
        self.advance
        if !self.at_end && self.peek == "p"
          self.advance
          if self.at_end || is_metachar(self.peek)
            time_posix = true
          else
            self.pos = saved
          end
        else
          self.pos = saved
        end
      end
      self.skip_whitespace
      if !self.at_end && starts_with_at(self.source, self.pos, "--")
        if self.pos + 2 >= self.length || is_whitespace(self.source[self.pos + 2])
          self.advance
          self.advance
          time_posix = true
          self.skip_whitespace
        end
      end
      while self.lex_is_at_reserved_word("time")
        self.lex_consume_word("time")
        self.skip_whitespace
        if !self.at_end && self.peek == "-"
          saved = self.pos
          self.advance
          if !self.at_end && self.peek == "p"
            self.advance
            if self.at_end || is_metachar(self.peek)
              time_posix = true
            else
              self.pos = saved
            end
          else
            self.pos = saved
          end
        end
      end
      self.skip_whitespace
      if !self.at_end && self.peek == "!"
        if (self.pos + 1 >= self.length || is_negation_boundary(self.source[self.pos + 1])) && !self.is_bang_followed_by_procsub
          self.advance
          prefix_order = "time_negation"
          self.skip_whitespace
        end
      end
    elsif !self.at_end && self.peek == "!"
      if (self.pos + 1 >= self.length || is_negation_boundary(self.source[self.pos + 1])) && !self.is_bang_followed_by_procsub
        self.advance
        self.skip_whitespace
        inner = self.parse_pipeline
        if !inner.nil? && inner.kind == "negation"
          if !inner.pipeline.nil?
            return inner.pipeline
          else
            return Command.new(words: [], kind: "command")
          end
        end
        return Negation.new(pipeline: inner, kind: "negation")
      end
    end
    result = self.parse_simple_pipeline
    if prefix_order == "time"
      result = Time_.new(pipeline: result, posix: time_posix, kind: "time")
    elsif prefix_order == "negation"
      result = Negation.new(pipeline: result, kind: "negation")
    elsif prefix_order == "time_negation"
      result = Time_.new(pipeline: result, posix: time_posix, kind: "time")
      result = Negation.new(pipeline: result, kind: "negation")
    elsif prefix_order == "negation_time"
      result = Time_.new(pipeline: result, posix: time_posix, kind: "time")
      result = Negation.new(pipeline: result, kind: "negation")
    elsif result.nil?
      return nil
    end
    return result
  end

  def parse_simple_pipeline()
    cmd = self.parse_compound_command
    if cmd.nil?
      return nil
    end
    commands = [cmd]
    while true
      self.skip_whitespace
      token_type, value = self.lex_peek_operator
      if token_type == 0
        break
      end
      if token_type != TOKENTYPE_PIPE && token_type != TOKENTYPE_PIPE_AMP
        break
      end
      self.lex_next_token
      is_pipe_both = token_type == TOKENTYPE_PIPE_AMP
      self.skip_whitespace_and_newlines
      if is_pipe_both
        commands.push(PipeBoth.new(kind: "pipe-both"))
      end
      cmd = self.parse_compound_command
      if cmd.nil?
        raise ParseError.new(message: "Expected command after |", pos: self.pos)
      end
      commands.push(cmd)
    end
    if commands.length == 1
      return commands[0]
    end
    return Pipeline.new(commands: commands, kind: "pipeline")
  end

  def parse_list_operator()
    self.skip_whitespace
    token_type,  = self.lex_peek_operator
    if token_type == 0
      return ""
    end
    if token_type == TOKENTYPE_AND_AND
      self.lex_next_token
      return "&&"
    end
    if token_type == TOKENTYPE_OR_OR
      self.lex_next_token
      return "||"
    end
    if token_type == TOKENTYPE_SEMI
      self.lex_next_token
      return ";"
    end
    if token_type == TOKENTYPE_AMP
      self.lex_next_token
      return "&"
    end
    return ""
  end

  def peek_list_operator()
    saved_pos = self.pos
    op = self.parse_list_operator
    self.pos = saved_pos
    return op
  end

  def parse_list(newline_as_separator = true)
    if newline_as_separator
      self.skip_whitespace_and_newlines
    else
      self.skip_whitespace
    end
    pipeline = self.parse_pipeline
    if pipeline.nil?
      return nil
    end
    parts = [pipeline]
    if self.in_state(PARSERSTATEFLAGS_PST_EOFTOKEN) && self.at_eof_token
      return parts.length == 1 ? parts[0] : List.new(parts: parts, kind: "list")
    end
    while true
      self.skip_whitespace
      op = self.parse_list_operator
      if op == ""
        if !self.at_end && self.peek == "\n"
          if !newline_as_separator
            break
          end
          self.advance
          self.gather_heredoc_bodies
          if self.cmdsub_heredoc_end != -1 && self.cmdsub_heredoc_end > self.pos
            self.pos = self.cmdsub_heredoc_end
            self.cmdsub_heredoc_end = -1
          end
          self.skip_whitespace_and_newlines
          if self.at_end || self.at_list_terminating_bracket
            break
          end
          next_op = self.peek_list_operator
          if next_op == "&" || next_op == ";"
            break
          end
          op = "\n"
        else
          break
        end
      end
      if op == ""
        break
      end
      parts.push(Operator.new(op: op, kind: "operator"))
      if op == "&&" || op == "||"
        self.skip_whitespace_and_newlines
      elsif op == "&"
        self.skip_whitespace
        if self.at_end || self.at_list_terminating_bracket
          break
        end
        if self.peek == "\n"
          if newline_as_separator
            self.skip_whitespace_and_newlines
            if self.at_end || self.at_list_terminating_bracket
              break
            end
          else
            break
          end
        end
      elsif op == ";"
        self.skip_whitespace
        if self.at_end || self.at_list_terminating_bracket
          break
        end
        if self.peek == "\n"
          if newline_as_separator
            self.skip_whitespace_and_newlines
            if self.at_end || self.at_list_terminating_bracket
              break
            end
          else
            break
          end
        end
      end
      pipeline = self.parse_pipeline
      if pipeline.nil?
        raise ParseError.new(message: "Expected command after " + op, pos: self.pos)
      end
      parts.push(pipeline)
      if self.in_state(PARSERSTATEFLAGS_PST_EOFTOKEN) && self.at_eof_token
        break
      end
    end
    if parts.length == 1
      return parts[0]
    end
    return List.new(parts: parts, kind: "list")
  end

  def parse_comment()
    if self.at_end || self.peek != "#"
      return nil
    end
    start = self.pos
    while !self.at_end && self.peek != "\n"
      self.advance
    end
    text = substring(self.source, start, self.pos)
    return Comment.new(text: text, kind: "comment")
  end

  def parse()
    source = self.source.gsub(/\A[ \t\n\r]+|[ \t\n\r]+\z/, '')
    if !(source && !source.empty?)
      return [Empty.new(kind: "empty")]
    end
    results = []
    while true
      self.skip_whitespace
      while !self.at_end && self.peek == "\n"
        self.advance
      end
      if self.at_end
        break
      end
      comment = self.parse_comment
      if !!comment.nil?
        break
      end
    end
    while !self.at_end
      result = self.parse_list(false)
      if !result.nil?
        results.push(result)
      end
      self.skip_whitespace
      found_newline = false
      while !self.at_end && self.peek == "\n"
        found_newline = true
        self.advance
        self.gather_heredoc_bodies
        if self.cmdsub_heredoc_end != -1 && self.cmdsub_heredoc_end > self.pos
          self.pos = self.cmdsub_heredoc_end
          self.cmdsub_heredoc_end = -1
        end
        self.skip_whitespace
      end
      if !found_newline && !self.at_end
        raise ParseError.new(message: "Syntax error", pos: self.pos)
      end
    end
    if !(results && !results.empty?)
      return [Empty.new(kind: "empty")]
    end
    if self.saw_newline_in_single_quote && (self.source && !self.source.empty?) && self.source[-1] == "\\" && !(self.source.length >= 3 && self.source[-3...-1] == "\\\n")
      if !self.last_word_on_own_line(results)
        self.strip_trailing_backslash_from_last_word(results)
      end
    end
    return results
  end

  def last_word_on_own_line(nodes)
    return nodes.length >= 2
  end

  def strip_trailing_backslash_from_last_word(nodes)
    if !(nodes && !nodes.empty?)
      return
    end
    last_node = nodes[-1]
    last_word = self.find_last_word(last_node)
    if !last_word.nil? && last_word.value.end_with?("\\")
      last_word.value = substring(last_word.value, 0, last_word.value.length - 1)
      if !(last_word.value && !last_word.value.empty?) && last_node.is_a?(Command) && (last_node.words && !last_node.words.empty?)
        last_node.words.pop
      end
    end
  end

  def find_last_word(node)
    case node
    when Word
      node = node
      return node
    end
    case node
    when Command
      node = node
      if (node.words && !node.words.empty?)
        last_word = node.words[-1]
        if last_word.value.end_with?("\\")
          return last_word
        end
      end
      if (node.redirects && !node.redirects.empty?)
        last_redirect = node.redirects[-1]
        case last_redirect
        when Redirect
          last_redirect = last_redirect
          return last_redirect.target
        end
      end
      if (node.words && !node.words.empty?)
        return node.words[-1]
      end
    end
    case node
    when Pipeline
      node = node
      if (node.commands && !node.commands.empty?)
        return self.find_last_word(node.commands[-1])
      end
    end
    case node
    when List
      node = node
      if (node.parts && !node.parts.empty?)
        return self.find_last_word(node.parts[-1])
      end
    end
    return nil
  end
end

def is_hex_digit(c)
  return c >= "0" && c <= "9" || c >= "a" && c <= "f" || c >= "A" && c <= "F"
end

def is_octal_digit(c)
  return c >= "0" && c <= "7"
end

def get_ansi_escape(c)
  return ANSI_C_ESCAPES.fetch(c, -1)
end

def is_whitespace(c)
  return c == " " || c == "\t" || c == "\n"
end

def string_to_bytes(s)
  return s.bytes.dup
end

def is_whitespace_no_newline(c)
  return c == " " || c == "\t"
end

def substring(s, start, end_)
  return s[start...end_]
end

def starts_with_at(s, pos, prefix)
  return s[pos..].start_with?(prefix)
end

def count_consecutive_dollars_before(s, pos)
  count = 0
  k = pos - 1
  while k >= 0 && s[k] == "$"
    bs_count = 0
    j = k - 1
    while j >= 0 && s[j] == "\\"
      bs_count += 1
      j -= 1
    end
    if bs_count % 2 == 1
      break
    end
    count += 1
    k -= 1
  end
  return count
end

def is_expansion_start(s, pos, delimiter)
  if !starts_with_at(s, pos, delimiter)
    return false
  end
  return count_consecutive_dollars_before(s, pos) % 2 == 0
end

def sublist(lst, start, end_)
  return lst[start...end_]
end

def repeat_str(s, n)
  result = []
  i = 0
  while i < n
    result.push(s)
    i += 1
  end
  return result.join
end

def strip_line_continuations_comment_aware(text)
  result = []
  i = 0
  in_comment = false
  quote = new_quote_state()
  while i < text.length
    c = text[i]
    if c == "\\" && i + 1 < text.length && text[i + 1] == "\n"
      num_preceding_backslashes = 0
      j = i - 1
      while j >= 0 && text[j] == "\\"
        num_preceding_backslashes += 1
        j -= 1
      end
      if num_preceding_backslashes % 2 == 0
        if in_comment
          result.push("\n")
        end
        i += 2
        in_comment = false
        next
      end
    end
    if c == "\n"
      in_comment = false
      result.push(c)
      i += 1
      next
    end
    if c == "'" && !quote.double && !in_comment
      quote.single = !quote.single
    elsif c == "\"" && !quote.single && !in_comment
      quote.double = !quote.double
    elsif c == "#" && !quote.single && !in_comment
      in_comment = true
    end
    result.push(c)
    i += 1
  end
  return result.join
end

def append_redirects(base, redirects)
  if (redirects && !redirects.empty?)
    parts = []
    redirects.each do |r|
      parts.push(r.to_sexp)
    end
    return base + " " + parts.join(" ")
  end
  return base
end

def format_arith_val(s)
  w = Word.new(value: s, parts: [], kind: "word")
  val = w.expand_all_ansi_c_quotes(s)
  val = w.strip_locale_string_dollars(val)
  val = w.format_command_substitutions(val, false)
  val = val.gsub("\\") { "\\\\" }.gsub("\"") { "\\\"" }
  val = val.gsub("
") { "\\n" }.gsub("	") { "\\t" }
  return val
end

def consume_single_quote(s, start)
  chars = ["'"]
  i = start + 1
  while i < s.length && s[i] != "'"
    chars.push(s[i])
    i += 1
  end
  if i < s.length
    chars.push(s[i])
    i += 1
  end
  return [i, chars]
end

def consume_double_quote(s, start)
  chars = ["\""]
  i = start + 1
  while i < s.length && s[i] != "\""
    if s[i] == "\\" && i + 1 < s.length
      chars.push(s[i])
      i += 1
    end
    chars.push(s[i])
    i += 1
  end
  if i < s.length
    chars.push(s[i])
    i += 1
  end
  return [i, chars]
end

def has_bracket_close(s, start, depth)
  i = start
  while i < s.length
    if s[i] == "]"
      return true
    end
    if (s[i] == "|" || s[i] == ")") && depth == 0
      return false
    end
    i += 1
  end
  return false
end

def consume_bracket_class(s, start, depth)
  scan_pos = start + 1
  if scan_pos < s.length && (s[scan_pos] == "!" || s[scan_pos] == "^")
    scan_pos += 1
  end
  if scan_pos < s.length && s[scan_pos] == "]"
    if has_bracket_close(s, scan_pos + 1, depth)
      scan_pos += 1
    end
  end
  is_bracket = false
  while scan_pos < s.length
    if s[scan_pos] == "]"
      is_bracket = true
      break
    end
    if s[scan_pos] == ")" && depth == 0
      break
    end
    if s[scan_pos] == "|" && depth == 0
      break
    end
    scan_pos += 1
  end
  if !is_bracket
    return [start + 1, ["["], false]
  end
  chars = ["["]
  i = start + 1
  if i < s.length && (s[i] == "!" || s[i] == "^")
    chars.push(s[i])
    i += 1
  end
  if i < s.length && s[i] == "]"
    if has_bracket_close(s, i + 1, depth)
      chars.push(s[i])
      i += 1
    end
  end
  while i < s.length && s[i] != "]"
    chars.push(s[i])
    i += 1
  end
  if i < s.length
    chars.push(s[i])
    i += 1
  end
  return [i, chars, true]
end

def format_cond_body(node)
  kind = node.kind
  if kind == "unary-test"
    operand_val = node.operand.get_cond_formatted_value
    return node.op + " " + operand_val
  end
  if kind == "binary-test"
    left_val = node.left.get_cond_formatted_value
    right_val = node.right.get_cond_formatted_value
    return left_val + " " + node.op + " " + right_val
  end
  if kind == "cond-and"
    return format_cond_body(node.left) + " && " + format_cond_body(node.right)
  end
  if kind == "cond-or"
    return format_cond_body(node.left) + " || " + format_cond_body(node.right)
  end
  if kind == "cond-not"
    return "! " + format_cond_body(node.operand)
  end
  if kind == "cond-paren"
    return "( " + format_cond_body(node.inner) + " )"
  end
  return ""
end

def starts_with_subshell(node)
  case node
  when Subshell
    node = node
    return true
  end
  case node
  when List
    node = node
    (node.parts || []).each do |p_|
      if p_.kind != "operator"
        return starts_with_subshell(p_)
      end
    end
    return false
  end
  case node
  when Pipeline
    node = node
    if (node.commands && !node.commands.empty?)
      return starts_with_subshell(node.commands[0])
    end
    return false
  end
  return false
end

def format_cmdsub_node(node, indent = 0, in_procsub = false, compact_redirects = false, procsub_first = false)
  if node.nil?
    return ""
  end
  sp = repeat_str(" ", indent)
  inner_sp = repeat_str(" ", indent + 4)
  case node
  when ArithEmpty
    node = node
    return ""
  end
  case node
  when Command
    node = node
    parts = []
    (node.words || []).each do |w|
      val = w.expand_all_ansi_c_quotes(w.value)
      val = w.strip_locale_string_dollars(val)
      val = w.normalize_array_whitespace(val)
      val = w.format_command_substitutions(val, false)
      parts.push(val)
    end
    heredocs = []
    (node.redirects || []).each do |r|
      case r
      when HereDoc
        r = r
        heredocs.push(r)
      end
    end
    (node.redirects || []).each do |r|
      parts.push(format_redirect(r, compact_redirects, true))
    end
    if compact_redirects && (node.words && !node.words.empty?) && (node.redirects && !node.redirects.empty?)
      word_parts = parts[0...node.words.length]
      redirect_parts = parts[node.words.length..]
      result = word_parts.join(" ") + redirect_parts.join
    else
      result = parts.join(" ")
    end
    heredocs.each do |h|
      result = result + format_heredoc_body(h)
    end
    return result
  end
  case node
  when Pipeline
    node = node
    cmds = []
    i = 0
    while i < node.commands.length
      cmd = node.commands[i]
      case cmd
      when PipeBoth
        cmd = cmd
        i += 1
        next
      end
      needs_redirect = i + 1 < node.commands.length && node.commands[i + 1].kind == "pipe-both"
      cmds.push([cmd, needs_redirect])
      i += 1
    end
    result_parts = []
    idx = 0
    while idx < cmds.length
      entry = cmds[idx]
      cmd = entry[0]
      needs_redirect = entry[1]
      formatted = format_cmdsub_node(cmd, indent, in_procsub, false, procsub_first && idx == 0)
      is_last = idx == cmds.length - 1
      has_heredoc = false
      if cmd.kind == "command" && (cmd.redirects && !cmd.redirects.empty?)
        (cmd.redirects || []).each do |r|
          case r
          when HereDoc
            r = r
            has_heredoc = true
            break
          end
        end
      end
      if needs_redirect
        if has_heredoc
          first_nl = formatted.index("\n")
          if first_nl != -1
            formatted = formatted[0...first_nl] + " 2>&1" + formatted[first_nl..]
          else
            formatted = formatted + " 2>&1"
          end
        else
          formatted = formatted + " 2>&1"
        end
      end
      if !is_last && has_heredoc
        first_nl = formatted.index("\n")
        if first_nl != -1
          formatted = formatted[0...first_nl] + " |" + formatted[first_nl..]
        end
        result_parts.push(formatted)
      else
        result_parts.push(formatted)
      end
      idx += 1
    end
    compact_pipe = in_procsub && (cmds && !cmds.empty?) && cmds[0][0].kind == "subshell"
    result = ""
    idx = 0
    while idx < result_parts.length
      part = result_parts[idx]
      if idx > 0
        if result.end_with?("\n")
          result = result + "  " + part
        elsif compact_pipe
          result = result + "|" + part
        else
          result = result + " | " + part
        end
      else
        result = part
      end
      idx += 1
    end
    return result
  end
  case node
  when List
    node = node
    has_heredoc = false
    (node.parts || []).each do |p_|
      if p_.kind == "command" && (p_.redirects && !p_.redirects.empty?)
        (p_.redirects || []).each do |r|
          case r
          when HereDoc
            r = r
            has_heredoc = true
            break
          end
        end
      else
        case p_
        when Pipeline
          p_ = p_
          (p_.commands || []).each do |cmd|
            if cmd.kind == "command" && (cmd.redirects && !cmd.redirects.empty?)
              (cmd.redirects || []).each do |r|
                case r
                when HereDoc
                  r = r
                  has_heredoc = true
                  break
                end
              end
            end
            if has_heredoc
              break
            end
          end
        end
      end
    end
    result = []
    skipped_semi = false
    cmd_count = 0
    (node.parts || []).each do |p_|
      case p_
      when Operator
        p_ = p_
        if p_.op == ";"
          if (result && !result.empty?) && result[-1].end_with?("\n")
            skipped_semi = true
            next
          end
          if result.length >= 3 && result[-2] == "\n" && result[-3].end_with?("\n")
            skipped_semi = true
            next
          end
          result.push(";")
          skipped_semi = false
        elsif p_.op == "\n"
          if (result && !result.empty?) && result[-1] == ";"
            skipped_semi = false
            next
          end
          if (result && !result.empty?) && result[-1].end_with?("\n")
            result.push(skipped_semi ? " " : "\n")
            skipped_semi = false
            next
          end
          result.push("\n")
          skipped_semi = false
        elsif p_.op == "&"
          if (result && !result.empty?) && (result[-1].include?("<<")) && (result[-1].include?("\n"))
            last = result[-1]
            if (last.include?(" |")) || last.start_with?("|")
              result[-1] = last + " &"
            else
              first_nl = last.index("\n")
              result[-1] = last[0...first_nl] + " &" + last[first_nl..]
            end
          else
            result.push(" &")
          end
        elsif (result && !result.empty?) && (result[-1].include?("<<")) && (result[-1].include?("\n"))
          last = result[-1]
          first_nl = last.index("\n")
          result[-1] = last[0...first_nl] + " " + p_.op + " " + last[first_nl..]
        else
          result.push(" " + p_.op)
        end
      else
        if (result && !result.empty?) && !result[-1].end_with?(" ", "\n")
          result.push(" ")
        end
        formatted_cmd = format_cmdsub_node(p_, indent, in_procsub, compact_redirects, procsub_first && cmd_count == 0)
        if result.length > 0
          last = result[-1]
          if (last.include?(" || \n")) || (last.include?(" && \n"))
            formatted_cmd = " " + formatted_cmd
          end
        end
        if skipped_semi
          formatted_cmd = " " + formatted_cmd
          skipped_semi = false
        end
        result.push(formatted_cmd)
        cmd_count += 1
      end
    end
    s = result.join
    if (s.include?(" &\n")) && s.end_with?("\n")
      return s + " "
    end
    while s.end_with?(";")
      s = substring(s, 0, s.length - 1)
    end
    if !has_heredoc
      while s.end_with?("\n")
        s = substring(s, 0, s.length - 1)
      end
    end
    return s
  end
  case node
  when If
    node = node
    cond = format_cmdsub_node(node.condition, indent, false, false, false)
    then_body = format_cmdsub_node(node.then_body, indent + 4, false, false, false)
    result = "if " + cond + "; then\n" + inner_sp + then_body + ";"
    if !node.else_body.nil?
      else_body = format_cmdsub_node(node.else_body, indent + 4, false, false, false)
      result = result + "\n" + sp + "else\n" + inner_sp + else_body + ";"
    end
    result = result + "\n" + sp + "fi"
    return result
  end
  case node
  when While
    node = node
    cond = format_cmdsub_node(node.condition, indent, false, false, false)
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    result = "while " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done"
    if (node.redirects && !node.redirects.empty?)
      (node.redirects || []).each do |r|
        result = result + " " + format_redirect(r, false, false)
      end
    end
    return result
  end
  case node
  when Until
    node = node
    cond = format_cmdsub_node(node.condition, indent, false, false, false)
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    result = "until " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done"
    if (node.redirects && !node.redirects.empty?)
      (node.redirects || []).each do |r|
        result = result + " " + format_redirect(r, false, false)
      end
    end
    return result
  end
  case node
  when For
    node = node
    var = node.var
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    if !node.words.nil?
      word_vals = []
      (node.words || []).each do |w|
        word_vals.push(w.value)
      end
      words = word_vals.join(" ")
      if (words && !words.empty?)
        result = "for " + var + " in " + words + ";\n" + sp + "do\n" + inner_sp + body + ";\n" + sp + "done"
      else
        result = "for " + var + " in ;\n" + sp + "do\n" + inner_sp + body + ";\n" + sp + "done"
      end
    else
      result = "for " + var + " in \"$@\";\n" + sp + "do\n" + inner_sp + body + ";\n" + sp + "done"
    end
    if (node.redirects && !node.redirects.empty?)
      (node.redirects || []).each do |r|
        result = result + " " + format_redirect(r, false, false)
      end
    end
    return result
  end
  case node
  when ForArith
    node = node
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    result = "for ((" + node.init + "; " + node.cond + "; " + node.incr + "))\ndo\n" + inner_sp + body + ";\n" + sp + "done"
    if (node.redirects && !node.redirects.empty?)
      (node.redirects || []).each do |r|
        result = result + " " + format_redirect(r, false, false)
      end
    end
    return result
  end
  case node
  when Case
    node = node
    word = node.word.value
    patterns = []
    i = 0
    while i < node.patterns.length
      p_ = node.patterns[i]
      pat = p_.pattern.gsub("|", " | ")
      if !p_.body.nil?
        body = format_cmdsub_node(p_.body, indent + 8, false, false, false)
      else
        body = ""
      end
      term = p_.terminator
      pat_indent = repeat_str(" ", indent + 8)
      term_indent = repeat_str(" ", indent + 4)
      body_part = (body && !body.empty?) ? pat_indent + body + "\n" : "\n"
      if i == 0
        patterns.push(" " + pat + ")\n" + body_part + term_indent + term)
      else
        patterns.push(pat + ")\n" + body_part + term_indent + term)
      end
      i += 1
    end
    pattern_str = patterns.join("\n" + repeat_str(" ", indent + 4))
    redirects = ""
    if (node.redirects && !node.redirects.empty?)
      redirect_parts = []
      (node.redirects || []).each do |r|
        redirect_parts.append(format_redirect(r, false, false))
      end
      redirects = " " + redirect_parts.join(" ")
    end
    return "case " + word + " in" + pattern_str + "\n" + sp + "esac" + redirects
  end
  case node
  when Function
    node = node
    name = node.name
    inner_body = node.body.kind == "brace-group" ? node.body.body : node.body
    body = format_cmdsub_node(inner_body, indent + 4, false, false, false).gsub(/[;]+\z/, '')
    return "function #{name} () 
{ 
#{inner_sp}#{body}
}"
  end
  case node
  when Subshell
    node = node
    body = format_cmdsub_node(node.body, indent, in_procsub, compact_redirects, false)
    redirects = ""
    if (node.redirects && !node.redirects.empty?)
      redirect_parts = []
      (node.redirects || []).each do |r|
        redirect_parts.append(format_redirect(r, false, false))
      end
      redirects = redirect_parts.join(" ")
    end
    if procsub_first
      if (redirects && !redirects.empty?)
        return "(" + body + ") " + redirects
      end
      return "(" + body + ")"
    end
    if (redirects && !redirects.empty?)
      return "( " + body + " ) " + redirects
    end
    return "( " + body + " )"
  end
  case node
  when BraceGroup
    node = node
    body = format_cmdsub_node(node.body, indent, false, false, false)
    body = body.gsub(/[;]+\z/, '')
    terminator = body.end_with?(" &") ? " }" : "; }"
    redirects = ""
    if (node.redirects && !node.redirects.empty?)
      redirect_parts = []
      (node.redirects || []).each do |r|
        redirect_parts.append(format_redirect(r, false, false))
      end
      redirects = redirect_parts.join(" ")
    end
    if (redirects && !redirects.empty?)
      return "{ " + body + terminator + " " + redirects
    end
    return "{ " + body + terminator
  end
  case node
  when ArithmeticCommand
    node = node
    return "((" + node.raw_content + "))"
  end
  case node
  when ConditionalExpr
    node = node
    body = format_cond_body(node.body)
    return "[[ " + body + " ]]"
  end
  case node
  when Negation
    node = node
    if !node.pipeline.nil?
      return "! " + format_cmdsub_node(node.pipeline, indent, false, false, false)
    end
    return "! "
  end
  case node
  when Time_
    node = node
    prefix = node.posix ? "time -p " : "time "
    if !node.pipeline.nil?
      return prefix + format_cmdsub_node(node.pipeline, indent, false, false, false)
    end
    return prefix
  end
  return ""
end

def format_redirect(r, compact = false, heredoc_op_only = false)
  case r
  when HereDoc
    r = r
    if r.strip_tabs
      op = "<<-"
    else
      op = "<<"
    end
    if !r.fd.nil? && r.fd > 0
      op = r.fd.to_s + op
    end
    if r.quoted
      delim = "'" + r.delimiter + "'"
    else
      delim = r.delimiter
    end
    if heredoc_op_only
      return op + delim
    end
    return op + delim + "\n" + r.content + r.delimiter + "\n"
  end
  op = r.op
  if op == "1>"
    op = ">"
  elsif op == "0<"
    op = "<"
  end
  target = r.target.value
  target = r.target.expand_all_ansi_c_quotes(target)
  target = r.target.strip_locale_string_dollars(target)
  target = r.target.format_command_substitutions(target, false)
  if target.start_with?("&")
    was_input_close = false
    if target == "&-" && op.end_with?("<")
      was_input_close = true
      op = substring(op, 0, op.length - 1) + ">"
    end
    after_amp = substring(target, 1, target.length)
    is_literal_fd = after_amp == "-" || after_amp.length > 0 && (after_amp[0]).match?(/\A\d+\z/)
    if is_literal_fd
      if op == ">" || op == ">&"
        op = was_input_close ? "0>" : "1>"
      elsif op == "<" || op == "<&"
        op = "0<"
      end
    elsif op == "1>"
      op = ">"
    elsif op == "0<"
      op = "<"
    end
    return op + target
  end
  if op.end_with?("&")
    return op + target
  end
  if compact
    return op + target
  end
  return op + " " + target
end

def format_heredoc_body(r)
  return "\n" + r.content + r.delimiter + "\n"
end

def lookahead_for_esac(value, start, case_depth)
  i = start
  depth = case_depth
  quote = new_quote_state()
  while i < value.length
    c = value[i]
    if c == "\\" && i + 1 < value.length && quote.double
      i += 2
      next
    end
    if c == "'" && !quote.double
      quote.single = !quote.single
      i += 1
      next
    end
    if c == "\"" && !quote.single
      quote.double = !quote.double
      i += 1
      next
    end
    if quote.single || quote.double
      i += 1
      next
    end
    if starts_with_at(value, i, "case") && is_word_boundary(value, i, 4)
      depth += 1
      i += 4
    elsif starts_with_at(value, i, "esac") && is_word_boundary(value, i, 4)
      depth -= 1
      if depth == 0
        return true
      end
      i += 4
    elsif c == "("
      i += 1
    elsif c == ")"
      if depth > 0
        i += 1
      else
        break
      end
    else
      i += 1
    end
  end
  return false
end

def skip_backtick(value, start)
  i = start + 1
  while i < value.length && value[i] != "`"
    if value[i] == "\\" && i + 1 < value.length
      i += 2
    else
      i += 1
    end
  end
  if i < value.length
    i += 1
  end
  return i
end

def skip_single_quoted(s, start)
  i = start
  while i < s.length && s[i] != "'"
    i += 1
  end
  return i < s.length ? i + 1 : i
end

def skip_double_quoted(s, start)
  i = start
  n = s.length
  pass_next = false
  backq = false
  while i < n
    c = s[i]
    if pass_next
      pass_next = false
      i += 1
      next
    end
    if c == "\\"
      pass_next = true
      i += 1
      next
    end
    if backq
      if c == "`"
        backq = false
      end
      i += 1
      next
    end
    if c == "`"
      backq = true
      i += 1
      next
    end
    if c == "$" && i + 1 < n
      if s[i + 1] == "("
        i = find_cmdsub_end(s, i + 2)
        next
      end
      if s[i + 1] == "{"
        i = find_braced_param_end(s, i + 2)
        next
      end
    end
    if c == "\""
      return i + 1
    end
    i += 1
  end
  return i
end

def is_valid_arithmetic_start(value, start)
  scan_paren = 0
  scan_i = start + 3
  while scan_i < value.length
    scan_c = value[scan_i]
    if is_expansion_start(value, scan_i, "$(")
      scan_i = find_cmdsub_end(value, scan_i + 2)
      next
    end
    if scan_c == "("
      scan_paren += 1
    elsif scan_c == ")"
      if scan_paren > 0
        scan_paren -= 1
      elsif scan_i + 1 < value.length && value[scan_i + 1] == ")"
        return true
      else
        return false
      end
    end
    scan_i += 1
  end
  return false
end

def find_funsub_end(value, start)
  depth = 1
  i = start
  quote = new_quote_state()
  while i < value.length && depth > 0
    c = value[i]
    if c == "\\" && i + 1 < value.length && !quote.single
      i += 2
      next
    end
    if c == "'" && !quote.double
      quote.single = !quote.single
      i += 1
      next
    end
    if c == "\"" && !quote.single
      quote.double = !quote.double
      i += 1
      next
    end
    if quote.single || quote.double
      i += 1
      next
    end
    if c == "{"
      depth += 1
    elsif c == "}"
      depth -= 1
      if depth == 0
        return i + 1
      end
    end
    i += 1
  end
  return value.length
end

def find_cmdsub_end(value, start)
  depth = 1
  i = start
  case_depth = 0
  in_case_patterns = false
  arith_depth = 0
  arith_paren_depth = 0
  while i < value.length && depth > 0
    c = value[i]
    if c == "\\" && i + 1 < value.length
      i += 2
      next
    end
    if c == "'"
      i = skip_single_quoted(value, i + 1)
      next
    end
    if c == "\""
      i = skip_double_quoted(value, i + 1)
      next
    end
    if c == "#" && arith_depth == 0 && (i == start || value[i - 1] == " " || value[i - 1] == "\t" || value[i - 1] == "\n" || value[i - 1] == ";" || value[i - 1] == "|" || value[i - 1] == "&" || value[i - 1] == "(" || value[i - 1] == ")")
      while i < value.length && value[i] != "\n"
        i += 1
      end
      next
    end
    if starts_with_at(value, i, "<<<")
      i += 3
      while i < value.length && (value[i] == " " || value[i] == "\t")
        i += 1
      end
      if i < value.length && value[i] == "\""
        i += 1
        while i < value.length && value[i] != "\""
          if value[i] == "\\" && i + 1 < value.length
            i += 2
          else
            i += 1
          end
        end
        if i < value.length
          i += 1
        end
      elsif i < value.length && value[i] == "'"
        i += 1
        while i < value.length && value[i] != "'"
          i += 1
        end
        if i < value.length
          i += 1
        end
      else
        while i < value.length && (!" \t\n;|&<>()".include?(value[i]))
          i += 1
        end
      end
      next
    end
    if is_expansion_start(value, i, "$((")
      if is_valid_arithmetic_start(value, i)
        arith_depth += 1
        i += 3
        next
      end
      j = find_cmdsub_end(value, i + 2)
      i = j
      next
    end
    if arith_depth > 0 && arith_paren_depth == 0 && starts_with_at(value, i, "))")
      arith_depth -= 1
      i += 2
      next
    end
    if c == "`"
      i = skip_backtick(value, i)
      next
    end
    if arith_depth == 0 && starts_with_at(value, i, "<<")
      i = skip_heredoc(value, i)
      next
    end
    if starts_with_at(value, i, "case") && is_word_boundary(value, i, 4)
      case_depth += 1
      in_case_patterns = false
      i += 4
      next
    end
    if case_depth > 0 && starts_with_at(value, i, "in") && is_word_boundary(value, i, 2)
      in_case_patterns = true
      i += 2
      next
    end
    if starts_with_at(value, i, "esac") && is_word_boundary(value, i, 4)
      if case_depth > 0
        case_depth -= 1
        in_case_patterns = false
      end
      i += 4
      next
    end
    if starts_with_at(value, i, ";;")
      i += 2
      next
    end
    if c == "("
      if !(in_case_patterns && case_depth > 0)
        if arith_depth > 0
          arith_paren_depth += 1
        else
          depth += 1
        end
      end
    elsif c == ")"
      if in_case_patterns && case_depth > 0
        if !lookahead_for_esac(value, i + 1, case_depth)
          depth -= 1
        end
      elsif arith_depth > 0
        if arith_paren_depth > 0
          arith_paren_depth -= 1
        end
      else
        depth -= 1
      end
    end
    i += 1
  end
  return i
end

def find_braced_param_end(value, start)
  depth = 1
  i = start
  in_double = false
  dolbrace_state = DOLBRACESTATE_PARAM
  while i < value.length && depth > 0
    c = value[i]
    if c == "\\" && i + 1 < value.length
      i += 2
      next
    end
    if c == "'" && dolbrace_state == DOLBRACESTATE_QUOTE && !in_double
      i = skip_single_quoted(value, i + 1)
      next
    end
    if c == "\""
      in_double = !in_double
      i += 1
      next
    end
    if in_double
      i += 1
      next
    end
    if dolbrace_state == DOLBRACESTATE_PARAM && ("%#^,".include?(c))
      dolbrace_state = DOLBRACESTATE_QUOTE
    elsif dolbrace_state == DOLBRACESTATE_PARAM && (":-=?+/".include?(c))
      dolbrace_state = DOLBRACESTATE_WORD
    end
    if c == "[" && dolbrace_state == DOLBRACESTATE_PARAM && !in_double
      end_ = skip_subscript(value, i, 0)
      if end_ != -1
        i = end_
        next
      end
    end
    if (c == "<" || c == ">") && i + 1 < value.length && value[i + 1] == "("
      i = find_cmdsub_end(value, i + 2)
      next
    end
    if c == "{"
      depth += 1
    elsif c == "}"
      depth -= 1
      if depth == 0
        return i + 1
      end
    end
    if is_expansion_start(value, i, "$(")
      i = find_cmdsub_end(value, i + 2)
      next
    end
    if is_expansion_start(value, i, "${")
      i = find_braced_param_end(value, i + 2)
      next
    end
    i += 1
  end
  return i
end

def skip_heredoc(value, start)
  i = start + 2
  if i < value.length && value[i] == "-"
    i += 1
  end
  while i < value.length && is_whitespace_no_newline(value[i])
    i += 1
  end
  delim_start = i
  quote_char = nil
  if i < value.length && (value[i] == "\"" || value[i] == "'")
    quote_char = value[i]
    i += 1
    delim_start = i
    while i < value.length && value[i] != quote_char
      i += 1
    end
    delimiter = substring(value, delim_start, i)
    if i < value.length
      i += 1
    end
  elsif i < value.length && value[i] == "\\"
    i += 1
    delim_start = i
    if i < value.length
      i += 1
    end
    while i < value.length && !is_metachar(value[i])
      i += 1
    end
    delimiter = substring(value, delim_start, i)
  else
    while i < value.length && !is_metachar(value[i])
      i += 1
    end
    delimiter = substring(value, delim_start, i)
  end
  paren_depth = 0
  quote = new_quote_state()
  in_backtick = false
  while i < value.length && value[i] != "\n"
    c = value[i]
    if c == "\\" && i + 1 < value.length && (quote.double || in_backtick)
      i += 2
      next
    end
    if c == "'" && !quote.double && !in_backtick
      quote.single = !quote.single
      i += 1
      next
    end
    if c == "\"" && !quote.single && !in_backtick
      quote.double = !quote.double
      i += 1
      next
    end
    if c == "`" && !quote.single
      in_backtick = !in_backtick
      i += 1
      next
    end
    if quote.single || quote.double || in_backtick
      i += 1
      next
    end
    if c == "("
      paren_depth += 1
    elsif c == ")"
      if paren_depth == 0
        break
      end
      paren_depth -= 1
    end
    i += 1
  end
  if i < value.length && value[i] == ")"
    return i
  end
  if i < value.length && value[i] == "\n"
    i += 1
  end
  while i < value.length
    line_start = i
    line_end = i
    while line_end < value.length && value[line_end] != "\n"
      line_end += 1
    end
    line = substring(value, line_start, line_end)
    while line_end < value.length
      trailing_bs = 0
      j = line.length - 1
      while j > -1
        if line[j] == "\\"
          trailing_bs += 1
        else
          break
        end
        j += -1
      end
      if trailing_bs % 2 == 0
        break
      end
      line = line[0...-1]
      line_end += 1
      next_line_start = line_end
      while line_end < value.length && value[line_end] != "\n"
        line_end += 1
      end
      line = line + substring(value, next_line_start, line_end)
    end
    if start + 2 < value.length && value[start + 2] == "-"
      stripped = line.gsub(/\A[\t]+/, '')
    else
      stripped = line
    end
    if stripped == delimiter
      if line_end < value.length
        return line_end + 1
      else
        return line_end
      end
    end
    if stripped.start_with?(delimiter) && stripped.length > delimiter.length
      tabs_stripped = line.length - stripped.length
      return line_start + tabs_stripped + delimiter.length
    end
    if line_end < value.length
      i = line_end + 1
    else
      i = line_end
    end
  end
  return i
end

def find_heredoc_content_end(source, start, delimiters)
  if !(delimiters && !delimiters.empty?)
    return [start, start]
  end
  pos = start
  while pos < source.length && source[pos] != "\n"
    pos += 1
  end
  if pos >= source.length
    return [start, start]
  end
  content_start = pos
  pos += 1
  delimiters.each do |item|
    delimiter = item[0]
    strip_tabs = item[1]
    while pos < source.length
      line_start = pos
      line_end = pos
      while line_end < source.length && source[line_end] != "\n"
        line_end += 1
      end
      line = substring(source, line_start, line_end)
      while line_end < source.length
        trailing_bs = 0
        j = line.length - 1
        while j > -1
          if line[j] == "\\"
            trailing_bs += 1
          else
            break
          end
          j += -1
        end
        if trailing_bs % 2 == 0
          break
        end
        line = line[0...-1]
        line_end += 1
        next_line_start = line_end
        while line_end < source.length && source[line_end] != "\n"
          line_end += 1
        end
        line = line + substring(source, next_line_start, line_end)
      end
      if strip_tabs
        line_stripped = line.gsub(/\A[\t]+/, '')
      else
        line_stripped = line
      end
      if line_stripped == delimiter
        pos = line_end < source.length ? line_end + 1 : line_end
        break
      end
      if line_stripped.start_with?(delimiter) && line_stripped.length > delimiter.length
        tabs_stripped = line.length - line_stripped.length
        pos = line_start + tabs_stripped + delimiter.length
        break
      end
      pos = line_end < source.length ? line_end + 1 : line_end
    end
  end
  return [content_start, pos]
end

def is_word_boundary(s, pos, word_len)
  if pos > 0
    prev = s[pos - 1]
    if (prev).match?(/\A[[:alnum:]]+\z/) || prev == "_"
      return false
    end
    if "{}!".include?(prev)
      return false
    end
  end
  end_ = pos + word_len
  if end_ < s.length && ((s[end_]).match?(/\A[[:alnum:]]+\z/) || s[end_] == "_")
    return false
  end
  return true
end

def is_quote(c)
  return c == "'" || c == "\""
end

def collapse_whitespace(s)
  result = []
  prev_was_ws = false
  s.each_char do |c|
    if c == " " || c == "\t"
      if !prev_was_ws
        result.push(" ")
      end
      prev_was_ws = true
    else
      result.push(c)
      prev_was_ws = false
    end
  end
  joined = result.join
  return joined.gsub(/\A[ \t]+|[ \t]+\z/, '')
end

def count_trailing_backslashes(s)
  count = 0
  i = s.length - 1
  while i > -1
    if s[i] == "\\"
      count += 1
    else
      break
    end
    i += -1
  end
  return count
end

def normalize_heredoc_delimiter(delimiter)
  result = []
  i = 0
  while i < delimiter.length
    if i + 1 < delimiter.length && delimiter[i...i + 2] == "$("
      result.push("$(")
      i += 2
      depth = 1
      inner = []
      while i < delimiter.length && depth > 0
        if delimiter[i] == "("
          depth += 1
          inner.push(delimiter[i])
        elsif delimiter[i] == ")"
          depth -= 1
          if depth == 0
            inner_str = inner.join
            inner_str = collapse_whitespace(inner_str)
            result.push(inner_str)
            result.push(")")
          else
            inner.push(delimiter[i])
          end
        else
          inner.push(delimiter[i])
        end
        i += 1
      end
    elsif i + 1 < delimiter.length && delimiter[i...i + 2] == "${"
      result.push("${")
      i += 2
      depth = 1
      inner = []
      while i < delimiter.length && depth > 0
        if delimiter[i] == "{"
          depth += 1
          inner.push(delimiter[i])
        elsif delimiter[i] == "}"
          depth -= 1
          if depth == 0
            inner_str = inner.join
            inner_str = collapse_whitespace(inner_str)
            result.push(inner_str)
            result.push("}")
          else
            inner.push(delimiter[i])
          end
        else
          inner.push(delimiter[i])
        end
        i += 1
      end
    elsif i + 1 < delimiter.length && ("<>".include?(delimiter[i])) && delimiter[i + 1] == "("
      result.push(delimiter[i])
      result.push("(")
      i += 2
      depth = 1
      inner = []
      while i < delimiter.length && depth > 0
        if delimiter[i] == "("
          depth += 1
          inner.push(delimiter[i])
        elsif delimiter[i] == ")"
          depth -= 1
          if depth == 0
            inner_str = inner.join
            inner_str = collapse_whitespace(inner_str)
            result.push(inner_str)
            result.push(")")
          else
            inner.push(delimiter[i])
          end
        else
          inner.push(delimiter[i])
        end
        i += 1
      end
    else
      result.push(delimiter[i])
      i += 1
    end
  end
  return result.join
end

def is_metachar(c)
  return c == " " || c == "\t" || c == "\n" || c == "|" || c == "&" || c == ";" || c == "(" || c == ")" || c == "<" || c == ">"
end

def is_funsub_char(c)
  return c == " " || c == "\t" || c == "\n" || c == "|"
end

def is_extglob_prefix(c)
  return c == "@" || c == "?" || c == "*" || c == "+" || c == "!"
end

def is_redirect_char(c)
  return c == "<" || c == ">"
end

def is_special_param(c)
  return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-" || c == "&"
end

def is_special_param_unbraced(c)
  return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-"
end

def is_digit(c)
  return c >= "0" && c <= "9"
end

def is_semicolon_or_newline(c)
  return c == ";" || c == "\n"
end

def is_word_end_context(c)
  return c == " " || c == "\t" || c == "\n" || c == ";" || c == "|" || c == "&" || c == "<" || c == ">" || c == "(" || c == ")"
end

def skip_matched_pair(s, start, open, close, flags = 0)
  n = s.length
  if (flags & SMP_PAST_OPEN) != 0
    i = start
  else
    if start >= n || s[start] != open
      return -1
    end
    i = start + 1
  end
  depth = 1
  pass_next = false
  backq = false
  while i < n && depth > 0
    c = s[i]
    if pass_next
      pass_next = false
      i += 1
      next
    end
    literal = flags & SMP_LITERAL
    if literal == 0 && c == "\\"
      pass_next = true
      i += 1
      next
    end
    if backq
      if c == "`"
        backq = false
      end
      i += 1
      next
    end
    if literal == 0 && c == "`"
      backq = true
      i += 1
      next
    end
    if literal == 0 && c == "'"
      i = skip_single_quoted(s, i + 1)
      next
    end
    if literal == 0 && c == "\""
      i = skip_double_quoted(s, i + 1)
      next
    end
    if literal == 0 && is_expansion_start(s, i, "$(")
      i = find_cmdsub_end(s, i + 2)
      next
    end
    if literal == 0 && is_expansion_start(s, i, "${")
      i = find_braced_param_end(s, i + 2)
      next
    end
    if literal == 0 && c == open
      depth += 1
    elsif c == close
      depth -= 1
    end
    i += 1
  end
  return depth == 0 ? i : -1
end

def skip_subscript(s, start, flags = 0)
  return skip_matched_pair(s, start, "[", "]", flags)
end

def assignment(s, flags = 0)
  if !(s && !s.empty?)
    return -1
  end
  if !((s[0]).match?(/\A[[:alpha:]]+\z/) || s[0] == "_")
    return -1
  end
  i = 1
  while i < s.length
    c = s[i]
    if c == "="
      return i
    end
    if c == "["
      sub_flags = (flags & 2) != 0 ? SMP_LITERAL : 0
      end_ = skip_subscript(s, i, sub_flags)
      if end_ == -1
        return -1
      end
      i = end_
      if i < s.length && s[i] == "+"
        i += 1
      end
      if i < s.length && s[i] == "="
        return i
      end
      return -1
    end
    if c == "+"
      if i + 1 < s.length && s[i + 1] == "="
        return i + 1
      end
      return -1
    end
    if !((c).match?(/\A[[:alnum:]]+\z/) || c == "_")
      return -1
    end
    i += 1
  end
  return -1
end

def is_array_assignment_prefix(chars)
  if !(chars && !chars.empty?)
    return false
  end
  if !((chars[0]).match?(/\A[[:alpha:]]+\z/) || chars[0] == "_")
    return false
  end
  s = chars.join
  i = 1
  while i < s.length && ((s[i]).match?(/\A[[:alnum:]]+\z/) || s[i] == "_")
    i += 1
  end
  while i < s.length
    if s[i] != "["
      return false
    end
    end_ = skip_subscript(s, i, SMP_LITERAL)
    if end_ == -1
      return false
    end
    i = end_
  end
  return true
end

def is_special_param_or_digit(c)
  return is_special_param(c) || is_digit(c)
end

def is_param_expansion_op(c)
  return c == ":" || c == "-" || c == "=" || c == "+" || c == "?" || c == "#" || c == "%" || c == "/" || c == "^" || c == "," || c == "@" || c == "*" || c == "["
end

def is_simple_param_op(c)
  return c == "-" || c == "=" || c == "?" || c == "+"
end

def is_escape_char_in_backtick(c)
  return c == "$" || c == "`" || c == "\\"
end

def is_negation_boundary(c)
  return is_whitespace(c) || c == ";" || c == "|" || c == ")" || c == "&" || c == ">" || c == "<"
end

def is_backslash_escaped(value, idx)
  bs_count = 0
  j = idx - 1
  while j >= 0 && value[j] == "\\"
    bs_count += 1
    j -= 1
  end
  return bs_count % 2 == 1
end

def is_dollar_dollar_paren(value, idx)
  dollar_count = 0
  j = idx - 1
  while j >= 0 && value[j] == "$"
    dollar_count += 1
    j -= 1
  end
  return dollar_count % 2 == 1
end

def is_paren(c)
  return c == "(" || c == ")"
end

def is_caret_or_bang(c)
  return c == "!" || c == "^"
end

def is_at_or_star(c)
  return c == "@" || c == "*"
end

def is_digit_or_dash(c)
  return is_digit(c) || c == "-"
end

def is_newline_or_right_paren(c)
  return c == "\n" || c == ")"
end

def is_semicolon_newline_brace(c)
  return c == ";" || c == "\n" || c == "{"
end

def looks_like_assignment(s)
  return assignment(s, 0) != -1
end

def is_valid_identifier(name)
  if !(name && !name.empty?)
    return false
  end
  if !((name[0]).match?(/\A[[:alpha:]]+\z/) || name[0] == "_")
    return false
  end
  name[1..].each_char do |c|
    if !((c).match?(/\A[[:alnum:]]+\z/) || c == "_")
      return false
    end
  end
  return true
end

def parse(source, extglob = false)
  parser = new_parser(source, false, extglob)
  return parser.parse
end

def new_parse_error(message, pos = nil, line = nil)
  self_ = ParseError.new()
  self_.message = message
  self_.pos = pos
  self_.line = line
  return self_
end

def new_matched_pair_error(message, pos, line)
  return MatchedPairError.new()
end

def new_quote_state()
  self_ = QuoteState.new()
  self_.single = false
  self_.double = false
  self_.stack = []
  return self_
end

def new_parse_context(kind = 0)
  self_ = ParseContext.new()
  self_.kind = kind
  self_.paren_depth = 0
  self_.brace_depth = 0
  self_.bracket_depth = 0
  self_.case_depth = 0
  self_.arith_depth = 0
  self_.arith_paren_depth = 0
  self_.quote = new_quote_state()
  return self_
end

def new_context_stack()
  self_ = ContextStack.new()
  self_.stack = [new_parse_context(0)]
  return self_
end

def new_lexer(source, extglob = false)
  self_ = Lexer.new()
  self_.source = source
  self_.pos = 0
  self_.length = source.length
  self_.quote = new_quote_state()
  self_.token_cache = nil
  self_.parser_state = PARSERSTATEFLAGS_NONE
  self_.dolbrace_state = DOLBRACESTATE_NONE
  self_.pending_heredocs = []
  self_.extglob = extglob
  self_.parser = nil
  self_.eof_token = ""
  self_.last_read_token = nil
  self_.word_context = WORD_CTX_NORMAL
  self_.at_command_start = false
  self_.in_array_literal = false
  self_.in_assign_builtin = false
  self_.post_read_pos = 0
  self_.cached_word_context = WORD_CTX_NORMAL
  self_.cached_at_command_start = false
  self_.cached_in_array_literal = false
  self_.cached_in_assign_builtin = false
  return self_
end

def new_parser(source, in_process_sub = false, extglob = false)
  self_ = Parser.new()
  self_.source = source
  self_.pos = 0
  self_.length = source.length
  self_.pending_heredocs = []
  self_.cmdsub_heredoc_end = -1
  self_.saw_newline_in_single_quote = false
  self_.in_process_sub = in_process_sub
  self_.extglob = extglob
  self_.ctx = new_context_stack()
  self_.lexer = new_lexer(source, extglob)
  self_.lexer.parser = self_
  self_.token_history = [nil, nil, nil, nil]
  self_.parser_state = PARSERSTATEFLAGS_NONE
  self_.dolbrace_state = DOLBRACESTATE_NONE
  self_.eof_token = ""
  self_.word_context = WORD_CTX_NORMAL
  self_.at_command_start = false
  self_.in_array_literal = false
  self_.in_assign_builtin = false
  self_.arith_src = ""
  self_.arith_pos = 0
  self_.arith_len = 0
  return self_
end
