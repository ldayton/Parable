-- Generated Lua code

local function _table_slice(t, i, j)
  local result = {}
  j = j or #t
  for k = i, j do
    result[#result + 1] = t[k]
  end
  return result
end

local function _string_split(s, sep)
  if sep == '' then
    local result = {}
    for i = 1, #s do
      result[i] = s:sub(i, i)
    end
    return result
  end
  local result = {}
  local pattern = '([^' .. sep .. ']+)'
  for part in string.gmatch(s, pattern) do
    result[#result + 1] = part
  end
  return result
end

local function _set_contains(s, v)
  return s[v] == true
end

local function _set_add(s, v)
  s[v] = true
end

local function _string_find(s, sub, start)
  start = start or 0
  local pos = string.find(s, sub, start + 1, true)
  if pos then return pos - 1 else return -1 end
end

local function _string_rfind(s, sub)
  local last = -1
  local start = 1
  while true do
    local pos = string.find(s, sub, start, true)
    if not pos then break end
    last = pos - 1
    start = pos + 1
  end
  return last
end

local function _range(start, stop, step)
  if stop == nil then stop = start; start = 0 end
  step = step or 1
  local result = {}
  if step > 0 then
    for i = start, stop - 1, step do
      result[#result + 1] = i
    end
  else
    for i = start, stop + 1, step do
      result[#result + 1] = i
    end
  end
  return result
end

local function _map_get(m, key, default)
  local v = m[key]
  if v == nil then return default else return v end
end

local function _bytes_to_string(bytes)
  local chars = {}
  for i, b in ipairs(bytes) do
    chars[i] = string.char(b)
  end
  return table.concat(chars, '')
end
ANSI_C_ESCAPES = {["a"] = 7, ["b"] = 8, ["e"] = 27, ["E"] = 27, ["f"] = 12, ["n"] = 10, ["r"] = 13, ["t"] = 9, ["v"] = 11, ["\\"] = 92, ["\""] = 34, ["?"] = 63}
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
RESERVED_WORDS = {["if"] = true, ["then"] = true, ["elif"] = true, ["else"] = true, ["fi"] = true, ["while"] = true, ["until"] = true, ["for"] = true, ["select"] = true, ["do"] = true, ["done"] = true, ["case"] = true, ["esac"] = true, ["in"] = true, ["function"] = true, ["coproc"] = true}
COND_UNARY_OPS = {["-a"] = true, ["-b"] = true, ["-c"] = true, ["-d"] = true, ["-e"] = true, ["-f"] = true, ["-g"] = true, ["-h"] = true, ["-k"] = true, ["-p"] = true, ["-r"] = true, ["-s"] = true, ["-t"] = true, ["-u"] = true, ["-w"] = true, ["-x"] = true, ["-G"] = true, ["-L"] = true, ["-N"] = true, ["-O"] = true, ["-S"] = true, ["-z"] = true, ["-n"] = true, ["-o"] = true, ["-v"] = true, ["-R"] = true}
COND_BINARY_OPS = {["=="] = true, ["!="] = true, ["=~"] = true, ["="] = true, ["<"] = true, [">"] = true, ["-eq"] = true, ["-ne"] = true, ["-lt"] = true, ["-le"] = true, ["-gt"] = true, ["-ge"] = true, ["-nt"] = true, ["-ot"] = true, ["-ef"] = true}
COMPOUND_KEYWORDS = {["while"] = true, ["until"] = true, ["for"] = true, ["if"] = true, ["case"] = true, ["select"] = true}
ASSIGNMENT_BUILTINS = {["alias"] = true, ["declare"] = true, ["typeset"] = true, ["local"] = true, ["export"] = true, ["readonly"] = true, ["eval"] = true, ["let"] = true}
SMP_LITERAL = 1
SMP_PAST_OPEN = 2
WORD_CTX_NORMAL = 0
WORD_CTX_COND = 1
WORD_CTX_REGEX = 2

-- Interface: Node
--   get_kind()
--   to_sexp()

ParseError = {}
ParseError.__index = ParseError

function ParseError:new(message, pos, line)
  local self = setmetatable({}, ParseError)
  if message == nil then message = "" end
  self.message = message
  if pos == nil then pos = 0 end
  self.pos = pos
  if line == nil then line = 0 end
  self.line = line
  return self
end

function ParseError:format_message()
  if self.line ~= 0 and self.pos ~= 0 then
    return string.format("Parse error at line %s, position %s: %s", self.line, self.pos, self.message)
  elseif self.pos ~= 0 then
    return string.format("Parse error at position %s: %s", self.pos, self.message)
  end
  return string.format("Parse error: %s", self.message)
end

MatchedPairError = {}
MatchedPairError.__index = MatchedPairError

function MatchedPairError:new()
  local self = setmetatable({}, MatchedPairError)
  return self
end


Token = {}
Token.__index = Token

function Token:new(type_, value, pos, parts, word)
  local self = setmetatable({}, Token)
  if type_ == nil then type_ = 0 end
  self.type_ = type_
  if value == nil then value = "" end
  self.value = value
  if pos == nil then pos = 0 end
  self.pos = pos
  if parts == nil then parts = {} end
  self.parts = parts
  if word == nil then word = nil end
  self.word = word
  return self
end

function Token:_repr__()
  if (self.word ~= nil) then
    return string.format("Token(%s, %s, %s, word=%s)", self.type_, self.value, self.pos, self.word)
  end
  if (#(self.parts) > 0) then
    return string.format("Token(%s, %s, %s, parts=%s)", self.type_, self.value, self.pos, #self.parts)
  end
  return string.format("Token(%s, %s, %s)", self.type_, self.value, self.pos)
end




SavedParserState = {}
SavedParserState.__index = SavedParserState

function SavedParserState:new(parser_state, dolbrace_state, pending_heredocs, ctx_stack, eof_token)
  local self = setmetatable({}, SavedParserState)
  if parser_state == nil then parser_state = 0 end
  self.parser_state = parser_state
  if dolbrace_state == nil then dolbrace_state = 0 end
  self.dolbrace_state = dolbrace_state
  if pending_heredocs == nil then pending_heredocs = {} end
  self.pending_heredocs = pending_heredocs
  if ctx_stack == nil then ctx_stack = {} end
  self.ctx_stack = ctx_stack
  if eof_token == nil then eof_token = "" end
  self.eof_token = eof_token
  return self
end

QuoteState = {}
QuoteState.__index = QuoteState

function QuoteState:new(single, double, stack)
  local self = setmetatable({}, QuoteState)
  if single == nil then single = false end
  self.single = single
  if double == nil then double = false end
  self.double = double
  if stack == nil then stack = {} end
  self.stack = stack
  return self
end

function QuoteState:push()
  ;(function() table.insert(self.stack, {self.single, self.double}); return self.stack end)()
  self.single = false
  self.double = false
end

function QuoteState:pop()
  if (#(self.stack) > 0) then
    self.single, self.double = table.unpack(table.remove(self.stack))
  end
end

function QuoteState:in_quotes()
  return self.single or self.double
end

function QuoteState:copy()
  local qs
  qs = new_quote_state()
  qs.single = self.single
  qs.double = self.double
  qs.stack = (function() local t = {}; for i, v in ipairs(self.stack) do t[i] = v end; return t end)()
  return qs
end

function QuoteState:outer_double()
  if #self.stack == 0 then
    return false
  end
  return self.stack[#self.stack - 1 + 1][2]
end

ParseContext = {}
ParseContext.__index = ParseContext

function ParseContext:new(kind, paren_depth, brace_depth, bracket_depth, case_depth, arith_depth, arith_paren_depth, quote)
  local self = setmetatable({}, ParseContext)
  if kind == nil then kind = 0 end
  self.kind = kind
  if paren_depth == nil then paren_depth = 0 end
  self.paren_depth = paren_depth
  if brace_depth == nil then brace_depth = 0 end
  self.brace_depth = brace_depth
  if bracket_depth == nil then bracket_depth = 0 end
  self.bracket_depth = bracket_depth
  if case_depth == nil then case_depth = 0 end
  self.case_depth = case_depth
  if arith_depth == nil then arith_depth = 0 end
  self.arith_depth = arith_depth
  if arith_paren_depth == nil then arith_paren_depth = 0 end
  self.arith_paren_depth = arith_paren_depth
  if quote == nil then quote = nil end
  self.quote = quote
  return self
end

function ParseContext:copy()
  local ctx
  ctx = new_parse_context(self.kind)
  ctx.paren_depth = self.paren_depth
  ctx.brace_depth = self.brace_depth
  ctx.bracket_depth = self.bracket_depth
  ctx.case_depth = self.case_depth
  ctx.arith_depth = self.arith_depth
  ctx.arith_paren_depth = self.arith_paren_depth
  ctx.quote = self.quote:copy()
  return ctx
end

ContextStack = {}
ContextStack.__index = ContextStack

function ContextStack:new(stack)
  local self = setmetatable({}, ContextStack)
  if stack == nil then stack = {} end
  self.stack = stack
  return self
end

function ContextStack:get_current()
  return self.stack[#self.stack - 1 + 1]
end

function ContextStack:push(kind)
  ;(function() table.insert(self.stack, new_parse_context(kind)); return self.stack end)()
end

function ContextStack:pop()
  if #self.stack > 1 then
    return table.remove(self.stack)
  end
  return self.stack[0 + 1]
end

function ContextStack:copy_stack()
  local ctx, result
  result = {}
  for _, ctx in ipairs(self.stack) do
    ;(function() table.insert(result, ctx:copy()); return result end)()
  end
  return result
end

function ContextStack:restore_from(saved_stack)
  local ctx, result
  result = {}
  for _, ctx in ipairs(saved_stack) do
    ;(function() table.insert(result, ctx:copy()); return result end)()
  end
  self.stack = result
end

Lexer = {}
Lexer.__index = Lexer

function Lexer:new(reserved_words, source, pos, length, quote, token_cache, parser_state, dolbrace_state, pending_heredocs, extglob, parser, eof_token, last_read_token, word_context, at_command_start, in_array_literal, in_assign_builtin, post_read_pos, cached_word_context, cached_at_command_start, cached_in_array_literal, cached_in_assign_builtin)
  local self = setmetatable({}, Lexer)
  if reserved_words == nil then reserved_words = {} end
  self.reserved_words = reserved_words
  if source == nil then source = "" end
  self.source = source
  if pos == nil then pos = 0 end
  self.pos = pos
  if length == nil then length = 0 end
  self.length = length
  if quote == nil then quote = nil end
  self.quote = quote
  if token_cache == nil then token_cache = nil end
  self.token_cache = token_cache
  if parser_state == nil then parser_state = 0 end
  self.parser_state = parser_state
  if dolbrace_state == nil then dolbrace_state = 0 end
  self.dolbrace_state = dolbrace_state
  if pending_heredocs == nil then pending_heredocs = {} end
  self.pending_heredocs = pending_heredocs
  if extglob == nil then extglob = false end
  self.extglob = extglob
  if parser == nil then parser = nil end
  self.parser = parser
  if eof_token == nil then eof_token = "" end
  self.eof_token = eof_token
  if last_read_token == nil then last_read_token = nil end
  self.last_read_token = last_read_token
  if word_context == nil then word_context = 0 end
  self.word_context = word_context
  if at_command_start == nil then at_command_start = false end
  self.at_command_start = at_command_start
  if in_array_literal == nil then in_array_literal = false end
  self.in_array_literal = in_array_literal
  if in_assign_builtin == nil then in_assign_builtin = false end
  self.in_assign_builtin = in_assign_builtin
  if post_read_pos == nil then post_read_pos = 0 end
  self.post_read_pos = post_read_pos
  if cached_word_context == nil then cached_word_context = 0 end
  self.cached_word_context = cached_word_context
  if cached_at_command_start == nil then cached_at_command_start = false end
  self.cached_at_command_start = cached_at_command_start
  if cached_in_array_literal == nil then cached_in_array_literal = false end
  self.cached_in_array_literal = cached_in_array_literal
  if cached_in_assign_builtin == nil then cached_in_assign_builtin = false end
  self.cached_in_assign_builtin = cached_in_assign_builtin
  return self
end

function Lexer:peek()
  if self.pos >= self.length then
    return ""
  end
  return string.sub(self.source, self.pos + 1, self.pos + 1)
end

function Lexer:advance()
  local c
  if self.pos >= self.length then
    return ""
  end
  c = string.sub(self.source, self.pos + 1, self.pos + 1)
  self.pos = self.pos + 1
  return c
end

function Lexer:at_end()
  return self.pos >= self.length
end

function Lexer:lookahead(n)
  return substring(self.source, self.pos, self.pos + n)
end

function Lexer:is_metachar(c)
  return ((string.find("|&;()<> \t\n", c, 1, true) ~= nil))
end

function Lexer:read_operator()
  local c, start, three, two
  start = self.pos
  c = self:peek()
  if c == "" then
    return nil
  end
  two = self:lookahead(2)
  three = self:lookahead(3)
  if three == ";;&" then
    self.pos = self.pos + 3
    return Token:new(TOKENTYPE_SEMI_SEMI_AMP, three, start, nil, nil)
  end
  if three == "<<-" then
    self.pos = self.pos + 3
    return Token:new(TOKENTYPE_LESS_LESS_MINUS, three, start, nil, nil)
  end
  if three == "<<<" then
    self.pos = self.pos + 3
    return Token:new(TOKENTYPE_LESS_LESS_LESS, three, start, nil, nil)
  end
  if three == "&>>" then
    self.pos = self.pos + 3
    return Token:new(TOKENTYPE_AMP_GREATER_GREATER, three, start, nil, nil)
  end
  if two == "&&" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_AND_AND, two, start, nil, nil)
  end
  if two == "||" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_OR_OR, two, start, nil, nil)
  end
  if two == ";;" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_SEMI_SEMI, two, start, nil, nil)
  end
  if two == ";&" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_SEMI_AMP, two, start, nil, nil)
  end
  if two == "<<" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_LESS_LESS, two, start, nil, nil)
  end
  if two == ">>" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_GREATER_GREATER, two, start, nil, nil)
  end
  if two == "<&" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_LESS_AMP, two, start, nil, nil)
  end
  if two == ">&" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_GREATER_AMP, two, start, nil, nil)
  end
  if two == "<>" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_LESS_GREATER, two, start, nil, nil)
  end
  if two == ">|" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_GREATER_PIPE, two, start, nil, nil)
  end
  if two == "&>" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_AMP_GREATER, two, start, nil, nil)
  end
  if two == "|&" then
    self.pos = self.pos + 2
    return Token:new(TOKENTYPE_PIPE_AMP, two, start, nil, nil)
  end
  if c == ";" then
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_SEMI, c, start, nil, nil)
  end
  if c == "|" then
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_PIPE, c, start, nil, nil)
  end
  if c == "&" then
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_AMP, c, start, nil, nil)
  end
  if c == "(" then
    if self.word_context == WORD_CTX_REGEX then
      return nil
    end
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_LPAREN, c, start, nil, nil)
  end
  if c == ")" then
    if self.word_context == WORD_CTX_REGEX then
      return nil
    end
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_RPAREN, c, start, nil, nil)
  end
  if c == "<" then
    if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
      return nil
    end
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_LESS, c, start, nil, nil)
  end
  if c == ">" then
    if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
      return nil
    end
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_GREATER, c, start, nil, nil)
  end
  if c == "\n" then
    self.pos = self.pos + 1
    return Token:new(TOKENTYPE_NEWLINE, c, start, nil, nil)
  end
  return nil
end

function Lexer:skip_blanks()
  local c
  while self.pos < self.length do
    c = string.sub(self.source, self.pos + 1, self.pos + 1)
    if c ~= " " and c ~= "\t" then
      break
    end
    self.pos = self.pos + 1
  end
end

function Lexer:skip_comment()
  local prev
  if self.pos >= self.length then
    return false
  end
  if string.sub(self.source, self.pos + 1, self.pos + 1) ~= "#" then
    return false
  end
  if self.quote:in_quotes() then
    return false
  end
  if self.pos > 0 then
    prev = string.sub(self.source, self.pos - 1 + 1, self.pos - 1 + 1)
    if (not (string.find(" \t\n;|&(){}", prev, 1, true) ~= nil)) then
      return false
    end
  end
  while self.pos < self.length and string.sub(self.source, self.pos + 1, self.pos + 1) ~= "\n" do
    self.pos = self.pos + 1
  end
  return true
end

function Lexer:read_single_quote(start)
  local c, chars, saw_newline
  chars = {"'"}
  saw_newline = false
  while self.pos < self.length do
    c = string.sub(self.source, self.pos + 1, self.pos + 1)
    if c == "\n" then
      saw_newline = true
    end
    ;(function() table.insert(chars, c); return chars end)()
    self.pos = self.pos + 1
    if c == "'" then
      return {table.concat(chars, ""), saw_newline}
    end
  end
  error({ParseError = true, message = "Unterminated single quote", pos = start})
end

function Lexer:is_word_terminator(ctx, ch, bracket_depth, paren_depth)
  if ctx == WORD_CTX_REGEX then
    if ch == "]" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "]" then
      return true
    end
    if ch == "&" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "&" then
      return true
    end
    if ch == ")" and paren_depth == 0 then
      return true
    end
    return is_whitespace(ch) and paren_depth == 0
  end
  if ctx == WORD_CTX_COND then
    if ch == "]" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "]" then
      return true
    end
    if ch == ")" then
      return true
    end
    if ch == "&" then
      return true
    end
    if ch == "|" then
      return true
    end
    if ch == ";" then
      return true
    end
    if is_redirect_char(ch) and not (self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(") then
      return true
    end
    return is_whitespace(ch)
  end
  if (self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN ~= 0) and self.eof_token ~= "" and ch == self.eof_token and bracket_depth == 0 then
    return true
  end
  if is_redirect_char(ch) and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
    return false
  end
  return is_metachar(ch) and bracket_depth == 0
end

function Lexer:read_bracket_expression(chars, parts, for_regex, paren_depth)
  local bracket_will_close, c, next_ch, sc, scan
  if for_regex then
    scan = self.pos + 1
    if scan < self.length and string.sub(self.source, scan + 1, scan + 1) == "^" then
      scan = scan + 1
    end
    if scan < self.length and string.sub(self.source, scan + 1, scan + 1) == "]" then
      scan = scan + 1
    end
    bracket_will_close = false
    while scan < self.length do
      sc = string.sub(self.source, scan + 1, scan + 1)
      if sc == "]" and scan + 1 < self.length and string.sub(self.source, scan + 1 + 1, scan + 1 + 1) == "]" then
        break
      end
      if sc == ")" and paren_depth > 0 then
        break
      end
      if sc == "&" and scan + 1 < self.length and string.sub(self.source, scan + 1 + 1, scan + 1 + 1) == "&" then
        break
      end
      if sc == "]" then
        bracket_will_close = true
        break
      end
      if sc == "[" and scan + 1 < self.length and string.sub(self.source, scan + 1 + 1, scan + 1 + 1) == ":" then
        scan = scan + 2
        while scan < self.length and not (string.sub(self.source, scan + 1, scan + 1) == ":" and scan + 1 < self.length and string.sub(self.source, scan + 1 + 1, scan + 1 + 1) == "]") do
          scan = scan + 1
        end
        if scan < self.length then
          scan = scan + 2
        end
        goto continue
      end
      scan = scan + 1
      ::continue::
    end
    if not bracket_will_close then
      return false
    end
  else
    if self.pos + 1 >= self.length then
      return false
    end
    next_ch = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
    if is_whitespace_no_newline(next_ch) or next_ch == "&" or next_ch == "|" then
      return false
    end
  end
  ;(function() table.insert(chars, self:advance()); return chars end)()
  if not self:at_end() and self:peek() == "^" then
    ;(function() table.insert(chars, self:advance()); return chars end)()
  end
  if not self:at_end() and self:peek() == "]" then
    ;(function() table.insert(chars, self:advance()); return chars end)()
  end
  while not self:at_end() do
    c = self:peek()
    if c == "]" then
      ;(function() table.insert(chars, self:advance()); return chars end)()
      break
    end
    if c == "[" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == ":" then
      ;(function() table.insert(chars, self:advance()); return chars end)()
      ;(function() table.insert(chars, self:advance()); return chars end)()
      while not self:at_end() and not (self:peek() == ":" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "]") do
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      if not self:at_end() then
        ;(function() table.insert(chars, self:advance()); return chars end)()
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
    elseif not for_regex and c == "[" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "=" then
      ;(function() table.insert(chars, self:advance()); return chars end)()
      ;(function() table.insert(chars, self:advance()); return chars end)()
      while not self:at_end() and not (self:peek() == "=" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "]") do
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      if not self:at_end() then
        ;(function() table.insert(chars, self:advance()); return chars end)()
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
    elseif not for_regex and c == "[" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "." then
      ;(function() table.insert(chars, self:advance()); return chars end)()
      ;(function() table.insert(chars, self:advance()); return chars end)()
      while not self:at_end() and not (self:peek() == "." and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "]") do
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      if not self:at_end() then
        ;(function() table.insert(chars, self:advance()); return chars end)()
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
    elseif for_regex and c == "$" then
      self:sync_to_parser()
      if not self.parser:parse_dollar_expansion(chars, parts, false) then
        self:sync_from_parser()
        ;(function() table.insert(chars, self:advance()); return chars end)()
      else
        self:sync_from_parser()
      end
    else
      ;(function() table.insert(chars, self:advance()); return chars end)()
    end
  end
  return true
end

function Lexer:parse_matched_pair(open_char, close_char, flags, initial_was_dollar)
  local after_brace_pos, arith_node, arith_text, ch, chars, cmd_node, cmd_text, count, direction, in_dquote, nested, next_ch, param_node, param_text, pass_next, procsub_node, procsub_text, quote_flags, start, was_dollar, was_gtlt
  start = self.pos
  count = 1
  chars = {}
  pass_next = false
  was_dollar = initial_was_dollar
  was_gtlt = false
  while count > 0 do
    if self:at_end() then
      error({MatchedPairError = true, message = string.format("unexpected EOF while looking for matching `%s'", close_char), pos = start})
    end
    ch = self:advance()
    if (flags & MATCHEDPAIRFLAGS_DOLBRACE ~= 0) and self.dolbrace_state == DOLBRACESTATE_OP then
      if (not (string.find("#%^,~:-=?+/", ch, 1, true) ~= nil)) then
        self.dolbrace_state = DOLBRACESTATE_WORD
      end
    end
    if pass_next then
      pass_next = false
      ;(function() table.insert(chars, ch); return chars end)()
      was_dollar = ch == "$"
      was_gtlt = ((string.find("<>", ch, 1, true) ~= nil))
      goto continue
    end
    if open_char == "'" then
      if ch == close_char then
        count = count - 1
        if count == 0 then
          break
        end
      end
      if ch == "\\" and (flags & MATCHEDPAIRFLAGS_ALLOWESC ~= 0) then
        pass_next = true
      end
      ;(function() table.insert(chars, ch); return chars end)()
      was_dollar = false
      was_gtlt = false
      goto continue
    end
    if ch == "\\" then
      if not self:at_end() and self:peek() == "\n" then
        self:advance()
        was_dollar = false
        was_gtlt = false
        goto continue
      end
      pass_next = true
      ;(function() table.insert(chars, ch); return chars end)()
      was_dollar = false
      was_gtlt = false
      goto continue
    end
    if ch == close_char then
      count = count - 1
      if count == 0 then
        break
      end
      ;(function() table.insert(chars, ch); return chars end)()
      was_dollar = false
      was_gtlt = ((string.find("<>", ch, 1, true) ~= nil))
      goto continue
    end
    if ch == open_char and open_char ~= close_char then
      if not ((flags & MATCHEDPAIRFLAGS_DOLBRACE ~= 0) and open_char == "{") then
        count = count + 1
      end
      ;(function() table.insert(chars, ch); return chars end)()
      was_dollar = false
      was_gtlt = ((string.find("<>", ch, 1, true) ~= nil))
      goto continue
    end
    if (((string.find("'\"`", ch, 1, true) ~= nil))) and open_char ~= close_char then
      if ch == "'" then
        ;(function() table.insert(chars, ch); return chars end)()
        quote_flags = (was_dollar and flags | MATCHEDPAIRFLAGS_ALLOWESC or flags)
        nested = self:parse_matched_pair("'", "'", quote_flags, false)
        ;(function() table.insert(chars, nested); return chars end)()
        ;(function() table.insert(chars, "'"); return chars end)()
        was_dollar = false
        was_gtlt = false
        goto continue
      elseif ch == "\"" then
        ;(function() table.insert(chars, ch); return chars end)()
        nested = self:parse_matched_pair("\"", "\"", flags | MATCHEDPAIRFLAGS_DQUOTE, false)
        ;(function() table.insert(chars, nested); return chars end)()
        ;(function() table.insert(chars, "\""); return chars end)()
        was_dollar = false
        was_gtlt = false
        goto continue
      elseif ch == "`" then
        ;(function() table.insert(chars, ch); return chars end)()
        nested = self:parse_matched_pair("`", "`", flags, false)
        ;(function() table.insert(chars, nested); return chars end)()
        ;(function() table.insert(chars, "`"); return chars end)()
        was_dollar = false
        was_gtlt = false
        goto continue
      end
    end
    if ch == "$" and not self:at_end() and ((flags & MATCHEDPAIRFLAGS_EXTGLOB) == 0) then
      next_ch = self:peek()
      if was_dollar then
        ;(function() table.insert(chars, ch); return chars end)()
        was_dollar = false
        was_gtlt = false
        goto continue
      end
      if next_ch == "{" then
        if (flags & MATCHEDPAIRFLAGS_ARITH ~= 0) then
          after_brace_pos = self.pos + 1
          if after_brace_pos >= self.length or not is_funsub_char(string.sub(self.source, after_brace_pos + 1, after_brace_pos + 1)) then
            ;(function() table.insert(chars, ch); return chars end)()
            was_dollar = true
            was_gtlt = false
            goto continue
          end
        end
        self.pos = self.pos - 1
        self:sync_to_parser()
        in_dquote = flags & MATCHEDPAIRFLAGS_DQUOTE ~= 0
        param_node, param_text = table.unpack(self.parser:parse_param_expansion(in_dquote))
        self:sync_from_parser()
        if (param_node ~= nil) then
          ;(function() table.insert(chars, param_text); return chars end)()
          was_dollar = false
          was_gtlt = false
        else
          ;(function() table.insert(chars, self:advance()); return chars end)()
          was_dollar = true
          was_gtlt = false
        end
        goto continue
      elseif next_ch == "(" then
        self.pos = self.pos - 1
        self:sync_to_parser()
        if self.pos + 2 < self.length and string.sub(self.source, self.pos + 2 + 1, self.pos + 2 + 1) == "(" then
          arith_node, arith_text = table.unpack(self.parser:parse_arithmetic_expansion())
          self:sync_from_parser()
          if (arith_node ~= nil) then
            ;(function() table.insert(chars, arith_text); return chars end)()
            was_dollar = false
            was_gtlt = false
          else
            self:sync_to_parser()
            cmd_node, cmd_text = table.unpack(self.parser:parse_command_substitution())
            self:sync_from_parser()
            if (cmd_node ~= nil) then
              ;(function() table.insert(chars, cmd_text); return chars end)()
              was_dollar = false
              was_gtlt = false
            else
              ;(function() table.insert(chars, self:advance()); return chars end)()
              ;(function() table.insert(chars, self:advance()); return chars end)()
              was_dollar = false
              was_gtlt = false
            end
          end
        else
          cmd_node, cmd_text = table.unpack(self.parser:parse_command_substitution())
          self:sync_from_parser()
          if (cmd_node ~= nil) then
            ;(function() table.insert(chars, cmd_text); return chars end)()
            was_dollar = false
            was_gtlt = false
          else
            ;(function() table.insert(chars, self:advance()); return chars end)()
            ;(function() table.insert(chars, self:advance()); return chars end)()
            was_dollar = false
            was_gtlt = false
          end
        end
        goto continue
      elseif next_ch == "[" then
        self.pos = self.pos - 1
        self:sync_to_parser()
        arith_node, arith_text = table.unpack(self.parser:parse_deprecated_arithmetic())
        self:sync_from_parser()
        if (arith_node ~= nil) then
          ;(function() table.insert(chars, arith_text); return chars end)()
          was_dollar = false
          was_gtlt = false
        else
          ;(function() table.insert(chars, self:advance()); return chars end)()
          was_dollar = true
          was_gtlt = false
        end
        goto continue
      end
    end
    if ch == "(" and was_gtlt and (flags & (MATCHEDPAIRFLAGS_DOLBRACE | MATCHEDPAIRFLAGS_ARRAYSUB) ~= 0) then
      direction = chars[#chars - 1 + 1]
      chars = _table_slice(chars, 1, #chars - 1)
      self.pos = self.pos - 1
      self:sync_to_parser()
      procsub_node, procsub_text = table.unpack(self.parser:parse_process_substitution())
      self:sync_from_parser()
      if (procsub_node ~= nil) then
        ;(function() table.insert(chars, procsub_text); return chars end)()
        was_dollar = false
        was_gtlt = false
      else
        ;(function() table.insert(chars, direction); return chars end)()
        ;(function() table.insert(chars, self:advance()); return chars end)()
        was_dollar = false
        was_gtlt = false
      end
      goto continue
    end
    ;(function() table.insert(chars, ch); return chars end)()
    was_dollar = ch == "$"
    was_gtlt = ((string.find("<>", ch, 1, true) ~= nil))
    ::continue::
  end
  return table.concat(chars, "")
end

function Lexer:collect_param_argument(flags, was_dollar)
  return self:parse_matched_pair("{", "}", flags | MATCHEDPAIRFLAGS_DOLBRACE, was_dollar)
end

function Lexer:read_word_internal(ctx, at_command_start, in_array_literal, in_assign_builtin)
  local ansi_result0, ansi_result1, array_result0, array_result1, bracket_depth, bracket_start_pos, c, ch, chars, cmdsub_result0, cmdsub_result1, content, for_regex, handle_line_continuation, in_single_in_dquote, is_array_assign, locale_result0, locale_result1, locale_result2, next_c, next_ch, paren_depth, parts, prev_char, procsub_result0, procsub_result1, saw_newline, seen_equals, start, track_newline
  start = self.pos
  chars = {}
  parts = {}
  bracket_depth = 0
  bracket_start_pos = -1
  seen_equals = false
  paren_depth = 0
  while not self:at_end() do
    ch = self:peek()
    if ctx == WORD_CTX_REGEX then
      if ch == "\\" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "\n" then
        self:advance()
        self:advance()
        goto continue
      end
    end
    if ctx ~= WORD_CTX_NORMAL and self:is_word_terminator(ctx, ch, bracket_depth, paren_depth) then
      break
    end
    if ctx == WORD_CTX_NORMAL and ch == "[" then
      if bracket_depth > 0 then
        bracket_depth = bracket_depth + 1
        ;(function() table.insert(chars, self:advance()); return chars end)()
        goto continue
      end
      if (#(chars) > 0) and at_command_start and not seen_equals and is_array_assignment_prefix(chars) then
        prev_char = chars[#chars - 1 + 1]
        if (string.match(prev_char, '^%w+$') ~= nil) or prev_char == "_" then
          bracket_start_pos = self.pos
          bracket_depth = bracket_depth + 1
          ;(function() table.insert(chars, self:advance()); return chars end)()
          goto continue
        end
      end
      if not (#(chars) > 0) and not seen_equals and in_array_literal then
        bracket_start_pos = self.pos
        bracket_depth = bracket_depth + 1
        ;(function() table.insert(chars, self:advance()); return chars end)()
        goto continue
      end
    end
    if ctx == WORD_CTX_NORMAL and ch == "]" and bracket_depth > 0 then
      bracket_depth = bracket_depth - 1
      ;(function() table.insert(chars, self:advance()); return chars end)()
      goto continue
    end
    if ctx == WORD_CTX_NORMAL and ch == "=" and bracket_depth == 0 then
      seen_equals = true
    end
    if ctx == WORD_CTX_REGEX and ch == "(" then
      paren_depth = paren_depth + 1
      ;(function() table.insert(chars, self:advance()); return chars end)()
      goto continue
    end
    if ctx == WORD_CTX_REGEX and ch == ")" then
      if paren_depth > 0 then
        paren_depth = paren_depth - 1
        ;(function() table.insert(chars, self:advance()); return chars end)()
        goto continue
      end
      break
    end
    if (ctx == WORD_CTX_COND or ctx == WORD_CTX_REGEX) and ch == "[" then
      for_regex = ctx == WORD_CTX_REGEX
      if self:read_bracket_expression(chars, parts, for_regex, paren_depth) then
        goto continue
      end
      ;(function() table.insert(chars, self:advance()); return chars end)()
      goto continue
    end
    if ctx == WORD_CTX_COND and ch == "(" then
      if self.extglob and (#(chars) > 0) and is_extglob_prefix(chars[#chars - 1 + 1]) then
        ;(function() table.insert(chars, self:advance()); return chars end)()
        content = self:parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false)
        ;(function() table.insert(chars, content); return chars end)()
        ;(function() table.insert(chars, ")"); return chars end)()
        goto continue
      else
        break
      end
    end
    if ctx == WORD_CTX_REGEX and is_whitespace(ch) and paren_depth > 0 then
      ;(function() table.insert(chars, self:advance()); return chars end)()
      goto continue
    end
    if ch == "'" then
      self:advance()
      track_newline = ctx == WORD_CTX_NORMAL
      content, saw_newline = table.unpack(self:read_single_quote(start))
      ;(function() table.insert(chars, content); return chars end)()
      if track_newline and saw_newline and (self.parser ~= nil) then
        self.parser.saw_newline_in_single_quote = true
      end
      goto continue
    end
    if ch == "\"" then
      self:advance()
      if ctx == WORD_CTX_NORMAL then
        ;(function() table.insert(chars, "\""); return chars end)()
        in_single_in_dquote = false
        while not self:at_end() and (in_single_in_dquote or self:peek() ~= "\"") do
          c = self:peek()
          if in_single_in_dquote then
            ;(function() table.insert(chars, self:advance()); return chars end)()
            if c == "'" then
              in_single_in_dquote = false
            end
            goto continue
          end
          if c == "\\" and self.pos + 1 < self.length then
            next_c = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
            if next_c == "\n" then
              self:advance()
              self:advance()
            else
              ;(function() table.insert(chars, self:advance()); return chars end)()
              ;(function() table.insert(chars, self:advance()); return chars end)()
            end
          elseif c == "$" then
            self:sync_to_parser()
            if not self.parser:parse_dollar_expansion(chars, parts, true) then
              self:sync_from_parser()
              ;(function() table.insert(chars, self:advance()); return chars end)()
            else
              self:sync_from_parser()
            end
          elseif c == "`" then
            self:sync_to_parser()
            cmdsub_result0, cmdsub_result1 = table.unpack(self.parser:parse_backtick_substitution())
            self:sync_from_parser()
            if (cmdsub_result0 ~= nil) then
              ;(function() table.insert(parts, cmdsub_result0); return parts end)()
              ;(function() table.insert(chars, cmdsub_result1); return chars end)()
            else
              ;(function() table.insert(chars, self:advance()); return chars end)()
            end
          else
            ;(function() table.insert(chars, self:advance()); return chars end)()
          end
          ::continue::
        end
        if self:at_end() then
          error({ParseError = true, message = "Unterminated double quote", pos = start})
        end
        ;(function() table.insert(chars, self:advance()); return chars end)()
      else
        handle_line_continuation = ctx == WORD_CTX_COND
        self:sync_to_parser()
        self.parser:scan_double_quote(chars, parts, start, handle_line_continuation)
        self:sync_from_parser()
      end
      goto continue
    end
    if ch == "\\" and self.pos + 1 < self.length then
      next_ch = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
      if ctx ~= WORD_CTX_REGEX and next_ch == "\n" then
        self:advance()
        self:advance()
      else
        ;(function() table.insert(chars, self:advance()); return chars end)()
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      goto continue
    end
    if ctx ~= WORD_CTX_REGEX and ch == "$" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "'" then
      ansi_result0, ansi_result1 = table.unpack(self:read_ansi_c_quote())
      if (ansi_result0 ~= nil) then
        ;(function() table.insert(parts, ansi_result0); return parts end)()
        ;(function() table.insert(chars, ansi_result1); return chars end)()
      else
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      goto continue
    end
    if ctx ~= WORD_CTX_REGEX and ch == "$" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "\"" then
      locale_result0, locale_result1, locale_result2 = table.unpack(self:read_locale_string())
      if (locale_result0 ~= nil) then
        ;(function() table.insert(parts, locale_result0); return parts end)()
        ;(function() for _, v in ipairs(locale_result2) do table.insert(parts, v) end; return parts end)()
        ;(function() table.insert(chars, locale_result1); return chars end)()
      else
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      goto continue
    end
    if ch == "$" then
      self:sync_to_parser()
      if not self.parser:parse_dollar_expansion(chars, parts, false) then
        self:sync_from_parser()
        ;(function() table.insert(chars, self:advance()); return chars end)()
      else
        self:sync_from_parser()
        if self.extglob and ctx == WORD_CTX_NORMAL and (#(chars) > 0) and #chars[#chars - 1 + 1] == 2 and string.sub(chars[#chars - 1 + 1], 0 + 1, 0 + 1) == "$" and (((string.find("?*@", string.sub(chars[#chars - 1 + 1], 1 + 1, 1 + 1), 1, true) ~= nil))) and not self:at_end() and self:peek() == "(" then
          ;(function() table.insert(chars, self:advance()); return chars end)()
          content = self:parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false)
          ;(function() table.insert(chars, content); return chars end)()
          ;(function() table.insert(chars, ")"); return chars end)()
        end
      end
      goto continue
    end
    if ctx ~= WORD_CTX_REGEX and ch == "`" then
      self:sync_to_parser()
      cmdsub_result0, cmdsub_result1 = table.unpack(self.parser:parse_backtick_substitution())
      self:sync_from_parser()
      if (cmdsub_result0 ~= nil) then
        ;(function() table.insert(parts, cmdsub_result0); return parts end)()
        ;(function() table.insert(chars, cmdsub_result1); return chars end)()
      else
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      goto continue
    end
    if ctx ~= WORD_CTX_REGEX and is_redirect_char(ch) and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
      self:sync_to_parser()
      procsub_result0, procsub_result1 = table.unpack(self.parser:parse_process_substitution())
      self:sync_from_parser()
      if (procsub_result0 ~= nil) then
        ;(function() table.insert(parts, procsub_result0); return parts end)()
        ;(function() table.insert(chars, procsub_result1); return chars end)()
      elseif (procsub_result1 ~= nil and #(procsub_result1) > 0) then
        ;(function() table.insert(chars, procsub_result1); return chars end)()
      else
        ;(function() table.insert(chars, self:advance()); return chars end)()
        if ctx == WORD_CTX_NORMAL then
          ;(function() table.insert(chars, self:advance()); return chars end)()
        end
      end
      goto continue
    end
    if ctx == WORD_CTX_NORMAL and ch == "(" and (#(chars) > 0) and bracket_depth == 0 then
      is_array_assign = false
      if #chars >= 3 and chars[#chars - 2 + 1] == "+" and chars[#chars - 1 + 1] == "=" then
        is_array_assign = is_array_assignment_prefix(_table_slice(chars, 1, #chars - 2))
      elseif chars[#chars - 1 + 1] == "=" and #chars >= 2 then
        is_array_assign = is_array_assignment_prefix(_table_slice(chars, 1, #chars - 1))
      end
      if is_array_assign and (at_command_start or in_assign_builtin) then
        self:sync_to_parser()
        array_result0, array_result1 = table.unpack(self.parser:parse_array_literal())
        self:sync_from_parser()
        if (array_result0 ~= nil) then
          ;(function() table.insert(parts, array_result0); return parts end)()
          ;(function() table.insert(chars, array_result1); return chars end)()
        else
          break
        end
        goto continue
      end
    end
    if self.extglob and ctx == WORD_CTX_NORMAL and is_extglob_prefix(ch) and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
      ;(function() table.insert(chars, self:advance()); return chars end)()
      ;(function() table.insert(chars, self:advance()); return chars end)()
      content = self:parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false)
      ;(function() table.insert(chars, content); return chars end)()
      ;(function() table.insert(chars, ")"); return chars end)()
      goto continue
    end
    if ctx == WORD_CTX_NORMAL and (self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN ~= 0) and self.eof_token ~= "" and ch == self.eof_token and bracket_depth == 0 then
      if not (#(chars) > 0) then
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
      break
    end
    if ctx == WORD_CTX_NORMAL and is_metachar(ch) and bracket_depth == 0 then
      break
    end
    ;(function() table.insert(chars, self:advance()); return chars end)()
    ::continue::
  end
  if bracket_depth > 0 and bracket_start_pos ~= -1 and self:at_end() then
    error({MatchedPairError = true, message = "unexpected EOF looking for `]'", pos = bracket_start_pos})
  end
  if not (#(chars) > 0) then
    return nil
  end
  if (#(parts) > 0) then
    return Word:new(table.concat(chars, ""), parts, "word")
  end
  return Word:new(table.concat(chars, ""), nil, "word")
end

function Lexer:read_word()
  local c, is_procsub, is_regex_paren, start, word
  start = self.pos
  if self.pos >= self.length then
    return nil
  end
  c = self:peek()
  if c == "" then
    return nil
  end
  is_procsub = (c == "<" or c == ">") and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "("
  is_regex_paren = self.word_context == WORD_CTX_REGEX and (c == "(" or c == ")")
  if self:is_metachar(c) and not is_procsub and not is_regex_paren then
    return nil
  end
  word = self:read_word_internal(self.word_context, self.at_command_start, self.in_array_literal, self.in_assign_builtin)
  if (word == nil) then
    return nil
  end
  return Token:new(TOKENTYPE_WORD, word.value, start, nil, word)
end

function Lexer:next_token()
  local tok
  if (self.token_cache ~= nil) then
    tok = self.token_cache
    self.token_cache = nil
    self.last_read_token = tok
    return tok
  end
  self:skip_blanks()
  if self:at_end() then
    tok = Token:new(TOKENTYPE_EOF, "", self.pos, nil, nil)
    self.last_read_token = tok
    return tok
  end
  if self.eof_token ~= "" and self:peek() == self.eof_token and ((self.parser_state & PARSERSTATEFLAGS_PST_CASEPAT) == 0) and ((self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN) == 0) then
    tok = Token:new(TOKENTYPE_EOF, "", self.pos, nil, nil)
    self.last_read_token = tok
    return tok
  end
  while self:skip_comment() do
    self:skip_blanks()
    if self:at_end() then
      tok = Token:new(TOKENTYPE_EOF, "", self.pos, nil, nil)
      self.last_read_token = tok
      return tok
    end
    if self.eof_token ~= "" and self:peek() == self.eof_token and ((self.parser_state & PARSERSTATEFLAGS_PST_CASEPAT) == 0) and ((self.parser_state & PARSERSTATEFLAGS_PST_EOFTOKEN) == 0) then
      tok = Token:new(TOKENTYPE_EOF, "", self.pos, nil, nil)
      self.last_read_token = tok
      return tok
    end
  end
  tok = self:read_operator()
  if (tok ~= nil) then
    self.last_read_token = tok
    return tok
  end
  tok = self:read_word()
  if (tok ~= nil) then
    self.last_read_token = tok
    return tok
  end
  tok = Token:new(TOKENTYPE_EOF, "", self.pos, nil, nil)
  self.last_read_token = tok
  return tok
end

function Lexer:peek_token()
  local saved_last
  if (self.token_cache == nil) then
    saved_last = self.last_read_token
    self.token_cache = self:next_token()
    self.last_read_token = saved_last
  end
  return self.token_cache
end

function Lexer:read_ansi_c_quote()
  local ch, content, content_chars, found_close, node, start, text
  if self:at_end() or self:peek() ~= "$" then
    return {nil, ""}
  end
  if self.pos + 1 >= self.length or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) ~= "'" then
    return {nil, ""}
  end
  start = self.pos
  self:advance()
  self:advance()
  content_chars = {}
  found_close = false
  while not self:at_end() do
    ch = self:peek()
    if ch == "'" then
      self:advance()
      found_close = true
      break
    elseif ch == "\\" then
      ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      if not self:at_end() then
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      end
    else
      ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
    end
  end
  if not found_close then
    error({MatchedPairError = true, message = "unexpected EOF while looking for matching `''", pos = start})
  end
  text = substring(self.source, start, self.pos)
  content = table.concat(content_chars, "")
  node = AnsiCQuote:new(content, "ansi-c")
  return {node, text}
end

function Lexer:sync_to_parser()
  if (self.parser ~= nil) then
    self.parser.pos = self.pos
  end
end

function Lexer:sync_from_parser()
  if (self.parser ~= nil) then
    self.pos = self.parser.pos
  end
end

function Lexer:read_locale_string()
  local arith_node, arith_text, ch, cmdsub_node, cmdsub_text, content, content_chars, found_close, inner_parts, next_ch, param_node, param_text, start, text
  if self:at_end() or self:peek() ~= "$" then
    return {nil, "", {}}
  end
  if self.pos + 1 >= self.length or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) ~= "\"" then
    return {nil, "", {}}
  end
  start = self.pos
  self:advance()
  self:advance()
  content_chars = {}
  inner_parts = {}
  found_close = false
  while not self:at_end() do
    ch = self:peek()
    if ch == "\"" then
      self:advance()
      found_close = true
      break
    elseif ch == "\\" and self.pos + 1 < self.length then
      next_ch = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
      if next_ch == "\n" then
        self:advance()
        self:advance()
      else
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      end
    elseif ch == "$" and self.pos + 2 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" and string.sub(self.source, self.pos + 2 + 1, self.pos + 2 + 1) == "(" then
      self:sync_to_parser()
      arith_node, arith_text = table.unpack(self.parser:parse_arithmetic_expansion())
      self:sync_from_parser()
      if (arith_node ~= nil) then
        ;(function() table.insert(inner_parts, arith_node); return inner_parts end)()
        ;(function() table.insert(content_chars, arith_text); return content_chars end)()
      else
        self:sync_to_parser()
        cmdsub_node, cmdsub_text = table.unpack(self.parser:parse_command_substitution())
        self:sync_from_parser()
        if (cmdsub_node ~= nil) then
          ;(function() table.insert(inner_parts, cmdsub_node); return inner_parts end)()
          ;(function() table.insert(content_chars, cmdsub_text); return content_chars end)()
        else
          ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
        end
      end
    elseif is_expansion_start(self.source, self.pos, "$(") then
      self:sync_to_parser()
      cmdsub_node, cmdsub_text = table.unpack(self.parser:parse_command_substitution())
      self:sync_from_parser()
      if (cmdsub_node ~= nil) then
        ;(function() table.insert(inner_parts, cmdsub_node); return inner_parts end)()
        ;(function() table.insert(content_chars, cmdsub_text); return content_chars end)()
      else
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      end
    elseif ch == "$" then
      self:sync_to_parser()
      param_node, param_text = table.unpack(self.parser:parse_param_expansion(false))
      self:sync_from_parser()
      if (param_node ~= nil) then
        ;(function() table.insert(inner_parts, param_node); return inner_parts end)()
        ;(function() table.insert(content_chars, param_text); return content_chars end)()
      else
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      end
    elseif ch == "`" then
      self:sync_to_parser()
      cmdsub_node, cmdsub_text = table.unpack(self.parser:parse_backtick_substitution())
      self:sync_from_parser()
      if (cmdsub_node ~= nil) then
        ;(function() table.insert(inner_parts, cmdsub_node); return inner_parts end)()
        ;(function() table.insert(content_chars, cmdsub_text); return content_chars end)()
      else
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      end
    else
      ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
    end
  end
  if not found_close then
    self.pos = start
    return {nil, "", {}}
  end
  content = table.concat(content_chars, "")
  text = "$\"" .. content .. "\""
  return {LocaleString:new(content, "locale"), text, inner_parts}
end

function Lexer:update_dolbrace_for_op(op, has_param)
  local first_char
  if self.dolbrace_state == DOLBRACESTATE_NONE then
    return
  end
  if op == "" or #op == 0 then
    return
  end
  first_char = string.sub(op, 0 + 1, 0 + 1)
  if self.dolbrace_state == DOLBRACESTATE_PARAM and has_param then
    if ((string.find("%#^,", first_char, 1, true) ~= nil)) then
      self.dolbrace_state = DOLBRACESTATE_QUOTE
      return
    end
    if first_char == "/" then
      self.dolbrace_state = DOLBRACESTATE_QUOTE2
      return
    end
  end
  if self.dolbrace_state == DOLBRACESTATE_PARAM then
    if ((string.find("#%^,~:-=?+/", first_char, 1, true) ~= nil)) then
      self.dolbrace_state = DOLBRACESTATE_OP
    end
  end
end

function Lexer:consume_param_operator()
  local ch, next_ch
  if self:at_end() then
    return ""
  end
  ch = self:peek()
  if ch == ":" then
    self:advance()
    if self:at_end() then
      return ":"
    end
    next_ch = self:peek()
    if is_simple_param_op(next_ch) then
      self:advance()
      return ":" .. next_ch
    end
    return ":"
  end
  if is_simple_param_op(ch) then
    self:advance()
    return ch
  end
  if ch == "#" then
    self:advance()
    if not self:at_end() and self:peek() == "#" then
      self:advance()
      return "##"
    end
    return "#"
  end
  if ch == "%" then
    self:advance()
    if not self:at_end() and self:peek() == "%" then
      self:advance()
      return "%%"
    end
    return "%"
  end
  if ch == "/" then
    self:advance()
    if not self:at_end() then
      next_ch = self:peek()
      if next_ch == "/" then
        self:advance()
        return "//"
      elseif next_ch == "#" then
        self:advance()
        return "/#"
      elseif next_ch == "%" then
        self:advance()
        return "/%"
      end
    end
    return "/"
  end
  if ch == "^" then
    self:advance()
    if not self:at_end() and self:peek() == "^" then
      self:advance()
      return "^^"
    end
    return "^"
  end
  if ch == "," then
    self:advance()
    if not self:at_end() and self:peek() == "," then
      self:advance()
      return ",,"
    end
    return ","
  end
  if ch == "@" then
    self:advance()
    return "@"
  end
  return ""
end

function Lexer:param_subscript_has_close(start_pos)
  local c, depth, i, quote
  depth = 1
  i = start_pos + 1
  quote = new_quote_state()
  while i < self.length do
    c = string.sub(self.source, i + 1, i + 1)
    if quote.single then
      if c == "'" then
        quote.single = false
      end
      i = i + 1
      goto continue
    end
    if quote.double then
      if c == "\\" and i + 1 < self.length then
        i = i + 2
        goto continue
      end
      if c == "\"" then
        quote.double = false
      end
      i = i + 1
      goto continue
    end
    if c == "'" then
      quote.single = true
      i = i + 1
      goto continue
    end
    if c == "\"" then
      quote.double = true
      i = i + 1
      goto continue
    end
    if c == "\\" then
      i = i + 2
      goto continue
    end
    if c == "}" then
      return false
    end
    if c == "[" then
      depth = depth + 1
    elseif c == "]" then
      depth = depth - 1
      if depth == 0 then
        return true
      end
    end
    i = i + 1
    ::continue::
  end
  return false
end

function Lexer:consume_param_name()
  local c, ch, content, name_chars
  if self:at_end() then
    return ""
  end
  ch = self:peek()
  if is_special_param(ch) then
    if ch == "$" and self.pos + 1 < self.length and (((string.find("{'\"", string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1), 1, true) ~= nil))) then
      return ""
    end
    self:advance()
    return ch
  end
  if (string.match(ch, '^%d+$') ~= nil) then
    name_chars = {}
    while not self:at_end() and (string.match(self:peek(), '^%d+$') ~= nil) do
      ;(function() table.insert(name_chars, self:advance()); return name_chars end)()
    end
    return table.concat(name_chars, "")
  end
  if (string.match(ch, '^%a+$') ~= nil) or ch == "_" then
    name_chars = {}
    while not self:at_end() do
      c = self:peek()
      if (string.match(c, '^%w+$') ~= nil) or c == "_" then
        ;(function() table.insert(name_chars, self:advance()); return name_chars end)()
      elseif c == "[" then
        if not self:param_subscript_has_close(self.pos) then
          break
        end
        ;(function() table.insert(name_chars, self:advance()); return name_chars end)()
        content = self:parse_matched_pair("[", "]", MATCHEDPAIRFLAGS_ARRAYSUB, false)
        ;(function() table.insert(name_chars, content); return name_chars end)()
        ;(function() table.insert(name_chars, "]"); return name_chars end)()
        break
      else
        break
      end
    end
    if (#(name_chars) > 0) then
      return table.concat(name_chars, "")
    else
      return ""
    end
  end
  return ""
end

function Lexer:read_param_expansion(in_dquote)
  local c, ch, name, name_start, start, text
  if self:at_end() or self:peek() ~= "$" then
    return {nil, ""}
  end
  start = self.pos
  self:advance()
  if self:at_end() then
    self.pos = start
    return {nil, ""}
  end
  ch = self:peek()
  if ch == "{" then
    self:advance()
    return self:read_braced_param(start, in_dquote)
  end
  if is_special_param_unbraced(ch) or is_digit(ch) or ch == "#" then
    self:advance()
    text = substring(self.source, start, self.pos)
    return {ParamExpansion:new(ch, nil, nil, "param"), text}
  end
  if (string.match(ch, '^%a+$') ~= nil) or ch == "_" then
    name_start = self.pos
    while not self:at_end() do
      c = self:peek()
      if (string.match(c, '^%w+$') ~= nil) or c == "_" then
        self:advance()
      else
        break
      end
    end
    name = substring(self.source, name_start, self.pos)
    text = substring(self.source, start, self.pos)
    return {ParamExpansion:new(name, nil, nil, "param"), text}
  end
  self.pos = start
  return {nil, ""}
end

function Lexer:read_braced_param(start, in_dquote)
  local arg_, backtick_pos, bc, ch, content, dollar_count, e, flags, formatted, inner, next_c, op, param, param_ends_with_dollar, parsed, saved_dolbrace, sub_parser, suffix, text, trailing
  if self:at_end() then
    error({MatchedPairError = true, message = "unexpected EOF looking for `}'", pos = start})
  end
  saved_dolbrace = self.dolbrace_state
  self.dolbrace_state = DOLBRACESTATE_PARAM
  ch = self:peek()
  if is_funsub_char(ch) then
    self.dolbrace_state = saved_dolbrace
    return self:read_funsub(start)
  end
  if ch == "#" then
    self:advance()
    param = self:consume_param_name()
    if (param ~= nil and #(param) > 0) and not self:at_end() and self:peek() == "}" then
      self:advance()
      text = substring(self.source, start, self.pos)
      self.dolbrace_state = saved_dolbrace
      return {ParamLength:new(param, "param-len"), text}
    end
    self.pos = start + 2
  end
  if ch == "!" then
    self:advance()
    while not self:at_end() and is_whitespace_no_newline(self:peek()) do
      self:advance()
    end
    param = self:consume_param_name()
    if (param ~= nil and #(param) > 0) then
      while not self:at_end() and is_whitespace_no_newline(self:peek()) do
        self:advance()
      end
      if not self:at_end() and self:peek() == "}" then
        self:advance()
        text = substring(self.source, start, self.pos)
        self.dolbrace_state = saved_dolbrace
        return {ParamIndirect:new(param, nil, nil, "param-indirect"), text}
      end
      if not self:at_end() and is_at_or_star(self:peek()) then
        suffix = self:advance()
        trailing = self:parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false)
        text = substring(self.source, start, self.pos)
        self.dolbrace_state = saved_dolbrace
        return {ParamIndirect:new(param .. suffix .. trailing, nil, nil, "param-indirect"), text}
      end
      op = self:consume_param_operator()
      if op == "" and not self:at_end() and ((not (string.find("}\"'`", self:peek(), 1, true) ~= nil))) then
        op = self:advance()
      end
      if op ~= "" and ((not (string.find("\"'`", op, 1, true) ~= nil))) then
        arg_ = self:parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false)
        text = substring(self.source, start, self.pos)
        self.dolbrace_state = saved_dolbrace
        return {ParamIndirect:new(param, op, arg_, "param-indirect"), text}
      end
      if self:at_end() then
        self.dolbrace_state = saved_dolbrace
        error({MatchedPairError = true, message = "unexpected EOF looking for `}'", pos = start})
      end
      self.pos = start + 2
    else
      self.pos = start + 2
    end
  end
  param = self:consume_param_name()
  if not (param ~= nil and #(param) > 0) then
    if not self:at_end() and ((((string.find("-=+?", self:peek(), 1, true) ~= nil))) or self:peek() == ":" and self.pos + 1 < self.length and is_simple_param_op(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1))) then
      param = ""
    else
      content = self:parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false)
      text = "${" .. content .. "}"
      self.dolbrace_state = saved_dolbrace
      return {ParamExpansion:new(content, nil, nil, "param"), text}
    end
  end
  if self:at_end() then
    self.dolbrace_state = saved_dolbrace
    error({MatchedPairError = true, message = "unexpected EOF looking for `}'", pos = start})
  end
  if self:peek() == "}" then
    self:advance()
    text = substring(self.source, start, self.pos)
    self.dolbrace_state = saved_dolbrace
    return {ParamExpansion:new(param, nil, nil, "param"), text}
  end
  op = self:consume_param_operator()
  if op == "" then
    if not self:at_end() and self:peek() == "$" and self.pos + 1 < self.length and (string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "\"" or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "'") then
      dollar_count = 1 + count_consecutive_dollars_before(self.source, self.pos)
      if dollar_count % 2 == 1 then
        op = ""
      else
        op = self:advance()
      end
    elseif not self:at_end() and self:peek() == "`" then
      backtick_pos = self.pos
      self:advance()
      while not self:at_end() and self:peek() ~= "`" do
        bc = self:peek()
        if bc == "\\" and self.pos + 1 < self.length then
          next_c = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
          if is_escape_char_in_backtick(next_c) then
            self:advance()
          end
        end
        self:advance()
      end
      if self:at_end() then
        self.dolbrace_state = saved_dolbrace
        error({ParseError = true, message = "Unterminated backtick", pos = backtick_pos})
      end
      self:advance()
      op = "`"
    elseif not self:at_end() and self:peek() == "$" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "{" then
      op = ""
    elseif not self:at_end() and (self:peek() == "'" or self:peek() == "\"") then
      op = ""
    elseif not self:at_end() and self:peek() == "\\" then
      op = self:advance()
      if not self:at_end() then
        op = op .. self:advance()
      end
    else
      op = self:advance()
    end
  end
  self:update_dolbrace_for_op(op, #param > 0)
  local _ok, _err = pcall(function()
    flags = (in_dquote and MATCHEDPAIRFLAGS_DQUOTE or MATCHEDPAIRFLAGS_NONE)
    param_ends_with_dollar = param ~= "" and (string.sub(param, -#"$") == "$")
    arg_ = self:collect_param_argument(flags, param_ends_with_dollar)
  end)
  if not _ok then
    local e = _err
    self.dolbrace_state = saved_dolbrace
    error(e)
  end
  if (op == "<" or op == ">") and (string.sub(arg_, 1, #"(") == "(") and (string.sub(arg_, -#")") == ")") then
    inner = string.sub(arg_, (1) + 1, #arg_ - 1)
    local _ok, _err = pcall(function()
      sub_parser = new_parser(inner, true, self.parser.extglob)
      parsed = sub_parser:parse_list(true)
      if (parsed ~= nil) and sub_parser:at_end() then
        formatted = format_cmdsub_node(parsed, 0, true, false, true)
        arg_ = "(" .. formatted .. ")"
      end
    end)
    if not _ok then
      -- empty catch
    end
  end
  text = "${" .. param .. op .. arg_ .. "}"
  self.dolbrace_state = saved_dolbrace
  return {ParamExpansion:new(param, op, arg_, "param"), text}
end

function Lexer:read_funsub(start)
  return self.parser:parse_funsub(start)
end

Word = {}
Word.__index = Word

function Word:new(value, parts, kind)
  local self = setmetatable({}, Word)
  if value == nil then value = "" end
  self.value = value
  if parts == nil then parts = {} end
  self.parts = parts
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Word:to_sexp()
  local escaped, value
  value = self.value
  value = self:expand_all_ansi_c_quotes(value)
  value = self:strip_locale_string_dollars(value)
  value = self:normalize_array_whitespace(value)
  value = self:format_command_substitutions(value, false)
  value = self:normalize_param_expansion_newlines(value)
  value = self:strip_arith_line_continuations(value)
  value = self:double_ctlesc_smart(value)
  value = (string.gsub(value, "\u{007f}", "\u{0001}\u{007f}"))
  value = (string.gsub(value, "\\", "\\\\"))
  if (string.sub(value, -#"\\\\") == "\\\\") and not (string.sub(value, -#"\\\\\\\\") == "\\\\\\\\") then
    value = value .. "\\\\"
  end
  escaped = (string.gsub((string.gsub((string.gsub(value, "\"", "\\\"")), "\n", "\\n")), "\t", "\\t"))
  return "(word \"" .. escaped .. "\")"
end

function Word:append_with_ctlesc(result, byte_val)
  ;(function() table.insert(result, byte_val); return result end)()
end

function Word:double_ctlesc_smart(value)
  local bs_count, c, j, quote, result
  result = {}
  quote = new_quote_state()
  for _ = 1, #value do
    local c = string.sub(value, _, _)
    if c == "'" and not quote.double then
      quote.single = not quote.single
    elseif c == "\"" and not quote.single then
      quote.double = not quote.double
    end
    ;(function() table.insert(result, c); return result end)()
    if c == "\u{0001}" then
      if quote.double then
        bs_count = 0
        j = #result - 2
        while j > -1 do
          if result[j + 1] == "\\" then
            bs_count = bs_count + 1
          else
            break
          end
          j = j + -1
        end
        if bs_count % 2 == 0 then
          ;(function() table.insert(result, "\u{0001}"); return result end)()
        end
      else
        ;(function() table.insert(result, "\u{0001}"); return result end)()
      end
    end
  end
  return table.concat(result, "")
end

function Word:normalize_param_expansion_newlines(value)
  local c, ch, depth, had_leading_newline, i, quote, result
  result = {}
  i = 0
  quote = new_quote_state()
  while i < #value do
    c = string.sub(value, i + 1, i + 1)
    if c == "'" and not quote.double then
      quote.single = not quote.single
      ;(function() table.insert(result, c); return result end)()
      i = i + 1
    elseif c == "\"" and not quote.single then
      quote.double = not quote.double
      ;(function() table.insert(result, c); return result end)()
      i = i + 1
    elseif is_expansion_start(value, i, "${") and not quote.single then
      ;(function() table.insert(result, "$"); return result end)()
      ;(function() table.insert(result, "{"); return result end)()
      i = i + 2
      had_leading_newline = i < #value and string.sub(value, i + 1, i + 1) == "\n"
      if had_leading_newline then
        ;(function() table.insert(result, " "); return result end)()
        i = i + 1
      end
      depth = 1
      while i < #value and depth > 0 do
        ch = string.sub(value, i + 1, i + 1)
        if ch == "\\" and i + 1 < #value and not quote.single then
          if string.sub(value, i + 1 + 1, i + 1 + 1) == "\n" then
            i = i + 2
            goto continue
          end
          ;(function() table.insert(result, ch); return result end)()
          ;(function() table.insert(result, string.sub(value, i + 1 + 1, i + 1 + 1)); return result end)()
          i = i + 2
          goto continue
        end
        if ch == "'" and not quote.double then
          quote.single = not quote.single
        elseif ch == "\"" and not quote.single then
          quote.double = not quote.double
        elseif not quote:in_quotes() then
          if ch == "{" then
            depth = depth + 1
          elseif ch == "}" then
            depth = depth - 1
            if depth == 0 then
              if had_leading_newline then
                ;(function() table.insert(result, " "); return result end)()
              end
              ;(function() table.insert(result, ch); return result end)()
              i = i + 1
              break
            end
          end
        end
        ;(function() table.insert(result, ch); return result end)()
        i = i + 1
        ::continue::
      end
    else
      ;(function() table.insert(result, c); return result end)()
      i = i + 1
    end
  end
  return table.concat(result, "")
end

function Word:sh_single_quote(s)
  local c, result
  if not (s ~= nil and #(s) > 0) then
    return "''"
  end
  if s == "'" then
    return "\\'"
  end
  result = {"'"}
  for _ = 1, #s do
    local c = string.sub(s, _, _)
    if c == "'" then
      ;(function() table.insert(result, "'\\''"); return result end)()
    else
      ;(function() table.insert(result, c); return result end)()
    end
  end
  ;(function() table.insert(result, "'"); return result end)()
  return table.concat(result, "")
end

function Word:ansi_c_to_bytes(inner)
  local byte_val, c, codepoint, ctrl_char, ctrl_val, hex_str, i, j, result, simple, skip_extra
  result = {}
  i = 0
  while i < #inner do
    if string.sub(inner, i + 1, i + 1) == "\\" and i + 1 < #inner then
      c = string.sub(inner, i + 1 + 1, i + 1 + 1)
      simple = get_ansi_escape(c)
      if simple >= 0 then
        ;(function() table.insert(result, simple); return result end)()
        i = i + 2
      elseif c == "'" then
        ;(function() table.insert(result, 39); return result end)()
        i = i + 2
      elseif c == "x" then
        if i + 2 < #inner and string.sub(inner, i + 2 + 1, i + 2 + 1) == "{" then
          j = i + 3
          while j < #inner and is_hex_digit(string.sub(inner, j + 1, j + 1)) do
            j = j + 1
          end
          hex_str = substring(inner, i + 3, j)
          if j < #inner and string.sub(inner, j + 1, j + 1) == "}" then
            j = j + 1
          end
          if not (hex_str ~= nil and #(hex_str) > 0) then
            return result
          end
          byte_val = tonumber(hex_str, 16) & 255
          if byte_val == 0 then
            return result
          end
          self:append_with_ctlesc(result, byte_val)
          i = j
        else
          j = i + 2
          while j < #inner and j < i + 4 and is_hex_digit(string.sub(inner, j + 1, j + 1)) do
            j = j + 1
          end
          if j > i + 2 then
            byte_val = tonumber(substring(inner, i + 2, j), 16)
            if byte_val == 0 then
              return result
            end
            self:append_with_ctlesc(result, byte_val)
            i = j
          else
            ;(function() table.insert(result, string.byte(string.sub(string.sub(inner, i + 1, i + 1), 0 + 1, 0 + 1))); return result end)()
            i = i + 1
          end
        end
      elseif c == "u" then
        j = i + 2
        while j < #inner and j < i + 6 and is_hex_digit(string.sub(inner, j + 1, j + 1)) do
          j = j + 1
        end
        if j > i + 2 then
          codepoint = tonumber(substring(inner, i + 2, j), 16)
          if codepoint == 0 then
            return result
          end
          ;(function() for _, v in ipairs(({string.byte(utf8.char(codepoint), 1, -1)})) do table.insert(result, v) end; return result end)()
          i = j
        else
          ;(function() table.insert(result, string.byte(string.sub(string.sub(inner, i + 1, i + 1), 0 + 1, 0 + 1))); return result end)()
          i = i + 1
        end
      elseif c == "U" then
        j = i + 2
        while j < #inner and j < i + 10 and is_hex_digit(string.sub(inner, j + 1, j + 1)) do
          j = j + 1
        end
        if j > i + 2 then
          codepoint = tonumber(substring(inner, i + 2, j), 16)
          if codepoint == 0 then
            return result
          end
          ;(function() for _, v in ipairs(({string.byte(utf8.char(codepoint), 1, -1)})) do table.insert(result, v) end; return result end)()
          i = j
        else
          ;(function() table.insert(result, string.byte(string.sub(string.sub(inner, i + 1, i + 1), 0 + 1, 0 + 1))); return result end)()
          i = i + 1
        end
      elseif c == "c" then
        if i + 3 <= #inner then
          ctrl_char = string.sub(inner, i + 2 + 1, i + 2 + 1)
          skip_extra = 0
          if ctrl_char == "\\" and i + 4 <= #inner and string.sub(inner, i + 3 + 1, i + 3 + 1) == "\\" then
            skip_extra = 1
          end
          ctrl_val = string.byte(string.sub(ctrl_char, 0 + 1, 0 + 1)) & 31
          if ctrl_val == 0 then
            return result
          end
          self:append_with_ctlesc(result, ctrl_val)
          i = i + 3 + skip_extra
        else
          ;(function() table.insert(result, string.byte(string.sub(string.sub(inner, i + 1, i + 1), 0 + 1, 0 + 1))); return result end)()
          i = i + 1
        end
      elseif c == "0" then
        j = i + 2
        while j < #inner and j < i + 4 and is_octal_digit(string.sub(inner, j + 1, j + 1)) do
          j = j + 1
        end
        if j > i + 2 then
          byte_val = tonumber(substring(inner, i + 1, j), 8) & 255
          if byte_val == 0 then
            return result
          end
          self:append_with_ctlesc(result, byte_val)
          i = j
        else
          return result
        end
      elseif c >= "1" and c <= "7" then
        j = i + 1
        while j < #inner and j < i + 4 and is_octal_digit(string.sub(inner, j + 1, j + 1)) do
          j = j + 1
        end
        byte_val = tonumber(substring(inner, i + 1, j), 8) & 255
        if byte_val == 0 then
          return result
        end
        self:append_with_ctlesc(result, byte_val)
        i = j
      else
        ;(function() table.insert(result, 92); return result end)()
        ;(function() table.insert(result, string.byte(string.sub(c, 0 + 1, 0 + 1))); return result end)()
        i = i + 2
      end
    else
      ;(function() for _, v in ipairs(({string.byte(string.sub(inner, i + 1, i + 1), 1, -1)})) do table.insert(result, v) end; return result end)()
      i = i + 1
    end
  end
  return result
end

function Word:expand_ansi_c_escapes(value)
  local inner, literal_bytes, literal_str
  if not ((string.sub(value, 1, #"'") == "'") and (string.sub(value, -#"'") == "'")) then
    return value
  end
  inner = substring(value, 1, #value - 1)
  literal_bytes = self:ansi_c_to_bytes(inner)
  literal_str = _bytes_to_string(literal_bytes)
  return self:sh_single_quote(literal_str)
end

function Word:expand_all_ansi_c_quotes(value)
  local after_brace, ansi_str, brace_depth, c, ch, effective_in_dquote, expanded, first_char, i, in_backtick, in_pattern, inner, is_ansi_c, j, last_brace_idx, op, op_start, outer_in_dquote, quote, rest, result, result_str, var_name_len
  result = {}
  i = 0
  quote = new_quote_state()
  in_backtick = false
  brace_depth = 0
  while i < #value do
    ch = string.sub(value, i + 1, i + 1)
    if ch == "`" and not quote.single then
      in_backtick = not in_backtick
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
      goto continue
    end
    if in_backtick then
      if ch == "\\" and i + 1 < #value then
        ;(function() table.insert(result, ch); return result end)()
        ;(function() table.insert(result, string.sub(value, i + 1 + 1, i + 1 + 1)); return result end)()
        i = i + 2
      else
        ;(function() table.insert(result, ch); return result end)()
        i = i + 1
      end
      goto continue
    end
    if not quote.single then
      if is_expansion_start(value, i, "${") then
        brace_depth = brace_depth + 1
        quote:push()
        ;(function() table.insert(result, "${"); return result end)()
        i = i + 2
        goto continue
      elseif ch == "}" and brace_depth > 0 and not quote.double then
        brace_depth = brace_depth - 1
        ;(function() table.insert(result, ch); return result end)()
        quote:pop()
        i = i + 1
        goto continue
      end
    end
    effective_in_dquote = quote.double
    if ch == "'" and not effective_in_dquote then
      is_ansi_c = not quote.single and i > 0 and string.sub(value, i - 1 + 1, i - 1 + 1) == "$" and count_consecutive_dollars_before(value, i - 1) % 2 == 0
      if not is_ansi_c then
        quote.single = not quote.single
      end
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "\"" and not quote.single then
      quote.double = not quote.double
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "\\" and i + 1 < #value and not quote.single then
      ;(function() table.insert(result, ch); return result end)()
      ;(function() table.insert(result, string.sub(value, i + 1 + 1, i + 1 + 1)); return result end)()
      i = i + 2
    elseif starts_with_at(value, i, "$'") and not quote.single and not effective_in_dquote and count_consecutive_dollars_before(value, i) % 2 == 0 then
      j = i + 2
      while j < #value do
        if string.sub(value, j + 1, j + 1) == "\\" and j + 1 < #value then
          j = j + 2
        elseif string.sub(value, j + 1, j + 1) == "'" then
          j = j + 1
          break
        else
          j = j + 1
        end
      end
      ansi_str = substring(value, i, j)
      expanded = self:expand_ansi_c_escapes(substring(ansi_str, 1, #ansi_str))
      outer_in_dquote = quote:outer_double()
      if brace_depth > 0 and outer_in_dquote and (string.sub(expanded, 1, #"'") == "'") and (string.sub(expanded, -#"'") == "'") then
        inner = substring(expanded, 1, #expanded - 1)
        if _string_find(inner, "\u{0001}") == -1 then
          result_str = table.concat(result, "")
          in_pattern = false
          last_brace_idx = _string_rfind(result_str, "${")
          if last_brace_idx >= 0 then
            after_brace = string.sub(result_str, (last_brace_idx + 2) + 1, #result_str)
            var_name_len = 0
            if (after_brace ~= nil and #(after_brace) > 0) then
              if ((string.find("@*#?-$!0123456789_", string.sub(after_brace, 0 + 1, 0 + 1), 1, true) ~= nil)) then
                var_name_len = 1
              elseif (string.match(string.sub(after_brace, 0 + 1, 0 + 1), '^%a+$') ~= nil) or string.sub(after_brace, 0 + 1, 0 + 1) == "_" then
                while var_name_len < #after_brace do
                  c = string.sub(after_brace, var_name_len + 1, var_name_len + 1)
                  if not ((string.match(c, '^%w+$') ~= nil) or c == "_") then
                    break
                  end
                  var_name_len = var_name_len + 1
                end
              end
            end
            if var_name_len > 0 and var_name_len < #after_brace and ((not (string.find("#?-", string.sub(after_brace, 0 + 1, 0 + 1), 1, true) ~= nil))) then
              op_start = string.sub(after_brace, (var_name_len) + 1, #after_brace)
              if (string.sub(op_start, 1, #"@") == "@") and #op_start > 1 then
                op_start = string.sub(op_start, (1) + 1, #op_start)
              end
              for _, op in ipairs({"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"}) do
                if (string.sub(op_start, 1, #op) == op) then
                  in_pattern = true
                  break
                end
              end
              if not in_pattern and (op_start ~= nil and #(op_start) > 0) and ((not (string.find("%#/^,~:+-=?", string.sub(op_start, 0 + 1, 0 + 1), 1, true) ~= nil))) then
                for _, op in ipairs({"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"}) do
                  if ((string.find(op_start, op, 1, true) ~= nil)) then
                    in_pattern = true
                    break
                  end
                end
              end
            elseif var_name_len == 0 and #after_brace > 1 then
              first_char = string.sub(after_brace, 0 + 1, 0 + 1)
              if (not (string.find("%#/^,", first_char, 1, true) ~= nil)) then
                rest = string.sub(after_brace, (1) + 1, #after_brace)
                for _, op in ipairs({"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"}) do
                  if ((string.find(rest, op, 1, true) ~= nil)) then
                    in_pattern = true
                    break
                  end
                end
              end
            end
          end
          if not in_pattern then
            expanded = inner
          end
        end
      end
      ;(function() table.insert(result, expanded); return result end)()
      i = j
    else
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    end
    ::continue::
  end
  return table.concat(result, "")
end

function Word:strip_locale_string_dollars(value)
  local brace_depth, brace_quote, bracket_depth, bracket_in_double_quote, ch, dollar_count, i, quote, result
  result = {}
  i = 0
  brace_depth = 0
  bracket_depth = 0
  quote = new_quote_state()
  brace_quote = new_quote_state()
  bracket_in_double_quote = false
  while i < #value do
    ch = string.sub(value, i + 1, i + 1)
    if ch == "\\" and i + 1 < #value and not quote.single and not brace_quote.single then
      ;(function() table.insert(result, ch); return result end)()
      ;(function() table.insert(result, string.sub(value, i + 1 + 1, i + 1 + 1)); return result end)()
      i = i + 2
    elseif starts_with_at(value, i, "${") and not quote.single and not brace_quote.single and (i == 0 or string.sub(value, i - 1 + 1, i - 1 + 1) ~= "$") then
      brace_depth = brace_depth + 1
      brace_quote.double = false
      brace_quote.single = false
      ;(function() table.insert(result, "$"); return result end)()
      ;(function() table.insert(result, "{"); return result end)()
      i = i + 2
    elseif ch == "}" and brace_depth > 0 and not quote.single and not brace_quote.double and not brace_quote.single then
      brace_depth = brace_depth - 1
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "[" and brace_depth > 0 and not quote.single and not brace_quote.double then
      bracket_depth = bracket_depth + 1
      bracket_in_double_quote = false
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "]" and bracket_depth > 0 and not quote.single and not bracket_in_double_quote then
      bracket_depth = bracket_depth - 1
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "'" and not quote.double and brace_depth == 0 then
      quote.single = not quote.single
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "\"" and not quote.single and brace_depth == 0 then
      quote.double = not quote.double
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "\"" and not quote.single and bracket_depth > 0 then
      bracket_in_double_quote = not bracket_in_double_quote
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "\"" and not quote.single and not brace_quote.single and brace_depth > 0 then
      brace_quote.double = not brace_quote.double
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif ch == "'" and not quote.double and not brace_quote.double and brace_depth > 0 then
      brace_quote.single = not brace_quote.single
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    elseif starts_with_at(value, i, "$\"") and not quote.single and not brace_quote.single and (brace_depth > 0 or bracket_depth > 0 or not quote.double) and not brace_quote.double and not bracket_in_double_quote then
      dollar_count = 1 + count_consecutive_dollars_before(value, i)
      if dollar_count % 2 == 1 then
        ;(function() table.insert(result, "\""); return result end)()
        if bracket_depth > 0 then
          bracket_in_double_quote = true
        elseif brace_depth > 0 then
          brace_quote.double = true
        else
          quote.double = true
        end
        i = i + 2
      else
        ;(function() table.insert(result, ch); return result end)()
        i = i + 1
      end
    else
      ;(function() table.insert(result, ch); return result end)()
      i = i + 1
    end
  end
  return table.concat(result, "")
end

function Word:normalize_array_whitespace(value)
  local close_paren_pos, depth, i, inner, open_paren_pos, prefix, result, suffix
  i = 0
  if not (i < #value and ((string.match(string.sub(value, i + 1, i + 1), '^%a+$') ~= nil) or string.sub(value, i + 1, i + 1) == "_")) then
    return value
  end
  i = i + 1
  while i < #value and ((string.match(string.sub(value, i + 1, i + 1), '^%w+$') ~= nil) or string.sub(value, i + 1, i + 1) == "_") do
    i = i + 1
  end
  while i < #value and string.sub(value, i + 1, i + 1) == "[" do
    depth = 1
    i = i + 1
    while i < #value and depth > 0 do
      if string.sub(value, i + 1, i + 1) == "[" then
        depth = depth + 1
      elseif string.sub(value, i + 1, i + 1) == "]" then
        depth = depth - 1
      end
      i = i + 1
    end
    if depth ~= 0 then
      return value
    end
  end
  if i < #value and string.sub(value, i + 1, i + 1) == "+" then
    i = i + 1
  end
  if not (i + 1 < #value and string.sub(value, i + 1, i + 1) == "=" and string.sub(value, i + 1 + 1, i + 1 + 1) == "(") then
    return value
  end
  prefix = substring(value, 0, i + 1)
  open_paren_pos = i + 1
  if (string.sub(value, -#")") == ")") then
    close_paren_pos = #value - 1
  else
    close_paren_pos = self:find_matching_paren(value, open_paren_pos)
    if close_paren_pos < 0 then
      return value
    end
  end
  inner = substring(value, open_paren_pos + 1, close_paren_pos)
  suffix = substring(value, close_paren_pos + 1, #value)
  result = self:normalize_array_inner(inner)
  return prefix .. "(" .. result .. ")" .. suffix
end

function Word:find_matching_paren(value, open_pos)
  local ch, depth, i, quote
  if open_pos >= #value or string.sub(value, open_pos + 1, open_pos + 1) ~= "(" then
    return -1
  end
  i = open_pos + 1
  depth = 1
  quote = new_quote_state()
  while i < #value and depth > 0 do
    ch = string.sub(value, i + 1, i + 1)
    if ch == "\\" and i + 1 < #value and not quote.single then
      i = i + 2
      goto continue
    end
    if ch == "'" and not quote.double then
      quote.single = not quote.single
      i = i + 1
      goto continue
    end
    if ch == "\"" and not quote.single then
      quote.double = not quote.double
      i = i + 1
      goto continue
    end
    if quote.single or quote.double then
      i = i + 1
      goto continue
    end
    if ch == "#" then
      while i < #value and string.sub(value, i + 1, i + 1) ~= "\n" do
        i = i + 1
      end
      goto continue
    end
    if ch == "(" then
      depth = depth + 1
    elseif ch == ")" then
      depth = depth - 1
      if depth == 0 then
        return i
      end
    end
    i = i + 1
    ::continue::
  end
  return -1
end

function Word:normalize_array_inner(inner)
  local brace_depth, bracket_depth, ch, depth, dq_brace_depth, dq_content, i, in_whitespace, j, normalized
  normalized = {}
  i = 0
  in_whitespace = true
  brace_depth = 0
  bracket_depth = 0
  while i < #inner do
    ch = string.sub(inner, i + 1, i + 1)
    if is_whitespace(ch) then
      if not in_whitespace and (#(normalized) > 0) and brace_depth == 0 and bracket_depth == 0 then
        ;(function() table.insert(normalized, " "); return normalized end)()
        in_whitespace = true
      end
      if brace_depth > 0 or bracket_depth > 0 then
        ;(function() table.insert(normalized, ch); return normalized end)()
      end
      i = i + 1
    elseif ch == "'" then
      in_whitespace = false
      j = i + 1
      while j < #inner and string.sub(inner, j + 1, j + 1) ~= "'" do
        j = j + 1
      end
      ;(function() table.insert(normalized, substring(inner, i, j + 1)); return normalized end)()
      i = j + 1
    elseif ch == "\"" then
      in_whitespace = false
      j = i + 1
      dq_content = {"\""}
      dq_brace_depth = 0
      while j < #inner do
        if string.sub(inner, j + 1, j + 1) == "\\" and j + 1 < #inner then
          if string.sub(inner, j + 1 + 1, j + 1 + 1) == "\n" then
            j = j + 2
          else
            ;(function() table.insert(dq_content, string.sub(inner, j + 1, j + 1)); return dq_content end)()
            ;(function() table.insert(dq_content, string.sub(inner, j + 1 + 1, j + 1 + 1)); return dq_content end)()
            j = j + 2
          end
        elseif is_expansion_start(inner, j, "${") then
          ;(function() table.insert(dq_content, "${"); return dq_content end)()
          dq_brace_depth = dq_brace_depth + 1
          j = j + 2
        elseif string.sub(inner, j + 1, j + 1) == "}" and dq_brace_depth > 0 then
          ;(function() table.insert(dq_content, "}"); return dq_content end)()
          dq_brace_depth = dq_brace_depth - 1
          j = j + 1
        elseif string.sub(inner, j + 1, j + 1) == "\"" and dq_brace_depth == 0 then
          ;(function() table.insert(dq_content, "\""); return dq_content end)()
          j = j + 1
          break
        else
          ;(function() table.insert(dq_content, string.sub(inner, j + 1, j + 1)); return dq_content end)()
          j = j + 1
        end
      end
      ;(function() table.insert(normalized, table.concat(dq_content, "")); return normalized end)()
      i = j
    elseif ch == "\\" and i + 1 < #inner then
      if string.sub(inner, i + 1 + 1, i + 1 + 1) == "\n" then
        i = i + 2
      else
        in_whitespace = false
        ;(function() table.insert(normalized, substring(inner, i, i + 2)); return normalized end)()
        i = i + 2
      end
    elseif is_expansion_start(inner, i, "$((") then
      in_whitespace = false
      j = i + 3
      depth = 1
      while j < #inner and depth > 0 do
        if j + 1 < #inner and string.sub(inner, j + 1, j + 1) == "(" and string.sub(inner, j + 1 + 1, j + 1 + 1) == "(" then
          depth = depth + 1
          j = j + 2
        elseif j + 1 < #inner and string.sub(inner, j + 1, j + 1) == ")" and string.sub(inner, j + 1 + 1, j + 1 + 1) == ")" then
          depth = depth - 1
          j = j + 2
        else
          j = j + 1
        end
      end
      ;(function() table.insert(normalized, substring(inner, i, j)); return normalized end)()
      i = j
    elseif is_expansion_start(inner, i, "$(") then
      in_whitespace = false
      j = i + 2
      depth = 1
      while j < #inner and depth > 0 do
        if string.sub(inner, j + 1, j + 1) == "(" and j > 0 and string.sub(inner, j - 1 + 1, j - 1 + 1) == "$" then
          depth = depth + 1
        elseif string.sub(inner, j + 1, j + 1) == ")" then
          depth = depth - 1
        elseif string.sub(inner, j + 1, j + 1) == "'" then
          j = j + 1
          while j < #inner and string.sub(inner, j + 1, j + 1) ~= "'" do
            j = j + 1
          end
        elseif string.sub(inner, j + 1, j + 1) == "\"" then
          j = j + 1
          while j < #inner do
            if string.sub(inner, j + 1, j + 1) == "\\" and j + 1 < #inner then
              j = j + 2
              goto continue
            end
            if string.sub(inner, j + 1, j + 1) == "\"" then
              break
            end
            j = j + 1
            ::continue::
          end
        end
        j = j + 1
      end
      ;(function() table.insert(normalized, substring(inner, i, j)); return normalized end)()
      i = j
    elseif (ch == "<" or ch == ">") and i + 1 < #inner and string.sub(inner, i + 1 + 1, i + 1 + 1) == "(" then
      in_whitespace = false
      j = i + 2
      depth = 1
      while j < #inner and depth > 0 do
        if string.sub(inner, j + 1, j + 1) == "(" then
          depth = depth + 1
        elseif string.sub(inner, j + 1, j + 1) == ")" then
          depth = depth - 1
        elseif string.sub(inner, j + 1, j + 1) == "'" then
          j = j + 1
          while j < #inner and string.sub(inner, j + 1, j + 1) ~= "'" do
            j = j + 1
          end
        elseif string.sub(inner, j + 1, j + 1) == "\"" then
          j = j + 1
          while j < #inner do
            if string.sub(inner, j + 1, j + 1) == "\\" and j + 1 < #inner then
              j = j + 2
              goto continue
            end
            if string.sub(inner, j + 1, j + 1) == "\"" then
              break
            end
            j = j + 1
            ::continue::
          end
        end
        j = j + 1
      end
      ;(function() table.insert(normalized, substring(inner, i, j)); return normalized end)()
      i = j
    elseif is_expansion_start(inner, i, "${") then
      in_whitespace = false
      ;(function() table.insert(normalized, "${"); return normalized end)()
      brace_depth = brace_depth + 1
      i = i + 2
    elseif ch == "{" and brace_depth > 0 then
      ;(function() table.insert(normalized, ch); return normalized end)()
      brace_depth = brace_depth + 1
      i = i + 1
    elseif ch == "}" and brace_depth > 0 then
      ;(function() table.insert(normalized, ch); return normalized end)()
      brace_depth = brace_depth - 1
      i = i + 1
    elseif ch == "#" and brace_depth == 0 and in_whitespace then
      while i < #inner and string.sub(inner, i + 1, i + 1) ~= "\n" do
        i = i + 1
      end
    elseif ch == "[" then
      if in_whitespace or bracket_depth > 0 then
        bracket_depth = bracket_depth + 1
      end
      in_whitespace = false
      ;(function() table.insert(normalized, ch); return normalized end)()
      i = i + 1
    elseif ch == "]" and bracket_depth > 0 then
      ;(function() table.insert(normalized, ch); return normalized end)()
      bracket_depth = bracket_depth - 1
      i = i + 1
    else
      in_whitespace = false
      ;(function() table.insert(normalized, ch); return normalized end)()
      i = i + 1
    end
  end
  return (string.gsub(table.concat(normalized, ""), '[' .. " \t\n\r" .. ']+$', ''))
end

function Word:strip_arith_line_continuations(value)
  local arith_content, closing, content, depth, first_close_idx, i, j, num_backslashes, result, start
  result = {}
  i = 0
  while i < #value do
    if is_expansion_start(value, i, "$((") then
      start = i
      i = i + 3
      depth = 2
      arith_content = {}
      first_close_idx = -1
      while i < #value and depth > 0 do
        if string.sub(value, i + 1, i + 1) == "(" then
          ;(function() table.insert(arith_content, "("); return arith_content end)()
          depth = depth + 1
          i = i + 1
          if depth > 1 then
            first_close_idx = -1
          end
        elseif string.sub(value, i + 1, i + 1) == ")" then
          if depth == 2 then
            first_close_idx = #arith_content
          end
          depth = depth - 1
          if depth > 0 then
            ;(function() table.insert(arith_content, ")"); return arith_content end)()
          end
          i = i + 1
        elseif string.sub(value, i + 1, i + 1) == "\\" and i + 1 < #value and string.sub(value, i + 1 + 1, i + 1 + 1) == "\n" then
          num_backslashes = 0
          j = #arith_content - 1
          while j >= 0 and arith_content[j + 1] == "\n" do
            j = j - 1
          end
          while j >= 0 and arith_content[j + 1] == "\\" do
            num_backslashes = num_backslashes + 1
            j = j - 1
          end
          if num_backslashes % 2 == 1 then
            ;(function() table.insert(arith_content, "\\"); return arith_content end)()
            ;(function() table.insert(arith_content, "\n"); return arith_content end)()
            i = i + 2
          else
            i = i + 2
          end
          if depth == 1 then
            first_close_idx = -1
          end
        else
          ;(function() table.insert(arith_content, string.sub(value, i + 1, i + 1)); return arith_content end)()
          i = i + 1
          if depth == 1 then
            first_close_idx = -1
          end
        end
      end
      if depth == 0 or depth == 1 and first_close_idx ~= -1 then
        content = table.concat(arith_content, "")
        if first_close_idx ~= -1 then
          content = string.sub(content, 1, first_close_idx)
          closing = (depth == 0 and "))" or ")")
          ;(function() table.insert(result, "$((" .. content .. closing); return result end)()
        else
          ;(function() table.insert(result, "$((" .. content .. ")"); return result end)()
        end
      else
        ;(function() table.insert(result, substring(value, start, i)); return result end)()
      end
    else
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
    end
  end
  return table.concat(result, "")
end

function Word:collect_cmdsubs(node)
  local elem, p, result
  result = {}
  if (type(node) == 'table' and getmetatable(node) == CommandSubstitution) then
    local node = node
    ;(function() table.insert(result, node); return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == Array) then
    local node = node
    for _, elem in ipairs(node.elements) do
      for _, p in ipairs(elem.parts) do
        if (type(p) == 'table' and getmetatable(p) == CommandSubstitution) then
          local p = p
          ;(function() table.insert(result, p); return result end)()
        else
          ;(function() for _, v in ipairs(self:collect_cmdsubs(p)) do table.insert(result, v) end; return result end)()
        end
      end
    end
  elseif (type(node) == 'table' and getmetatable(node) == ArithmeticExpansion) then
    local node = node
    if (node.expression ~= nil) then
      ;(function() for _, v in ipairs(self:collect_cmdsubs(node.expression)) do table.insert(result, v) end; return result end)()
    end
  elseif (type(node) == 'table' and getmetatable(node) == ArithBinaryOp) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.left)) do table.insert(result, v) end; return result end)()
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.right)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithComma) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.left)) do table.insert(result, v) end; return result end)()
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.right)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithUnaryOp) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.operand)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithPreIncr) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.operand)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithPostIncr) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.operand)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithPreDecr) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.operand)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithPostDecr) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.operand)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithTernary) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.condition)) do table.insert(result, v) end; return result end)()
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.if_true)) do table.insert(result, v) end; return result end)()
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.if_false)) do table.insert(result, v) end; return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == ArithAssign) then
    local node = node
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.target)) do table.insert(result, v) end; return result end)()
    ;(function() for _, v in ipairs(self:collect_cmdsubs(node.value)) do table.insert(result, v) end; return result end)()
  end
  return result
end

function Word:collect_procsubs(node)
  local elem, p, result
  result = {}
  if (type(node) == 'table' and getmetatable(node) == ProcessSubstitution) then
    local node = node
    ;(function() table.insert(result, node); return result end)()
  elseif (type(node) == 'table' and getmetatable(node) == Array) then
    local node = node
    for _, elem in ipairs(node.elements) do
      for _, p in ipairs(elem.parts) do
        if (type(p) == 'table' and getmetatable(p) == ProcessSubstitution) then
          local p = p
          ;(function() table.insert(result, p); return result end)()
        else
          ;(function() for _, v in ipairs(self:collect_procsubs(p)) do table.insert(result, v) end; return result end)()
        end
      end
    end
  end
  return result
end

function Word:format_command_substitutions(value, in_arith)
  local arith_depth, arith_paren_depth, brace_quote, c, cmdsub_idx, cmdsub_node, cmdsub_parts, compact, deprecated_arith_depth, depth, direction, ends_with_newline, extglob_depth, final_output, formatted, formatted_inner, has_arith, has_brace_cmdsub, has_param_with_procsub_pattern, has_pipe, has_untracked_cmdsub, has_untracked_procsub, i, idx, inner, is_procsub, j, leading_ws, leading_ws_end, main_quote, node, normalized_ws, orig_inner, p, parsed, parser, prefix, procsub_idx, procsub_parts, raw_content, raw_stripped, result, scan_quote, spaced, stripped, suffix, terminator
  cmdsub_parts = {}
  procsub_parts = {}
  has_arith = false
  for _, p in ipairs(self.parts) do
    if (type(p) == 'table' and getmetatable(p) == CommandSubstitution) then
      local p = p
      ;(function() table.insert(cmdsub_parts, p); return cmdsub_parts end)()
    elseif (type(p) == 'table' and getmetatable(p) == ProcessSubstitution) then
      local p = p
      ;(function() table.insert(procsub_parts, p); return procsub_parts end)()
    elseif (type(p) == 'table' and getmetatable(p) == ArithmeticExpansion) then
      local p = p
      has_arith = true
    else
      ;(function() for _, v in ipairs(self:collect_cmdsubs(p)) do table.insert(cmdsub_parts, v) end; return cmdsub_parts end)()
      ;(function() for _, v in ipairs(self:collect_procsubs(p)) do table.insert(procsub_parts, v) end; return procsub_parts end)()
    end
  end
  has_brace_cmdsub = _string_find(value, "${ ") ~= -1 or _string_find(value, "${\t") ~= -1 or _string_find(value, "${\n") ~= -1 or _string_find(value, "${|") ~= -1
  has_untracked_cmdsub = false
  has_untracked_procsub = false
  idx = 0
  scan_quote = new_quote_state()
  while idx < #value do
    if string.sub(value, idx + 1, idx + 1) == "\"" then
      scan_quote.double = not scan_quote.double
      idx = idx + 1
    elseif string.sub(value, idx + 1, idx + 1) == "'" and not scan_quote.double then
      idx = idx + 1
      while idx < #value and string.sub(value, idx + 1, idx + 1) ~= "'" do
        idx = idx + 1
      end
      if idx < #value then
        idx = idx + 1
      end
    elseif starts_with_at(value, idx, "$(") and not starts_with_at(value, idx, "$((") and not is_backslash_escaped(value, idx) and not is_dollar_dollar_paren(value, idx) then
      has_untracked_cmdsub = true
      break
    elseif (starts_with_at(value, idx, "<(") or starts_with_at(value, idx, ">(")) and not scan_quote.double then
      if idx == 0 or not (string.match(string.sub(value, idx - 1 + 1, idx - 1 + 1), '^%w+$') ~= nil) and ((not (string.find("\"'", string.sub(value, idx - 1 + 1, idx - 1 + 1), 1, true) ~= nil))) then
        has_untracked_procsub = true
        break
      end
      idx = idx + 1
    else
      idx = idx + 1
    end
  end
  has_param_with_procsub_pattern = (((string.find(value, "${", 1, true) ~= nil))) and ((((string.find(value, "<(", 1, true) ~= nil))) or (((string.find(value, ">(", 1, true) ~= nil))))
  if not (#(cmdsub_parts) > 0) and not (#(procsub_parts) > 0) and not has_brace_cmdsub and not has_untracked_cmdsub and not has_untracked_procsub and not has_param_with_procsub_pattern then
    return value
  end
  result = {}
  i = 0
  cmdsub_idx = 0
  procsub_idx = 0
  main_quote = new_quote_state()
  extglob_depth = 0
  deprecated_arith_depth = 0
  arith_depth = 0
  arith_paren_depth = 0
  while i < #value do
    if i > 0 and is_extglob_prefix(string.sub(value, i - 1 + 1, i - 1 + 1)) and string.sub(value, i + 1, i + 1) == "(" and not is_backslash_escaped(value, i - 1) then
      extglob_depth = extglob_depth + 1
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
      goto continue
    end
    if string.sub(value, i + 1, i + 1) == ")" and extglob_depth > 0 then
      extglob_depth = extglob_depth - 1
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
      goto continue
    end
    if starts_with_at(value, i, "$[") and not is_backslash_escaped(value, i) then
      deprecated_arith_depth = deprecated_arith_depth + 1
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
      goto continue
    end
    if string.sub(value, i + 1, i + 1) == "]" and deprecated_arith_depth > 0 then
      deprecated_arith_depth = deprecated_arith_depth - 1
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
      goto continue
    end
    if is_expansion_start(value, i, "$((") and not is_backslash_escaped(value, i) and has_arith then
      arith_depth = arith_depth + 1
      arith_paren_depth = arith_paren_depth + 2
      ;(function() table.insert(result, "$(("); return result end)()
      i = i + 3
      goto continue
    end
    if arith_depth > 0 and arith_paren_depth == 2 and starts_with_at(value, i, "))") then
      arith_depth = arith_depth - 1
      arith_paren_depth = arith_paren_depth - 2
      ;(function() table.insert(result, "))"); return result end)()
      i = i + 2
      goto continue
    end
    if arith_depth > 0 then
      if string.sub(value, i + 1, i + 1) == "(" then
        arith_paren_depth = arith_paren_depth + 1
        ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
        i = i + 1
        goto continue
      elseif string.sub(value, i + 1, i + 1) == ")" then
        arith_paren_depth = arith_paren_depth - 1
        ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
        i = i + 1
        goto continue
      end
    end
    if is_expansion_start(value, i, "$((") and not has_arith then
      j = find_cmdsub_end(value, i + 2)
      ;(function() table.insert(result, substring(value, i, j)); return result end)()
      if cmdsub_idx < #cmdsub_parts then
        cmdsub_idx = cmdsub_idx + 1
      end
      i = j
      goto continue
    end
    if starts_with_at(value, i, "$(") and not starts_with_at(value, i, "$((") and not is_backslash_escaped(value, i) and not is_dollar_dollar_paren(value, i) then
      j = find_cmdsub_end(value, i + 2)
      if extglob_depth > 0 then
        ;(function() table.insert(result, substring(value, i, j)); return result end)()
        if cmdsub_idx < #cmdsub_parts then
          cmdsub_idx = cmdsub_idx + 1
        end
        i = j
        goto continue
      end
      inner = substring(value, i + 2, j - 1)
      if cmdsub_idx < #cmdsub_parts then
        node = cmdsub_parts[cmdsub_idx + 1]
        formatted = format_cmdsub_node(node.command, 0, false, false, false)
        cmdsub_idx = cmdsub_idx + 1
      else
        local _ok, _err = pcall(function()
          parser = new_parser(inner, false, false)
          parsed = parser:parse_list(true)
          formatted = ((parsed ~= nil) and format_cmdsub_node(parsed, 0, false, false, false) or "")
        end)
        if not _ok then
          formatted = inner
        end
      end
      if (string.sub(formatted, 1, #"(") == "(") then
        ;(function() table.insert(result, "$( " .. formatted .. ")"); return result end)()
      else
        ;(function() table.insert(result, "$(" .. formatted .. ")"); return result end)()
      end
      i = j
    elseif string.sub(value, i + 1, i + 1) == "`" and cmdsub_idx < #cmdsub_parts then
      j = i + 1
      while j < #value do
        if string.sub(value, j + 1, j + 1) == "\\" and j + 1 < #value then
          j = j + 2
          goto continue
        end
        if string.sub(value, j + 1, j + 1) == "`" then
          j = j + 1
          break
        end
        j = j + 1
        ::continue::
      end
      ;(function() table.insert(result, substring(value, i, j)); return result end)()
      cmdsub_idx = cmdsub_idx + 1
      i = j
    elseif is_expansion_start(value, i, "${") and i + 2 < #value and is_funsub_char(string.sub(value, i + 2 + 1, i + 2 + 1)) and not is_backslash_escaped(value, i) then
      j = find_funsub_end(value, i + 2)
      cmdsub_node = (cmdsub_idx < #cmdsub_parts and cmdsub_parts[cmdsub_idx + 1] or nil)
      if (type(cmdsub_node) == 'table' and getmetatable(cmdsub_node) == CommandSubstitution) and cmdsub_node.brace then
        node = cmdsub_node
        formatted = format_cmdsub_node(node.command, 0, false, false, false)
        has_pipe = string.sub(value, i + 2 + 1, i + 2 + 1) == "|"
        prefix = (has_pipe and "${|" or "${ ")
        orig_inner = substring(value, i + 2, j - 1)
        ends_with_newline = (string.sub(orig_inner, -#"\n") == "\n")
        if not (formatted ~= nil and #(formatted) > 0) or (string.match(formatted, '^%s+$') ~= nil) then
          suffix = "}"
        elseif (string.sub(formatted, -#"&") == "&") or (string.sub(formatted, -#"& ") == "& ") then
          suffix = ((string.sub(formatted, -#"&") == "&") and " }" or "}")
        elseif ends_with_newline then
          suffix = "\n }"
        else
          suffix = "; }"
        end
        ;(function() table.insert(result, prefix .. formatted .. suffix); return result end)()
        cmdsub_idx = cmdsub_idx + 1
      else
        ;(function() table.insert(result, substring(value, i, j)); return result end)()
      end
      i = j
    elseif (starts_with_at(value, i, ">(") or starts_with_at(value, i, "<(")) and not main_quote.double and deprecated_arith_depth == 0 and arith_depth == 0 then
      is_procsub = i == 0 or not (string.match(string.sub(value, i - 1 + 1, i - 1 + 1), '^%w+$') ~= nil) and ((not (string.find("\"'", string.sub(value, i - 1 + 1, i - 1 + 1), 1, true) ~= nil)))
      if extglob_depth > 0 then
        j = find_cmdsub_end(value, i + 2)
        ;(function() table.insert(result, substring(value, i, j)); return result end)()
        if procsub_idx < #procsub_parts then
          procsub_idx = procsub_idx + 1
        end
        i = j
        goto continue
      end
      if procsub_idx < #procsub_parts then
        direction = string.sub(value, i + 1, i + 1)
        j = find_cmdsub_end(value, i + 2)
        node = procsub_parts[procsub_idx + 1]
        compact = starts_with_subshell(node.command)
        formatted = format_cmdsub_node(node.command, 0, true, compact, true)
        raw_content = substring(value, i + 2, j - 1)
        if node.command.kind == "subshell" then
          leading_ws_end = 0
          while leading_ws_end < #raw_content and (((string.find(" \t\n", string.sub(raw_content, leading_ws_end + 1, leading_ws_end + 1), 1, true) ~= nil))) do
            leading_ws_end = leading_ws_end + 1
          end
          leading_ws = string.sub(raw_content, 1, leading_ws_end)
          stripped = string.sub(raw_content, (leading_ws_end) + 1, #raw_content)
          if (string.sub(stripped, 1, #"(") == "(") then
            if (leading_ws ~= nil and #(leading_ws) > 0) then
              normalized_ws = (string.gsub((string.gsub(leading_ws, "\n", " ")), "\t", " "))
              spaced = format_cmdsub_node(node.command, 0, false, false, false)
              ;(function() table.insert(result, direction .. "(" .. normalized_ws .. spaced .. ")"); return result end)()
            else
              raw_content = (string.gsub(raw_content, "\\\n", ""))
              ;(function() table.insert(result, direction .. "(" .. raw_content .. ")"); return result end)()
            end
            procsub_idx = procsub_idx + 1
            i = j
            goto continue
          end
        end
        raw_content = substring(value, i + 2, j - 1)
        raw_stripped = (string.gsub(raw_content, "\\\n", ""))
        if starts_with_subshell(node.command) and formatted ~= raw_stripped then
          ;(function() table.insert(result, direction .. "(" .. raw_stripped .. ")"); return result end)()
        else
          final_output = direction .. "(" .. formatted .. ")"
          ;(function() table.insert(result, final_output); return result end)()
        end
        procsub_idx = procsub_idx + 1
        i = j
      elseif is_procsub and (#self.parts ~= 0) then
        direction = string.sub(value, i + 1, i + 1)
        j = find_cmdsub_end(value, i + 2)
        if j > #value or j > 0 and j <= #value and string.sub(value, j - 1 + 1, j - 1 + 1) ~= ")" then
          ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
          i = i + 1
          goto continue
        end
        inner = substring(value, i + 2, j - 1)
        local _ok, _err = pcall(function()
          parser = new_parser(inner, false, false)
          parsed = parser:parse_list(true)
          if (parsed ~= nil) and parser.pos == #inner and ((not (string.find(inner, "\n", 1, true) ~= nil))) then
            compact = starts_with_subshell(parsed)
            formatted = format_cmdsub_node(parsed, 0, true, compact, true)
          else
            formatted = inner
          end
        end)
        if not _ok then
          formatted = inner
        end
        ;(function() table.insert(result, direction .. "(" .. formatted .. ")"); return result end)()
        i = j
      elseif is_procsub then
        direction = string.sub(value, i + 1, i + 1)
        j = find_cmdsub_end(value, i + 2)
        if j > #value or j > 0 and j <= #value and string.sub(value, j - 1 + 1, j - 1 + 1) ~= ")" then
          ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
          i = i + 1
          goto continue
        end
        inner = substring(value, i + 2, j - 1)
        if in_arith then
          ;(function() table.insert(result, direction .. "(" .. inner .. ")"); return result end)()
        elseif ((string.gsub((string.gsub(inner, '^[' .. " \t\n\r" .. ']+', '')), '[' .. " \t\n\r" .. ']+$', '')) ~= nil and #((string.gsub((string.gsub(inner, '^[' .. " \t\n\r" .. ']+', '')), '[' .. " \t\n\r" .. ']+$', ''))) > 0) then
          stripped = (string.gsub(inner, '^[' .. " \t" .. ']+', ''))
          ;(function() table.insert(result, direction .. "(" .. stripped .. ")"); return result end)()
        else
          ;(function() table.insert(result, direction .. "(" .. inner .. ")"); return result end)()
        end
        i = j
      else
        ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
        i = i + 1
      end
    elseif (is_expansion_start(value, i, "${ ") or is_expansion_start(value, i, "${\t") or is_expansion_start(value, i, "${\n") or is_expansion_start(value, i, "${|")) and not is_backslash_escaped(value, i) then
      prefix = (string.gsub((string.gsub(substring(value, i, i + 3), "\t", " ")), "\n", " "))
      j = i + 3
      depth = 1
      while j < #value and depth > 0 do
        if string.sub(value, j + 1, j + 1) == "{" then
          depth = depth + 1
        elseif string.sub(value, j + 1, j + 1) == "}" then
          depth = depth - 1
        end
        j = j + 1
      end
      inner = substring(value, i + 2, j - 1)
      if (string.gsub((string.gsub(inner, '^[' .. " \t\n\r" .. ']+', '')), '[' .. " \t\n\r" .. ']+$', '')) == "" then
        ;(function() table.insert(result, "${ }"); return result end)()
      else
        local _ok, _err = pcall(function()
          parser = new_parser((string.gsub(inner, '^[' .. " \t\n|" .. ']+', '')), false, false)
          parsed = parser:parse_list(true)
          if (parsed ~= nil) then
            formatted = format_cmdsub_node(parsed, 0, false, false, false)
            formatted = (string.gsub(formatted, '[' .. ";" .. ']+$', ''))
            if (string.sub((string.gsub(inner, '[' .. " \t" .. ']+$', '')), -#"\n") == "\n") then
              terminator = "\n }"
            elseif (string.sub(formatted, -#" &") == " &") then
              terminator = " }"
            else
              terminator = "; }"
            end
            ;(function() table.insert(result, prefix .. formatted .. terminator); return result end)()
          else
            ;(function() table.insert(result, "${ }"); return result end)()
          end
        end)
        if not _ok then
          ;(function() table.insert(result, substring(value, i, j)); return result end)()
        end
      end
      i = j
    elseif is_expansion_start(value, i, "${") and not is_backslash_escaped(value, i) then
      j = i + 2
      depth = 1
      brace_quote = new_quote_state()
      while j < #value and depth > 0 do
        c = string.sub(value, j + 1, j + 1)
        if c == "\\" and j + 1 < #value and not brace_quote.single then
          j = j + 2
          goto continue
        end
        if c == "'" and not brace_quote.double then
          brace_quote.single = not brace_quote.single
        elseif c == "\"" and not brace_quote.single then
          brace_quote.double = not brace_quote.double
        elseif not brace_quote:in_quotes() then
          if is_expansion_start(value, j, "$(") and not starts_with_at(value, j, "$((") then
            j = find_cmdsub_end(value, j + 2)
            goto continue
          end
          if c == "{" then
            depth = depth + 1
          elseif c == "}" then
            depth = depth - 1
          end
        end
        j = j + 1
        ::continue::
      end
      if depth > 0 then
        inner = substring(value, i + 2, j)
      else
        inner = substring(value, i + 2, j - 1)
      end
      formatted_inner = self:format_command_substitutions(inner, false)
      formatted_inner = self:normalize_extglob_whitespace(formatted_inner)
      if depth == 0 then
        ;(function() table.insert(result, "${" .. formatted_inner .. "}"); return result end)()
      else
        ;(function() table.insert(result, "${" .. formatted_inner); return result end)()
      end
      i = j
    elseif string.sub(value, i + 1, i + 1) == "\"" then
      main_quote.double = not main_quote.double
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
    elseif string.sub(value, i + 1, i + 1) == "'" and not main_quote.double then
      j = i + 1
      while j < #value and string.sub(value, j + 1, j + 1) ~= "'" do
        j = j + 1
      end
      if j < #value then
        j = j + 1
      end
      ;(function() table.insert(result, substring(value, i, j)); return result end)()
      i = j
    else
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
    end
    ::continue::
  end
  return table.concat(result, "")
end

function Word:normalize_extglob_whitespace(value)
  local current_part, deprecated_arith_depth, depth, extglob_quote, has_pipe, i, part_content, pattern_parts, prefix_char, result
  result = {}
  i = 0
  extglob_quote = new_quote_state()
  deprecated_arith_depth = 0
  while i < #value do
    if string.sub(value, i + 1, i + 1) == "\"" then
      extglob_quote.double = not extglob_quote.double
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
      goto continue
    end
    if starts_with_at(value, i, "$[") and not is_backslash_escaped(value, i) then
      deprecated_arith_depth = deprecated_arith_depth + 1
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
      goto continue
    end
    if string.sub(value, i + 1, i + 1) == "]" and deprecated_arith_depth > 0 then
      deprecated_arith_depth = deprecated_arith_depth - 1
      ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
      i = i + 1
      goto continue
    end
    if i + 1 < #value and string.sub(value, i + 1 + 1, i + 1 + 1) == "(" then
      prefix_char = string.sub(value, i + 1, i + 1)
      if (((string.find("><", prefix_char, 1, true) ~= nil))) and not extglob_quote.double and deprecated_arith_depth == 0 then
        ;(function() table.insert(result, prefix_char); return result end)()
        ;(function() table.insert(result, "("); return result end)()
        i = i + 2
        depth = 1
        pattern_parts = {}
        current_part = {}
        has_pipe = false
        while i < #value and depth > 0 do
          if string.sub(value, i + 1, i + 1) == "\\" and i + 1 < #value then
            ;(function() table.insert(current_part, string.sub(value, (i) + 1, i + 2)); return current_part end)()
            i = i + 2
            goto continue
          elseif string.sub(value, i + 1, i + 1) == "(" then
            depth = depth + 1
            ;(function() table.insert(current_part, string.sub(value, i + 1, i + 1)); return current_part end)()
            i = i + 1
          elseif string.sub(value, i + 1, i + 1) == ")" then
            depth = depth - 1
            if depth == 0 then
              part_content = table.concat(current_part, "")
              if ((string.find(part_content, "<<", 1, true) ~= nil)) then
                ;(function() table.insert(pattern_parts, part_content); return pattern_parts end)()
              elseif has_pipe then
                ;(function() table.insert(pattern_parts, (string.gsub((string.gsub(part_content, '^[' .. " \t\n\r" .. ']+', '')), '[' .. " \t\n\r" .. ']+$', ''))); return pattern_parts end)()
              else
                ;(function() table.insert(pattern_parts, part_content); return pattern_parts end)()
              end
              break
            end
            ;(function() table.insert(current_part, string.sub(value, i + 1, i + 1)); return current_part end)()
            i = i + 1
          elseif string.sub(value, i + 1, i + 1) == "|" and depth == 1 then
            if i + 1 < #value and string.sub(value, i + 1 + 1, i + 1 + 1) == "|" then
              ;(function() table.insert(current_part, "||"); return current_part end)()
              i = i + 2
            else
              has_pipe = true
              part_content = table.concat(current_part, "")
              if ((string.find(part_content, "<<", 1, true) ~= nil)) then
                ;(function() table.insert(pattern_parts, part_content); return pattern_parts end)()
              else
                ;(function() table.insert(pattern_parts, (string.gsub((string.gsub(part_content, '^[' .. " \t\n\r" .. ']+', '')), '[' .. " \t\n\r" .. ']+$', ''))); return pattern_parts end)()
              end
              current_part = {}
              i = i + 1
            end
          else
            ;(function() table.insert(current_part, string.sub(value, i + 1, i + 1)); return current_part end)()
            i = i + 1
          end
          ::continue::
        end
        ;(function() table.insert(result, table.concat(pattern_parts, " | ")); return result end)()
        if depth == 0 then
          ;(function() table.insert(result, ")"); return result end)()
          i = i + 1
        end
        goto continue
      end
    end
    ;(function() table.insert(result, string.sub(value, i + 1, i + 1)); return result end)()
    i = i + 1
    ::continue::
  end
  return table.concat(result, "")
end

function Word:get_cond_formatted_value()
  local value
  value = self:expand_all_ansi_c_quotes(self.value)
  value = self:strip_locale_string_dollars(value)
  value = self:format_command_substitutions(value, false)
  value = self:normalize_extglob_whitespace(value)
  value = (string.gsub(value, "\u{0001}", "\u{0001}\u{0001}"))
  return (string.gsub(value, '[' .. "\n" .. ']+$', ''))
end

function Word:get_kind()
  return self.kind
end

Command = {}
Command.__index = Command

function Command:new(words, redirects, kind)
  local self = setmetatable({}, Command)
  if words == nil then words = {} end
  self.words = words
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Command:to_sexp()
  local inner, parts, r, w
  parts = {}
  for _, w in ipairs(self.words) do
    ;(function() table.insert(parts, w:to_sexp()); return parts end)()
  end
  for _, r in ipairs(self.redirects) do
    ;(function() table.insert(parts, r:to_sexp()); return parts end)()
  end
  inner = table.concat(parts, " ")
  if not (inner ~= nil and #(inner) > 0) then
    return "(command)"
  end
  return "(command " .. inner .. ")"
end

function Command:get_kind()
  return self.kind
end

Pipeline = {}
Pipeline.__index = Pipeline

function Pipeline:new(commands, kind)
  local self = setmetatable({}, Pipeline)
  if commands == nil then commands = {} end
  self.commands = commands
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Pipeline:to_sexp()
  local cmd, cmds, i, j, last_cmd, last_needs, last_pair, needs, needs_redirect, pair, result
  if #self.commands == 1 then
    return self.commands[0 + 1]:to_sexp()
  end
  cmds = {}
  i = 0
  while i < #self.commands do
    cmd = self.commands[i + 1]
    if (type(cmd) == 'table' and getmetatable(cmd) == PipeBoth) then
      local cmd = cmd
      i = i + 1
      goto continue
    end
    needs_redirect = i + 1 < #self.commands and self.commands[i + 1 + 1].kind == "pipe-both"
    ;(function() table.insert(cmds, {cmd, needs_redirect}); return cmds end)()
    i = i + 1
    ::continue::
  end
  if #cmds == 1 then
    pair = cmds[0 + 1]
    cmd = pair[1]
    needs = pair[2]
    return self:cmd_sexp(cmd, needs)
  end
  last_pair = cmds[#cmds - 1 + 1]
  last_cmd = last_pair[1]
  last_needs = last_pair[2]
  result = self:cmd_sexp(last_cmd, last_needs)
  j = #cmds - 2
  while j >= 0 do
    pair = cmds[j + 1]
    cmd = pair[1]
    needs = pair[2]
    if needs and cmd.kind ~= "command" then
      result = "(pipe " .. cmd:to_sexp() .. " (redirect \">&\" 1) " .. result .. ")"
    else
      result = "(pipe " .. self:cmd_sexp(cmd, needs) .. " " .. result .. ")"
    end
    j = j - 1
  end
  return result
end

function Pipeline:cmd_sexp(cmd, needs_redirect)
  local parts, r, w
  if not needs_redirect then
    return cmd:to_sexp()
  end
  if (type(cmd) == 'table' and getmetatable(cmd) == Command) then
    local cmd = cmd
    parts = {}
    for _, w in ipairs(cmd.words) do
      ;(function() table.insert(parts, w:to_sexp()); return parts end)()
    end
    for _, r in ipairs(cmd.redirects) do
      ;(function() table.insert(parts, r:to_sexp()); return parts end)()
    end
    ;(function() table.insert(parts, "(redirect \">&\" 1)"); return parts end)()
    return "(command " .. table.concat(parts, " ") .. ")"
  end
  return cmd:to_sexp()
end

function Pipeline:get_kind()
  return self.kind
end

List = {}
List.__index = List

function List:new(parts, kind)
  local self = setmetatable({}, List)
  if parts == nil then parts = {} end
  self.parts = parts
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function List:to_sexp()
  local i, inner_list, inner_parts, left, left_sexp, op_names, parts, right, right_sexp
  parts = (function() local t = {}; for i, v in ipairs(self.parts) do t[i] = v end; return t end)()
  op_names = {["&&"] = "and", ["||"] = "or", [";"] = "semi", ["\n"] = "semi", ["&"] = "background"}
  while #parts > 1 and parts[#parts - 1 + 1].kind == "operator" and (parts[#parts - 1 + 1].op == ";" or parts[#parts - 1 + 1].op == "\n") do
    parts = sublist(parts, 0, #parts - 1)
  end
  if #parts == 1 then
    return parts[0 + 1]:to_sexp()
  end
  if parts[#parts - 1 + 1].kind == "operator" and parts[#parts - 1 + 1].op == "&" then
    i = #parts - 3
    while i > 0 do
      if parts[i + 1].kind == "operator" and (parts[i + 1].op == ";" or parts[i + 1].op == "\n") then
        left = sublist(parts, 0, i)
        right = sublist(parts, i + 1, #parts - 1)
        if #left > 1 then
          left_sexp = List:new(left, "list"):to_sexp()
        else
          left_sexp = left[0 + 1]:to_sexp()
        end
        if #right > 1 then
          right_sexp = List:new(right, "list"):to_sexp()
        else
          right_sexp = right[0 + 1]:to_sexp()
        end
        return "(semi " .. left_sexp .. " (background " .. right_sexp .. "))"
      end
      i = i + -2
    end
    inner_parts = sublist(parts, 0, #parts - 1)
    if #inner_parts == 1 then
      return "(background " .. inner_parts[0 + 1]:to_sexp() .. ")"
    end
    inner_list = List:new(inner_parts, "list")
    return "(background " .. inner_list:to_sexp() .. ")"
  end
  return self:to_sexp_with_precedence(parts, op_names)
end

function List:to_sexp_with_precedence(parts, op_names)
  local i, pos, result, seg, segments, semi_positions, start
  semi_positions = {}
  for i = 0, #parts - 1 do
    if parts[i + 1].kind == "operator" and (parts[i + 1].op == ";" or parts[i + 1].op == "\n") then
      ;(function() table.insert(semi_positions, i); return semi_positions end)()
    end
  end
  if (#(semi_positions) > 0) then
    segments = {}
    start = 0
    for _, pos in ipairs(semi_positions) do
      seg = sublist(parts, start, pos)
      if (#(seg) > 0) and seg[0 + 1].kind ~= "operator" then
        ;(function() table.insert(segments, seg); return segments end)()
      end
      start = pos + 1
    end
    seg = sublist(parts, start, #parts)
    if (#(seg) > 0) and seg[0 + 1].kind ~= "operator" then
      ;(function() table.insert(segments, seg); return segments end)()
    end
    if not (#(segments) > 0) then
      return "()"
    end
    result = self:to_sexp_amp_and_higher(segments[0 + 1], op_names)
    i = 1
    while i < #segments do
      result = "(semi " .. result .. " " .. self:to_sexp_amp_and_higher(segments[i + 1], op_names) .. ")"
      i = i + 1
    end
    return result
  end
  return self:to_sexp_amp_and_higher(parts, op_names)
end

function List:to_sexp_amp_and_higher(parts, op_names)
  local amp_positions, i, pos, result, segments, start
  if #parts == 1 then
    return parts[0 + 1]:to_sexp()
  end
  amp_positions = {}
  i = 1
  while i < #parts - 1 do
    if parts[i + 1].kind == "operator" and parts[i + 1].op == "&" then
      ;(function() table.insert(amp_positions, i); return amp_positions end)()
    end
    i = i + 2
  end
  if (#(amp_positions) > 0) then
    segments = {}
    start = 0
    for _, pos in ipairs(amp_positions) do
      ;(function() table.insert(segments, sublist(parts, start, pos)); return segments end)()
      start = pos + 1
    end
    ;(function() table.insert(segments, sublist(parts, start, #parts)); return segments end)()
    result = self:to_sexp_and_or(segments[0 + 1], op_names)
    i = 1
    while i < #segments do
      result = "(background " .. result .. " " .. self:to_sexp_and_or(segments[i + 1], op_names) .. ")"
      i = i + 1
    end
    return result
  end
  return self:to_sexp_and_or(parts, op_names)
end

function List:to_sexp_and_or(parts, op_names)
  local cmd, i, op, op_name, result
  if #parts == 1 then
    return parts[0 + 1]:to_sexp()
  end
  result = parts[0 + 1]:to_sexp()
  i = 1
  while i < #parts - 1 do
    op = parts[i + 1]
    cmd = parts[i + 1 + 1]
    op_name = _map_get(op_names, op.op, op.op)
    result = "(" .. op_name .. " " .. result .. " " .. cmd:to_sexp() .. ")"
    i = i + 2
  end
  return result
end

function List:get_kind()
  return self.kind
end

Operator = {}
Operator.__index = Operator

function Operator:new(op, kind)
  local self = setmetatable({}, Operator)
  if op == nil then op = "" end
  self.op = op
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Operator:to_sexp()
  local names
  names = {["&&"] = "and", ["||"] = "or", [";"] = "semi", ["&"] = "bg", ["|"] = "pipe"}
  return "(" .. _map_get(names, self.op, self.op) .. ")"
end

function Operator:get_kind()
  return self.kind
end

PipeBoth = {}
PipeBoth.__index = PipeBoth

function PipeBoth:new(kind)
  local self = setmetatable({}, PipeBoth)
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function PipeBoth:to_sexp()
  return "(pipe-both)"
end

function PipeBoth:get_kind()
  return self.kind
end

Empty = {}
Empty.__index = Empty

function Empty:new(kind)
  local self = setmetatable({}, Empty)
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Empty:to_sexp()
  return ""
end

function Empty:get_kind()
  return self.kind
end

Comment = {}
Comment.__index = Comment

function Comment:new(text, kind)
  local self = setmetatable({}, Comment)
  if text == nil then text = "" end
  self.text = text
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Comment:to_sexp()
  return ""
end

function Comment:get_kind()
  return self.kind
end

Redirect = {}
Redirect.__index = Redirect

function Redirect:new(op, target, fd, kind)
  local self = setmetatable({}, Redirect)
  if op == nil then op = "" end
  self.op = op
  if target == nil then target = nil end
  self.target = target
  if fd == nil then fd = nil end
  self.fd = fd
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Redirect:to_sexp()
  local fd_target, j, op, out_val, raw, target_val
  op = (string.gsub(self.op, '^[' .. "0123456789" .. ']+', ''))
  if (string.sub(op, 1, #"{") == "{") then
    j = 1
    if j < #op and ((string.match(string.sub(op, j + 1, j + 1), '^%a+$') ~= nil) or string.sub(op, j + 1, j + 1) == "_") then
      j = j + 1
      while j < #op and ((string.match(string.sub(op, j + 1, j + 1), '^%w+$') ~= nil) or string.sub(op, j + 1, j + 1) == "_") do
        j = j + 1
      end
      if j < #op and string.sub(op, j + 1, j + 1) == "[" then
        j = j + 1
        while j < #op and string.sub(op, j + 1, j + 1) ~= "]" do
          j = j + 1
        end
        if j < #op and string.sub(op, j + 1, j + 1) == "]" then
          j = j + 1
        end
      end
      if j < #op and string.sub(op, j + 1, j + 1) == "}" then
        op = substring(op, j + 1, #op)
      end
    end
  end
  target_val = self.target.value
  target_val = self.target:expand_all_ansi_c_quotes(target_val)
  target_val = self.target:strip_locale_string_dollars(target_val)
  target_val = self.target:format_command_substitutions(target_val, false)
  target_val = self.target:strip_arith_line_continuations(target_val)
  if (string.sub(target_val, -#"\\") == "\\") and not (string.sub(target_val, -#"\\\\") == "\\\\") then
    target_val = target_val .. "\\"
  end
  if (string.sub(target_val, 1, #"&") == "&") then
    if op == ">" then
      op = ">&"
    elseif op == "<" then
      op = "<&"
    end
    raw = substring(target_val, 1, #target_val)
    if (string.match(raw, '^%d+$') ~= nil) and tonumber(raw) <= 2147483647 then
      return "(redirect \"" .. op .. "\" " .. tostring(tonumber(raw)) .. ")"
    end
    if (string.sub(raw, -#"-") == "-") and (string.match(string.sub(raw, 1, #raw - 1), '^%d+$') ~= nil) and tonumber(string.sub(raw, 1, #raw - 1)) <= 2147483647 then
      return "(redirect \"" .. op .. "\" " .. tostring(tonumber(string.sub(raw, 1, #raw - 1))) .. ")"
    end
    if target_val == "&-" then
      return "(redirect \">&-\" 0)"
    end
    fd_target = ((string.sub(raw, -#"-") == "-") and string.sub(raw, 1, #raw - 1) or raw)
    return "(redirect \"" .. op .. "\" \"" .. fd_target .. "\")"
  end
  if op == ">&" or op == "<&" then
    if (string.match(target_val, '^%d+$') ~= nil) and tonumber(target_val) <= 2147483647 then
      return "(redirect \"" .. op .. "\" " .. tostring(tonumber(target_val)) .. ")"
    end
    if target_val == "-" then
      return "(redirect \">&-\" 0)"
    end
    if (string.sub(target_val, -#"-") == "-") and (string.match(string.sub(target_val, 1, #target_val - 1), '^%d+$') ~= nil) and tonumber(string.sub(target_val, 1, #target_val - 1)) <= 2147483647 then
      return "(redirect \"" .. op .. "\" " .. tostring(tonumber(string.sub(target_val, 1, #target_val - 1))) .. ")"
    end
    out_val = ((string.sub(target_val, -#"-") == "-") and string.sub(target_val, 1, #target_val - 1) or target_val)
    return "(redirect \"" .. op .. "\" \"" .. out_val .. "\")"
  end
  return "(redirect \"" .. op .. "\" \"" .. target_val .. "\")"
end

function Redirect:get_kind()
  return self.kind
end

HereDoc = {}
HereDoc.__index = HereDoc

function HereDoc:new(delimiter, content, strip_tabs, quoted, fd, complete, start_pos, kind)
  local self = setmetatable({}, HereDoc)
  if delimiter == nil then delimiter = "" end
  self.delimiter = delimiter
  if content == nil then content = "" end
  self.content = content
  if strip_tabs == nil then strip_tabs = false end
  self.strip_tabs = strip_tabs
  if quoted == nil then quoted = false end
  self.quoted = quoted
  if fd == nil then fd = nil end
  self.fd = fd
  if complete == nil then complete = false end
  self.complete = complete
  if start_pos == nil then start_pos = 0 end
  self.start_pos = start_pos
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function HereDoc:to_sexp()
  local content, op
  op = (self.strip_tabs and "<<-" or "<<")
  content = self.content
  if (string.sub(content, -#"\\") == "\\") and not (string.sub(content, -#"\\\\") == "\\\\") then
    content = content .. "\\"
  end
  return string.format("(redirect \"%s\" \"%s\")", op, content)
end

function HereDoc:get_kind()
  return self.kind
end

Subshell = {}
Subshell.__index = Subshell

function Subshell:new(body, redirects, kind)
  local self = setmetatable({}, Subshell)
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Subshell:to_sexp()
  local base
  base = "(subshell " .. self.body:to_sexp() .. ")"
  return append_redirects(base, self.redirects)
end

function Subshell:get_kind()
  return self.kind
end

BraceGroup = {}
BraceGroup.__index = BraceGroup

function BraceGroup:new(body, redirects, kind)
  local self = setmetatable({}, BraceGroup)
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function BraceGroup:to_sexp()
  local base
  base = "(brace-group " .. self.body:to_sexp() .. ")"
  return append_redirects(base, self.redirects)
end

function BraceGroup:get_kind()
  return self.kind
end

If = {}
If.__index = If

function If:new(condition, then_body, else_body, redirects, kind)
  local self = setmetatable({}, If)
  if condition == nil then condition = nil end
  self.condition = condition
  if then_body == nil then then_body = nil end
  self.then_body = then_body
  if else_body == nil then else_body = nil end
  self.else_body = else_body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function If:to_sexp()
  local r, result
  result = "(if " .. self.condition:to_sexp() .. " " .. self.then_body:to_sexp()
  if (self.else_body ~= nil) then
    result = result .. " " .. self.else_body:to_sexp()
  end
  result = result .. ")"
  for _, r in ipairs(self.redirects) do
    result = result .. " " .. r:to_sexp()
  end
  return result
end

function If:get_kind()
  return self.kind
end

While = {}
While.__index = While

function While:new(condition, body, redirects, kind)
  local self = setmetatable({}, While)
  if condition == nil then condition = nil end
  self.condition = condition
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function While:to_sexp()
  local base
  base = "(while " .. self.condition:to_sexp() .. " " .. self.body:to_sexp() .. ")"
  return append_redirects(base, self.redirects)
end

function While:get_kind()
  return self.kind
end

Until = {}
Until.__index = Until

function Until:new(condition, body, redirects, kind)
  local self = setmetatable({}, Until)
  if condition == nil then condition = nil end
  self.condition = condition
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Until:to_sexp()
  local base
  base = "(until " .. self.condition:to_sexp() .. " " .. self.body:to_sexp() .. ")"
  return append_redirects(base, self.redirects)
end

function Until:get_kind()
  return self.kind
end

For = {}
For.__index = For

function For:new(var, words, body, redirects, kind)
  local self = setmetatable({}, For)
  if var == nil then var = "" end
  self.var = var
  if words == nil then words = nil end
  self.words = words
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function For:to_sexp()
  local r, redirect_parts, suffix, temp_word, var_escaped, var_formatted, w, word_parts, word_strs
  suffix = ""
  if (#(self.redirects) > 0) then
    redirect_parts = {}
    for _, r in ipairs(self.redirects) do
      ;(function() table.insert(redirect_parts, r:to_sexp()); return redirect_parts end)()
    end
    suffix = " " .. table.concat(redirect_parts, " ")
  end
  temp_word = Word:new(self.var, {}, "word")
  var_formatted = temp_word:format_command_substitutions(self.var, false)
  var_escaped = (string.gsub((string.gsub(var_formatted, "\\", "\\\\")), "\"", "\\\""))
  if (self.words == nil) then
    return "(for (word \"" .. var_escaped .. "\") (in (word \"\\\"$@\\\"\")) " .. self.body:to_sexp() .. ")" .. suffix
  elseif #self.words == 0 then
    return "(for (word \"" .. var_escaped .. "\") (in) " .. self.body:to_sexp() .. ")" .. suffix
  else
    word_parts = {}
    for _, w in ipairs(self.words) do
      ;(function() table.insert(word_parts, w:to_sexp()); return word_parts end)()
    end
    word_strs = table.concat(word_parts, " ")
    return "(for (word \"" .. var_escaped .. "\") (in " .. word_strs .. ") " .. self.body:to_sexp() .. ")" .. suffix
  end
end

function For:get_kind()
  return self.kind
end

ForArith = {}
ForArith.__index = ForArith

function ForArith:new(init, cond, incr, body, redirects, kind)
  local self = setmetatable({}, ForArith)
  if init == nil then init = "" end
  self.init = init
  if cond == nil then cond = "" end
  self.cond = cond
  if incr == nil then incr = "" end
  self.incr = incr
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ForArith:to_sexp()
  local body_str, cond_str, cond_val, incr_str, incr_val, init_str, init_val, r, redirect_parts, suffix
  suffix = ""
  if (#(self.redirects) > 0) then
    redirect_parts = {}
    for _, r in ipairs(self.redirects) do
      ;(function() table.insert(redirect_parts, r:to_sexp()); return redirect_parts end)()
    end
    suffix = " " .. table.concat(redirect_parts, " ")
  end
  init_val = ((self.init ~= nil and #(self.init) > 0) and self.init or "1")
  cond_val = ((self.cond ~= nil and #(self.cond) > 0) and self.cond or "1")
  incr_val = ((self.incr ~= nil and #(self.incr) > 0) and self.incr or "1")
  init_str = format_arith_val(init_val)
  cond_str = format_arith_val(cond_val)
  incr_str = format_arith_val(incr_val)
  body_str = self.body:to_sexp()
  return string.format("(arith-for (init (word \"%s\")) (test (word \"%s\")) (step (word \"%s\")) %s)%s", init_str, cond_str, incr_str, body_str, suffix)
end

function ForArith:get_kind()
  return self.kind
end

Select = {}
Select.__index = Select

function Select:new(var, words, body, redirects, kind)
  local self = setmetatable({}, Select)
  if var == nil then var = "" end
  self.var = var
  if words == nil then words = nil end
  self.words = words
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Select:to_sexp()
  local in_clause, r, redirect_parts, suffix, var_escaped, w, word_parts, word_strs
  suffix = ""
  if (#(self.redirects) > 0) then
    redirect_parts = {}
    for _, r in ipairs(self.redirects) do
      ;(function() table.insert(redirect_parts, r:to_sexp()); return redirect_parts end)()
    end
    suffix = " " .. table.concat(redirect_parts, " ")
  end
  var_escaped = (string.gsub((string.gsub(self.var, "\\", "\\\\")), "\"", "\\\""))
  if (self.words ~= nil) then
    word_parts = {}
    for _, w in ipairs(self.words) do
      ;(function() table.insert(word_parts, w:to_sexp()); return word_parts end)()
    end
    word_strs = table.concat(word_parts, " ")
    if (self.words ~= nil and #(self.words) > 0) then
      in_clause = "(in " .. word_strs .. ")"
    else
      in_clause = "(in)"
    end
  else
    in_clause = "(in (word \"\\\"$@\\\"\"))"
  end
  return "(select (word \"" .. var_escaped .. "\") " .. in_clause .. " " .. self.body:to_sexp() .. ")" .. suffix
end

function Select:get_kind()
  return self.kind
end

Case = {}
Case.__index = Case

function Case:new(word, patterns, redirects, kind)
  local self = setmetatable({}, Case)
  if word == nil then word = nil end
  self.word = word
  if patterns == nil then patterns = {} end
  self.patterns = patterns
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Case:to_sexp()
  local base, p, parts
  parts = {}
  ;(function() table.insert(parts, "(case " .. self.word:to_sexp()); return parts end)()
  for _, p in ipairs(self.patterns) do
    ;(function() table.insert(parts, p:to_sexp()); return parts end)()
  end
  base = table.concat(parts, " ") .. ")"
  return append_redirects(base, self.redirects)
end

function Case:get_kind()
  return self.kind
end

CasePattern = {}
CasePattern.__index = CasePattern

function CasePattern:new(pattern, body, terminator, kind)
  local self = setmetatable({}, CasePattern)
  if pattern == nil then pattern = "" end
  self.pattern = pattern
  if body == nil then body = nil end
  self.body = body
  if terminator == nil then terminator = "" end
  self.terminator = terminator
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function CasePattern:to_sexp()
  local alt, alternatives, ch, current, depth, i, parts, pattern_str, result0, result1, result2, word_list
  alternatives = {}
  current = {}
  i = 0
  depth = 0
  while i < #self.pattern do
    ch = string.sub(self.pattern, i + 1, i + 1)
    if ch == "\\" and i + 1 < #self.pattern then
      ;(function() table.insert(current, substring(self.pattern, i, i + 2)); return current end)()
      i = i + 2
    elseif (ch == "@" or ch == "?" or ch == "*" or ch == "+" or ch == "!") and i + 1 < #self.pattern and string.sub(self.pattern, i + 1 + 1, i + 1 + 1) == "(" then
      ;(function() table.insert(current, ch); return current end)()
      ;(function() table.insert(current, "("); return current end)()
      depth = depth + 1
      i = i + 2
    elseif is_expansion_start(self.pattern, i, "$(") then
      ;(function() table.insert(current, ch); return current end)()
      ;(function() table.insert(current, "("); return current end)()
      depth = depth + 1
      i = i + 2
    elseif ch == "(" and depth > 0 then
      ;(function() table.insert(current, ch); return current end)()
      depth = depth + 1
      i = i + 1
    elseif ch == ")" and depth > 0 then
      ;(function() table.insert(current, ch); return current end)()
      depth = depth - 1
      i = i + 1
    elseif ch == "[" then
      result0, result1, result2 = table.unpack(consume_bracket_class(self.pattern, i, depth))
      i = result0
      ;(function() for _, v in ipairs(result1) do table.insert(current, v) end; return current end)()
    elseif ch == "'" and depth == 0 then
      result0, result1 = table.unpack(consume_single_quote(self.pattern, i))
      i = result0
      ;(function() for _, v in ipairs(result1) do table.insert(current, v) end; return current end)()
    elseif ch == "\"" and depth == 0 then
      result0, result1 = table.unpack(consume_double_quote(self.pattern, i))
      i = result0
      ;(function() for _, v in ipairs(result1) do table.insert(current, v) end; return current end)()
    elseif ch == "|" and depth == 0 then
      ;(function() table.insert(alternatives, table.concat(current, "")); return alternatives end)()
      current = {}
      i = i + 1
    else
      ;(function() table.insert(current, ch); return current end)()
      i = i + 1
    end
  end
  ;(function() table.insert(alternatives, table.concat(current, "")); return alternatives end)()
  word_list = {}
  for _, alt in ipairs(alternatives) do
    ;(function() table.insert(word_list, Word:new(alt, nil, "word"):to_sexp()); return word_list end)()
  end
  pattern_str = table.concat(word_list, " ")
  parts = {"(pattern (" .. pattern_str .. ")"}
  if (self.body ~= nil) then
    ;(function() table.insert(parts, " " .. self.body:to_sexp()); return parts end)()
  else
    ;(function() table.insert(parts, " ()"); return parts end)()
  end
  ;(function() table.insert(parts, ")"); return parts end)()
  return table.concat(parts, "")
end

function CasePattern:get_kind()
  return self.kind
end

Function = {}
Function.__index = Function

function Function:new(name, body, kind)
  local self = setmetatable({}, Function)
  if name == nil then name = "" end
  self.name = name
  if body == nil then body = nil end
  self.body = body
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Function:to_sexp()
  return "(function \"" .. self.name .. "\" " .. self.body:to_sexp() .. ")"
end

function Function:get_kind()
  return self.kind
end

ParamExpansion = {}
ParamExpansion.__index = ParamExpansion

function ParamExpansion:new(param, op, arg_, kind)
  local self = setmetatable({}, ParamExpansion)
  if param == nil then param = "" end
  self.param = param
  if op == nil then op = "" end
  self.op = op
  if arg_ == nil then arg_ = "" end
  self.arg_ = arg_
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ParamExpansion:to_sexp()
  local arg_val, escaped_arg, escaped_op, escaped_param
  escaped_param = (string.gsub((string.gsub(self.param, "\\", "\\\\")), "\"", "\\\""))
  if self.op ~= "" then
    escaped_op = (string.gsub((string.gsub(self.op, "\\", "\\\\")), "\"", "\\\""))
    if self.arg_ ~= "" then
      arg_val = self.arg_
    else
      arg_val = ""
    end
    escaped_arg = (string.gsub((string.gsub(arg_val, "\\", "\\\\")), "\"", "\\\""))
    return "(param \"" .. escaped_param .. "\" \"" .. escaped_op .. "\" \"" .. escaped_arg .. "\")"
  end
  return "(param \"" .. escaped_param .. "\")"
end

function ParamExpansion:get_kind()
  return self.kind
end

ParamLength = {}
ParamLength.__index = ParamLength

function ParamLength:new(param, kind)
  local self = setmetatable({}, ParamLength)
  if param == nil then param = "" end
  self.param = param
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ParamLength:to_sexp()
  local escaped
  escaped = (string.gsub((string.gsub(self.param, "\\", "\\\\")), "\"", "\\\""))
  return "(param-len \"" .. escaped .. "\")"
end

function ParamLength:get_kind()
  return self.kind
end

ParamIndirect = {}
ParamIndirect.__index = ParamIndirect

function ParamIndirect:new(param, op, arg_, kind)
  local self = setmetatable({}, ParamIndirect)
  if param == nil then param = "" end
  self.param = param
  if op == nil then op = "" end
  self.op = op
  if arg_ == nil then arg_ = "" end
  self.arg_ = arg_
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ParamIndirect:to_sexp()
  local arg_val, escaped, escaped_arg, escaped_op
  escaped = (string.gsub((string.gsub(self.param, "\\", "\\\\")), "\"", "\\\""))
  if self.op ~= "" then
    escaped_op = (string.gsub((string.gsub(self.op, "\\", "\\\\")), "\"", "\\\""))
    if self.arg_ ~= "" then
      arg_val = self.arg_
    else
      arg_val = ""
    end
    escaped_arg = (string.gsub((string.gsub(arg_val, "\\", "\\\\")), "\"", "\\\""))
    return "(param-indirect \"" .. escaped .. "\" \"" .. escaped_op .. "\" \"" .. escaped_arg .. "\")"
  end
  return "(param-indirect \"" .. escaped .. "\")"
end

function ParamIndirect:get_kind()
  return self.kind
end

CommandSubstitution = {}
CommandSubstitution.__index = CommandSubstitution

function CommandSubstitution:new(command, brace, kind)
  local self = setmetatable({}, CommandSubstitution)
  if command == nil then command = nil end
  self.command = command
  if brace == nil then brace = false end
  self.brace = brace
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function CommandSubstitution:to_sexp()
  if self.brace then
    return "(funsub " .. self.command:to_sexp() .. ")"
  end
  return "(cmdsub " .. self.command:to_sexp() .. ")"
end

function CommandSubstitution:get_kind()
  return self.kind
end

ArithmeticExpansion = {}
ArithmeticExpansion.__index = ArithmeticExpansion

function ArithmeticExpansion:new(expression, kind)
  local self = setmetatable({}, ArithmeticExpansion)
  if expression == nil then expression = nil end
  self.expression = expression
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithmeticExpansion:to_sexp()
  if (self.expression == nil) then
    return "(arith)"
  end
  return "(arith " .. self.expression:to_sexp() .. ")"
end

function ArithmeticExpansion:get_kind()
  return self.kind
end

ArithmeticCommand = {}
ArithmeticCommand.__index = ArithmeticCommand

function ArithmeticCommand:new(expression, redirects, raw_content, kind)
  local self = setmetatable({}, ArithmeticCommand)
  if expression == nil then expression = nil end
  self.expression = expression
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if raw_content == nil then raw_content = "" end
  self.raw_content = raw_content
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithmeticCommand:to_sexp()
  local escaped, formatted, r, redirect_parts, redirect_sexps, result
  formatted = Word:new(self.raw_content, nil, "word"):format_command_substitutions(self.raw_content, true)
  escaped = (string.gsub((string.gsub((string.gsub((string.gsub(formatted, "\\", "\\\\")), "\"", "\\\"")), "\n", "\\n")), "\t", "\\t"))
  result = "(arith (word \"" .. escaped .. "\"))"
  if (#(self.redirects) > 0) then
    redirect_parts = {}
    for _, r in ipairs(self.redirects) do
      ;(function() table.insert(redirect_parts, r:to_sexp()); return redirect_parts end)()
    end
    redirect_sexps = table.concat(redirect_parts, " ")
    return result .. " " .. redirect_sexps
  end
  return result
end

function ArithmeticCommand:get_kind()
  return self.kind
end

ArithNumber = {}
ArithNumber.__index = ArithNumber

function ArithNumber:new(value, kind)
  local self = setmetatable({}, ArithNumber)
  if value == nil then value = "" end
  self.value = value
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithNumber:to_sexp()
  return "(number \"" .. self.value .. "\")"
end

function ArithNumber:get_kind()
  return self.kind
end

ArithEmpty = {}
ArithEmpty.__index = ArithEmpty

function ArithEmpty:new(kind)
  local self = setmetatable({}, ArithEmpty)
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithEmpty:to_sexp()
  return "(empty)"
end

function ArithEmpty:get_kind()
  return self.kind
end

ArithVar = {}
ArithVar.__index = ArithVar

function ArithVar:new(name, kind)
  local self = setmetatable({}, ArithVar)
  if name == nil then name = "" end
  self.name = name
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithVar:to_sexp()
  return "(var \"" .. self.name .. "\")"
end

function ArithVar:get_kind()
  return self.kind
end

ArithBinaryOp = {}
ArithBinaryOp.__index = ArithBinaryOp

function ArithBinaryOp:new(op, left, right, kind)
  local self = setmetatable({}, ArithBinaryOp)
  if op == nil then op = "" end
  self.op = op
  if left == nil then left = nil end
  self.left = left
  if right == nil then right = nil end
  self.right = right
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithBinaryOp:to_sexp()
  return "(binary-op \"" .. self.op .. "\" " .. self.left:to_sexp() .. " " .. self.right:to_sexp() .. ")"
end

function ArithBinaryOp:get_kind()
  return self.kind
end

ArithUnaryOp = {}
ArithUnaryOp.__index = ArithUnaryOp

function ArithUnaryOp:new(op, operand, kind)
  local self = setmetatable({}, ArithUnaryOp)
  if op == nil then op = "" end
  self.op = op
  if operand == nil then operand = nil end
  self.operand = operand
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithUnaryOp:to_sexp()
  return "(unary-op \"" .. self.op .. "\" " .. self.operand:to_sexp() .. ")"
end

function ArithUnaryOp:get_kind()
  return self.kind
end

ArithPreIncr = {}
ArithPreIncr.__index = ArithPreIncr

function ArithPreIncr:new(operand, kind)
  local self = setmetatable({}, ArithPreIncr)
  if operand == nil then operand = nil end
  self.operand = operand
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithPreIncr:to_sexp()
  return "(pre-incr " .. self.operand:to_sexp() .. ")"
end

function ArithPreIncr:get_kind()
  return self.kind
end

ArithPostIncr = {}
ArithPostIncr.__index = ArithPostIncr

function ArithPostIncr:new(operand, kind)
  local self = setmetatable({}, ArithPostIncr)
  if operand == nil then operand = nil end
  self.operand = operand
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithPostIncr:to_sexp()
  return "(post-incr " .. self.operand:to_sexp() .. ")"
end

function ArithPostIncr:get_kind()
  return self.kind
end

ArithPreDecr = {}
ArithPreDecr.__index = ArithPreDecr

function ArithPreDecr:new(operand, kind)
  local self = setmetatable({}, ArithPreDecr)
  if operand == nil then operand = nil end
  self.operand = operand
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithPreDecr:to_sexp()
  return "(pre-decr " .. self.operand:to_sexp() .. ")"
end

function ArithPreDecr:get_kind()
  return self.kind
end

ArithPostDecr = {}
ArithPostDecr.__index = ArithPostDecr

function ArithPostDecr:new(operand, kind)
  local self = setmetatable({}, ArithPostDecr)
  if operand == nil then operand = nil end
  self.operand = operand
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithPostDecr:to_sexp()
  return "(post-decr " .. self.operand:to_sexp() .. ")"
end

function ArithPostDecr:get_kind()
  return self.kind
end

ArithAssign = {}
ArithAssign.__index = ArithAssign

function ArithAssign:new(op, target, value, kind)
  local self = setmetatable({}, ArithAssign)
  if op == nil then op = "" end
  self.op = op
  if target == nil then target = nil end
  self.target = target
  if value == nil then value = nil end
  self.value = value
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithAssign:to_sexp()
  return "(assign \"" .. self.op .. "\" " .. self.target:to_sexp() .. " " .. self.value:to_sexp() .. ")"
end

function ArithAssign:get_kind()
  return self.kind
end

ArithTernary = {}
ArithTernary.__index = ArithTernary

function ArithTernary:new(condition, if_true, if_false, kind)
  local self = setmetatable({}, ArithTernary)
  if condition == nil then condition = nil end
  self.condition = condition
  if if_true == nil then if_true = nil end
  self.if_true = if_true
  if if_false == nil then if_false = nil end
  self.if_false = if_false
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithTernary:to_sexp()
  return "(ternary " .. self.condition:to_sexp() .. " " .. self.if_true:to_sexp() .. " " .. self.if_false:to_sexp() .. ")"
end

function ArithTernary:get_kind()
  return self.kind
end

ArithComma = {}
ArithComma.__index = ArithComma

function ArithComma:new(left, right, kind)
  local self = setmetatable({}, ArithComma)
  if left == nil then left = nil end
  self.left = left
  if right == nil then right = nil end
  self.right = right
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithComma:to_sexp()
  return "(comma " .. self.left:to_sexp() .. " " .. self.right:to_sexp() .. ")"
end

function ArithComma:get_kind()
  return self.kind
end

ArithSubscript = {}
ArithSubscript.__index = ArithSubscript

function ArithSubscript:new(array, index, kind)
  local self = setmetatable({}, ArithSubscript)
  if array == nil then array = "" end
  self.array = array
  if index == nil then index = nil end
  self.index = index
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithSubscript:to_sexp()
  return "(subscript \"" .. self.array .. "\" " .. self.index:to_sexp() .. ")"
end

function ArithSubscript:get_kind()
  return self.kind
end

ArithEscape = {}
ArithEscape.__index = ArithEscape

function ArithEscape:new(char, kind)
  local self = setmetatable({}, ArithEscape)
  if char == nil then char = "" end
  self.char = char
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithEscape:to_sexp()
  return "(escape \"" .. self.char .. "\")"
end

function ArithEscape:get_kind()
  return self.kind
end

ArithDeprecated = {}
ArithDeprecated.__index = ArithDeprecated

function ArithDeprecated:new(expression, kind)
  local self = setmetatable({}, ArithDeprecated)
  if expression == nil then expression = "" end
  self.expression = expression
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithDeprecated:to_sexp()
  local escaped
  escaped = (string.gsub((string.gsub((string.gsub(self.expression, "\\", "\\\\")), "\"", "\\\"")), "\n", "\\n"))
  return "(arith-deprecated \"" .. escaped .. "\")"
end

function ArithDeprecated:get_kind()
  return self.kind
end

ArithConcat = {}
ArithConcat.__index = ArithConcat

function ArithConcat:new(parts, kind)
  local self = setmetatable({}, ArithConcat)
  if parts == nil then parts = {} end
  self.parts = parts
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ArithConcat:to_sexp()
  local p, sexps
  sexps = {}
  for _, p in ipairs(self.parts) do
    ;(function() table.insert(sexps, p:to_sexp()); return sexps end)()
  end
  return "(arith-concat " .. table.concat(sexps, " ") .. ")"
end

function ArithConcat:get_kind()
  return self.kind
end

AnsiCQuote = {}
AnsiCQuote.__index = AnsiCQuote

function AnsiCQuote:new(content, kind)
  local self = setmetatable({}, AnsiCQuote)
  if content == nil then content = "" end
  self.content = content
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function AnsiCQuote:to_sexp()
  local escaped
  escaped = (string.gsub((string.gsub((string.gsub(self.content, "\\", "\\\\")), "\"", "\\\"")), "\n", "\\n"))
  return "(ansi-c \"" .. escaped .. "\")"
end

function AnsiCQuote:get_kind()
  return self.kind
end

LocaleString = {}
LocaleString.__index = LocaleString

function LocaleString:new(content, kind)
  local self = setmetatable({}, LocaleString)
  if content == nil then content = "" end
  self.content = content
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function LocaleString:to_sexp()
  local escaped
  escaped = (string.gsub((string.gsub((string.gsub(self.content, "\\", "\\\\")), "\"", "\\\"")), "\n", "\\n"))
  return "(locale \"" .. escaped .. "\")"
end

function LocaleString:get_kind()
  return self.kind
end

ProcessSubstitution = {}
ProcessSubstitution.__index = ProcessSubstitution

function ProcessSubstitution:new(direction, command, kind)
  local self = setmetatable({}, ProcessSubstitution)
  if direction == nil then direction = "" end
  self.direction = direction
  if command == nil then command = nil end
  self.command = command
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ProcessSubstitution:to_sexp()
  return "(procsub \"" .. self.direction .. "\" " .. self.command:to_sexp() .. ")"
end

function ProcessSubstitution:get_kind()
  return self.kind
end

Negation = {}
Negation.__index = Negation

function Negation:new(pipeline, kind)
  local self = setmetatable({}, Negation)
  if pipeline == nil then pipeline = nil end
  self.pipeline = pipeline
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Negation:to_sexp()
  if (self.pipeline == nil) then
    return "(negation (command))"
  end
  return "(negation " .. self.pipeline:to_sexp() .. ")"
end

function Negation:get_kind()
  return self.kind
end

Time = {}
Time.__index = Time

function Time:new(pipeline, posix, kind)
  local self = setmetatable({}, Time)
  if pipeline == nil then pipeline = nil end
  self.pipeline = pipeline
  if posix == nil then posix = false end
  self.posix = posix
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Time:to_sexp()
  if (self.pipeline == nil) then
    if self.posix then
      return "(time -p (command))"
    else
      return "(time (command))"
    end
  end
  if self.posix then
    return "(time -p " .. self.pipeline:to_sexp() .. ")"
  end
  return "(time " .. self.pipeline:to_sexp() .. ")"
end

function Time:get_kind()
  return self.kind
end

ConditionalExpr = {}
ConditionalExpr.__index = ConditionalExpr

function ConditionalExpr:new(body, redirects, kind)
  local self = setmetatable({}, ConditionalExpr)
  if body == nil then body = nil end
  self.body = body
  if redirects == nil then redirects = {} end
  self.redirects = redirects
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function ConditionalExpr:to_sexp()
  local body, escaped, r, redirect_parts, redirect_sexps, result
  body = self.body
  if type(body) == 'string' then
    local body = body
    escaped = (string.gsub((string.gsub((string.gsub(body, "\\", "\\\\")), "\"", "\\\"")), "\n", "\\n"))
    result = "(cond \"" .. escaped .. "\")"
  else
    result = "(cond " .. body:to_sexp() .. ")"
  end
  if (#(self.redirects) > 0) then
    redirect_parts = {}
    for _, r in ipairs(self.redirects) do
      ;(function() table.insert(redirect_parts, r:to_sexp()); return redirect_parts end)()
    end
    redirect_sexps = table.concat(redirect_parts, " ")
    return result .. " " .. redirect_sexps
  end
  return result
end

function ConditionalExpr:get_kind()
  return self.kind
end

UnaryTest = {}
UnaryTest.__index = UnaryTest

function UnaryTest:new(op, operand, kind)
  local self = setmetatable({}, UnaryTest)
  if op == nil then op = "" end
  self.op = op
  if operand == nil then operand = nil end
  self.operand = operand
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function UnaryTest:to_sexp()
  local operand_val
  operand_val = self.operand:get_cond_formatted_value()
  return "(cond-unary \"" .. self.op .. "\" (cond-term \"" .. operand_val .. "\"))"
end

function UnaryTest:get_kind()
  return self.kind
end

BinaryTest = {}
BinaryTest.__index = BinaryTest

function BinaryTest:new(op, left, right, kind)
  local self = setmetatable({}, BinaryTest)
  if op == nil then op = "" end
  self.op = op
  if left == nil then left = nil end
  self.left = left
  if right == nil then right = nil end
  self.right = right
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function BinaryTest:to_sexp()
  local left_val, right_val
  left_val = self.left:get_cond_formatted_value()
  right_val = self.right:get_cond_formatted_value()
  return "(cond-binary \"" .. self.op .. "\" (cond-term \"" .. left_val .. "\") (cond-term \"" .. right_val .. "\"))"
end

function BinaryTest:get_kind()
  return self.kind
end

CondAnd = {}
CondAnd.__index = CondAnd

function CondAnd:new(left, right, kind)
  local self = setmetatable({}, CondAnd)
  if left == nil then left = nil end
  self.left = left
  if right == nil then right = nil end
  self.right = right
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function CondAnd:to_sexp()
  return "(cond-and " .. self.left:to_sexp() .. " " .. self.right:to_sexp() .. ")"
end

function CondAnd:get_kind()
  return self.kind
end

CondOr = {}
CondOr.__index = CondOr

function CondOr:new(left, right, kind)
  local self = setmetatable({}, CondOr)
  if left == nil then left = nil end
  self.left = left
  if right == nil then right = nil end
  self.right = right
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function CondOr:to_sexp()
  return "(cond-or " .. self.left:to_sexp() .. " " .. self.right:to_sexp() .. ")"
end

function CondOr:get_kind()
  return self.kind
end

CondNot = {}
CondNot.__index = CondNot

function CondNot:new(operand, kind)
  local self = setmetatable({}, CondNot)
  if operand == nil then operand = nil end
  self.operand = operand
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function CondNot:to_sexp()
  return self.operand:to_sexp()
end

function CondNot:get_kind()
  return self.kind
end

CondParen = {}
CondParen.__index = CondParen

function CondParen:new(inner, kind)
  local self = setmetatable({}, CondParen)
  if inner == nil then inner = nil end
  self.inner = inner
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function CondParen:to_sexp()
  return "(cond-expr " .. self.inner:to_sexp() .. ")"
end

function CondParen:get_kind()
  return self.kind
end

Array = {}
Array.__index = Array

function Array:new(elements, kind)
  local self = setmetatable({}, Array)
  if elements == nil then elements = {} end
  self.elements = elements
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Array:to_sexp()
  local e, inner, parts
  if not (#(self.elements) > 0) then
    return "(array)"
  end
  parts = {}
  for _, e in ipairs(self.elements) do
    ;(function() table.insert(parts, e:to_sexp()); return parts end)()
  end
  inner = table.concat(parts, " ")
  return "(array " .. inner .. ")"
end

function Array:get_kind()
  return self.kind
end

Coproc = {}
Coproc.__index = Coproc

function Coproc:new(command, name, kind)
  local self = setmetatable({}, Coproc)
  if command == nil then command = nil end
  self.command = command
  if name == nil then name = "" end
  self.name = name
  if kind == nil then kind = "" end
  self.kind = kind
  return self
end

function Coproc:to_sexp()
  local name
  if (self.name ~= nil and #(self.name) > 0) then
    name = self.name
  else
    name = "COPROC"
  end
  return "(coproc \"" .. name .. "\" " .. self.command:to_sexp() .. ")"
end

function Coproc:get_kind()
  return self.kind
end

Parser = {}
Parser.__index = Parser

function Parser:new(source, pos, length, pending_heredocs, cmdsub_heredoc_end, saw_newline_in_single_quote, in_process_sub, extglob, ctx, lexer, token_history, parser_state, dolbrace_state, eof_token, word_context, at_command_start, in_array_literal, in_assign_builtin, arith_src, arith_pos, arith_len)
  local self = setmetatable({}, Parser)
  if source == nil then source = "" end
  self.source = source
  if pos == nil then pos = 0 end
  self.pos = pos
  if length == nil then length = 0 end
  self.length = length
  if pending_heredocs == nil then pending_heredocs = {} end
  self.pending_heredocs = pending_heredocs
  if cmdsub_heredoc_end == nil then cmdsub_heredoc_end = 0 end
  self.cmdsub_heredoc_end = cmdsub_heredoc_end
  if saw_newline_in_single_quote == nil then saw_newline_in_single_quote = false end
  self.saw_newline_in_single_quote = saw_newline_in_single_quote
  if in_process_sub == nil then in_process_sub = false end
  self.in_process_sub = in_process_sub
  if extglob == nil then extglob = false end
  self.extglob = extglob
  if ctx == nil then ctx = nil end
  self.ctx = ctx
  if lexer == nil then lexer = nil end
  self.lexer = lexer
  if token_history == nil then token_history = {} end
  self.token_history = token_history
  if parser_state == nil then parser_state = 0 end
  self.parser_state = parser_state
  if dolbrace_state == nil then dolbrace_state = 0 end
  self.dolbrace_state = dolbrace_state
  if eof_token == nil then eof_token = "" end
  self.eof_token = eof_token
  if word_context == nil then word_context = 0 end
  self.word_context = word_context
  if at_command_start == nil then at_command_start = false end
  self.at_command_start = at_command_start
  if in_array_literal == nil then in_array_literal = false end
  self.in_array_literal = in_array_literal
  if in_assign_builtin == nil then in_assign_builtin = false end
  self.in_assign_builtin = in_assign_builtin
  if arith_src == nil then arith_src = "" end
  self.arith_src = arith_src
  if arith_pos == nil then arith_pos = 0 end
  self.arith_pos = arith_pos
  if arith_len == nil then arith_len = 0 end
  self.arith_len = arith_len
  return self
end

function Parser:set_state(flag)
  self.parser_state = self.parser_state | flag
end

function Parser:clear_state(flag)
  self.parser_state = self.parser_state & ~flag
end

function Parser:in_state(flag)
  return self.parser_state & flag ~= 0
end

function Parser:save_parser_state()
  return SavedParserState:new(self.parser_state, self.dolbrace_state, self.pending_heredocs, self.ctx:copy_stack(), self.eof_token)
end

function Parser:restore_parser_state(saved)
  self.parser_state = saved.parser_state
  self.dolbrace_state = saved.dolbrace_state
  self.eof_token = saved.eof_token
  self.ctx:restore_from(saved.ctx_stack)
end

function Parser:record_token(tok)
  self.token_history = {tok, self.token_history[0 + 1], self.token_history[1 + 1], self.token_history[2 + 1]}
end

function Parser:update_dolbrace_for_op(op, has_param)
  local first_char
  if self.dolbrace_state == DOLBRACESTATE_NONE then
    return
  end
  if op == "" or #op == 0 then
    return
  end
  first_char = string.sub(op, 0 + 1, 0 + 1)
  if self.dolbrace_state == DOLBRACESTATE_PARAM and has_param then
    if ((string.find("%#^,", first_char, 1, true) ~= nil)) then
      self.dolbrace_state = DOLBRACESTATE_QUOTE
      return
    end
    if first_char == "/" then
      self.dolbrace_state = DOLBRACESTATE_QUOTE2
      return
    end
  end
  if self.dolbrace_state == DOLBRACESTATE_PARAM then
    if ((string.find("#%^,~:-=?+/", first_char, 1, true) ~= nil)) then
      self.dolbrace_state = DOLBRACESTATE_OP
    end
  end
end

function Parser:sync_lexer()
  if (self.lexer.token_cache ~= nil) then
    if self.lexer.token_cache.pos ~= self.pos or self.lexer.cached_word_context ~= self.word_context or self.lexer.cached_at_command_start ~= self.at_command_start or self.lexer.cached_in_array_literal ~= self.in_array_literal or self.lexer.cached_in_assign_builtin ~= self.in_assign_builtin then
      self.lexer.token_cache = nil
    end
  end
  if self.lexer.pos ~= self.pos then
    self.lexer.pos = self.pos
  end
  self.lexer.eof_token = self.eof_token
  self.lexer.parser_state = self.parser_state
  self.lexer.last_read_token = self.token_history[0 + 1]
  self.lexer.word_context = self.word_context
  self.lexer.at_command_start = self.at_command_start
  self.lexer.in_array_literal = self.in_array_literal
  self.lexer.in_assign_builtin = self.in_assign_builtin
end

function Parser:sync_parser()
  self.pos = self.lexer.pos
end

function Parser:lex_peek_token()
  local result, saved_pos
  if (self.lexer.token_cache ~= nil) and self.lexer.token_cache.pos == self.pos and self.lexer.cached_word_context == self.word_context and self.lexer.cached_at_command_start == self.at_command_start and self.lexer.cached_in_array_literal == self.in_array_literal and self.lexer.cached_in_assign_builtin == self.in_assign_builtin then
    return self.lexer.token_cache
  end
  saved_pos = self.pos
  self:sync_lexer()
  result = self.lexer:peek_token()
  self.lexer.cached_word_context = self.word_context
  self.lexer.cached_at_command_start = self.at_command_start
  self.lexer.cached_in_array_literal = self.in_array_literal
  self.lexer.cached_in_assign_builtin = self.in_assign_builtin
  self.lexer.post_read_pos = self.lexer.pos
  self.pos = saved_pos
  return result
end

function Parser:lex_next_token()
  local tok
  if (self.lexer.token_cache ~= nil) and self.lexer.token_cache.pos == self.pos and self.lexer.cached_word_context == self.word_context and self.lexer.cached_at_command_start == self.at_command_start and self.lexer.cached_in_array_literal == self.in_array_literal and self.lexer.cached_in_assign_builtin == self.in_assign_builtin then
    tok = self.lexer:next_token()
    self.pos = self.lexer.post_read_pos
    self.lexer.pos = self.lexer.post_read_pos
  else
    self:sync_lexer()
    tok = self.lexer:next_token()
    self.lexer.cached_word_context = self.word_context
    self.lexer.cached_at_command_start = self.at_command_start
    self.lexer.cached_in_array_literal = self.in_array_literal
    self.lexer.cached_in_assign_builtin = self.in_assign_builtin
    self:sync_parser()
  end
  self:record_token(tok)
  return tok
end

function Parser:lex_skip_blanks()
  self:sync_lexer()
  self.lexer:skip_blanks()
  self:sync_parser()
end

function Parser:lex_skip_comment()
  local result
  self:sync_lexer()
  result = self.lexer:skip_comment()
  self:sync_parser()
  return result
end

function Parser:lex_is_command_terminator()
  local t, tok
  tok = self:lex_peek_token()
  t = tok.type_
  return t == TOKENTYPE_EOF or t == TOKENTYPE_NEWLINE or t == TOKENTYPE_PIPE or t == TOKENTYPE_SEMI or t == TOKENTYPE_LPAREN or t == TOKENTYPE_RPAREN or t == TOKENTYPE_AMP
end

function Parser:lex_peek_operator()
  local t, tok
  tok = self:lex_peek_token()
  t = tok.type_
  if t >= TOKENTYPE_SEMI and t <= TOKENTYPE_GREATER or t >= TOKENTYPE_AND_AND and t <= TOKENTYPE_PIPE_AMP then
    return {t, tok.value}
  end
  return {0, ""}
end

function Parser:lex_peek_reserved_word()
  local tok, word
  tok = self:lex_peek_token()
  if tok.type_ ~= TOKENTYPE_WORD then
    return ""
  end
  word = tok.value
  if (string.sub(word, -#"\\\n") == "\\\n") then
    word = string.sub(word, 1, #word - 2)
  end
  if (_set_contains(RESERVED_WORDS, word)) or word == "{" or word == "}" or word == "[[" or word == "]]" or word == "!" or word == "time" then
    return word
  end
  return ""
end

function Parser:lex_is_at_reserved_word(word)
  local reserved
  reserved = self:lex_peek_reserved_word()
  return reserved == word
end

function Parser:lex_consume_word(expected)
  local tok, word
  tok = self:lex_peek_token()
  if tok.type_ ~= TOKENTYPE_WORD then
    return false
  end
  word = tok.value
  if (string.sub(word, -#"\\\n") == "\\\n") then
    word = string.sub(word, 1, #word - 2)
  end
  if word == expected then
    self:lex_next_token()
    return true
  end
  return false
end

function Parser:lex_peek_case_terminator()
  local t, tok
  tok = self:lex_peek_token()
  t = tok.type_
  if t == TOKENTYPE_SEMI_SEMI then
    return ";;"
  end
  if t == TOKENTYPE_SEMI_AMP then
    return ";&"
  end
  if t == TOKENTYPE_SEMI_SEMI_AMP then
    return ";;&"
  end
  return ""
end

function Parser:at_end()
  return self.pos >= self.length
end

function Parser:peek()
  if self:at_end() then
    return ""
  end
  return string.sub(self.source, self.pos + 1, self.pos + 1)
end

function Parser:advance()
  local ch
  if self:at_end() then
    return ""
  end
  ch = string.sub(self.source, self.pos + 1, self.pos + 1)
  self.pos = self.pos + 1
  return ch
end

function Parser:peek_at(offset)
  local pos
  pos = self.pos + offset
  if pos < 0 or pos >= self.length then
    return ""
  end
  return string.sub(self.source, pos + 1, pos + 1)
end

function Parser:lookahead(n)
  return substring(self.source, self.pos, self.pos + n)
end

function Parser:is_bang_followed_by_procsub()
  local next_char
  if self.pos + 2 >= self.length then
    return false
  end
  next_char = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
  if next_char ~= ">" and next_char ~= "<" then
    return false
  end
  return string.sub(self.source, self.pos + 2 + 1, self.pos + 2 + 1) == "("
end

function Parser:skip_whitespace()
  local ch
  while not self:at_end() do
    self:lex_skip_blanks()
    if self:at_end() then
      break
    end
    ch = self:peek()
    if ch == "#" then
      self:lex_skip_comment()
    elseif ch == "\\" and self:peek_at(1) == "\n" then
      self:advance()
      self:advance()
    else
      break
    end
  end
end

function Parser:skip_whitespace_and_newlines()
  local ch
  while not self:at_end() do
    ch = self:peek()
    if is_whitespace(ch) then
      self:advance()
      if ch == "\n" then
        self:gather_heredoc_bodies()
        if self.cmdsub_heredoc_end ~= -1 and self.cmdsub_heredoc_end > self.pos then
          self.pos = self.cmdsub_heredoc_end
          self.cmdsub_heredoc_end = -1
        end
      end
    elseif ch == "#" then
      while not self:at_end() and self:peek() ~= "\n" do
        self:advance()
      end
    elseif ch == "\\" and self:peek_at(1) == "\n" then
      self:advance()
      self:advance()
    else
      break
    end
  end
end

function Parser:at_list_terminating_bracket()
  local ch, next_pos
  if self:at_end() then
    return false
  end
  ch = self:peek()
  if self.eof_token ~= "" and ch == self.eof_token then
    return true
  end
  if ch == ")" then
    return true
  end
  if ch == "}" then
    next_pos = self.pos + 1
    if next_pos >= self.length then
      return true
    end
    return is_word_end_context(string.sub(self.source, next_pos + 1, next_pos + 1))
  end
  return false
end

function Parser:at_eof_token()
  local tok
  if self.eof_token == "" then
    return false
  end
  tok = self:lex_peek_token()
  if self.eof_token == ")" then
    return tok.type_ == TOKENTYPE_RPAREN
  end
  if self.eof_token == "}" then
    return tok.type_ == TOKENTYPE_WORD and tok.value == "}"
  end
  return false
end

function Parser:collect_redirects()
  local redirect, redirects
  redirects = {}
  while true do
    self:skip_whitespace()
    redirect = self:parse_redirect()
    if (redirect == nil) then
      break
    end
    ;(function() table.insert(redirects, redirect); return redirects end)()
  end
  return ((#(redirects) > 0) and redirects or nil)
end

function Parser:parse_loop_body(context)
  local body, brace
  if self:peek() == "{" then
    brace = self:parse_brace_group()
    if (brace == nil) then
      error({ParseError = true, message = string.format("Expected brace group body in %s", context), pos = self:lex_peek_token().pos})
    end
    return brace.body
  end
  if self:lex_consume_word("do") then
    body = self:parse_list_until({["done"] = true})
    if (body == nil) then
      error({ParseError = true, message = "Expected commands after 'do'", pos = self:lex_peek_token().pos})
    end
    self:skip_whitespace_and_newlines()
    if not self:lex_consume_word("done") then
      error({ParseError = true, message = string.format("Expected 'done' to close %s", context), pos = self:lex_peek_token().pos})
    end
    return body
  end
  error({ParseError = true, message = string.format("Expected 'do' or '{' in %s", context), pos = self:lex_peek_token().pos})
end

function Parser:peek_word()
  local ch, chars, saved_pos, word
  saved_pos = self.pos
  self:skip_whitespace()
  if self:at_end() or is_metachar(self:peek()) then
    self.pos = saved_pos
    return ""
  end
  chars = {}
  while not self:at_end() and not is_metachar(self:peek()) do
    ch = self:peek()
    if is_quote(ch) then
      break
    end
    if ch == "\\" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "\n" then
      break
    end
    if ch == "\\" and self.pos + 1 < self.length then
      ;(function() table.insert(chars, self:advance()); return chars end)()
      ;(function() table.insert(chars, self:advance()); return chars end)()
      goto continue
    end
    ;(function() table.insert(chars, self:advance()); return chars end)()
    ::continue::
  end
  if (#(chars) > 0) then
    word = table.concat(chars, "")
  else
    word = ""
  end
  self.pos = saved_pos
  return word
end

function Parser:consume_word(expected)
  local has_leading_brace, keyword_word, saved_pos, word
  saved_pos = self.pos
  self:skip_whitespace()
  word = self:peek_word()
  keyword_word = word
  has_leading_brace = false
  if word ~= "" and self.in_process_sub and #word > 1 and string.sub(word, 0 + 1, 0 + 1) == "}" then
    keyword_word = string.sub(word, (1) + 1, #word)
    has_leading_brace = true
  end
  if keyword_word ~= expected then
    self.pos = saved_pos
    return false
  end
  self:skip_whitespace()
  if has_leading_brace then
    self:advance()
  end
  for _ = 1, #expected do
    self:advance()
  end
  while self:peek() == "\\" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "\n" do
    self:advance()
    self:advance()
  end
  return true
end

function Parser:is_word_terminator(ctx, ch, bracket_depth, paren_depth)
  self:sync_lexer()
  return self.lexer:is_word_terminator(ctx, ch, bracket_depth, paren_depth)
end

function Parser:scan_double_quote(chars, parts, start, handle_line_continuation)
  local c, next_c
  ;(function() table.insert(chars, "\""); return chars end)()
  while not self:at_end() and self:peek() ~= "\"" do
    c = self:peek()
    if c == "\\" and self.pos + 1 < self.length then
      next_c = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
      if handle_line_continuation and next_c == "\n" then
        self:advance()
        self:advance()
      else
        ;(function() table.insert(chars, self:advance()); return chars end)()
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
    elseif c == "$" then
      if not self:parse_dollar_expansion(chars, parts, true) then
        ;(function() table.insert(chars, self:advance()); return chars end)()
      end
    else
      ;(function() table.insert(chars, self:advance()); return chars end)()
    end
  end
  if self:at_end() then
    error({ParseError = true, message = "Unterminated double quote", pos = start})
  end
  ;(function() table.insert(chars, self:advance()); return chars end)()
end

function Parser:parse_dollar_expansion(chars, parts, in_dquote)
  local result0, result1
  if self.pos + 2 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" and string.sub(self.source, self.pos + 2 + 1, self.pos + 2 + 1) == "(" then
    result0, result1 = table.unpack(self:parse_arithmetic_expansion())
    if (result0 ~= nil) then
      ;(function() table.insert(parts, result0); return parts end)()
      ;(function() table.insert(chars, result1); return chars end)()
      return true
    end
    result0, result1 = table.unpack(self:parse_command_substitution())
    if (result0 ~= nil) then
      ;(function() table.insert(parts, result0); return parts end)()
      ;(function() table.insert(chars, result1); return chars end)()
      return true
    end
    return false
  end
  if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "[" then
    result0, result1 = table.unpack(self:parse_deprecated_arithmetic())
    if (result0 ~= nil) then
      ;(function() table.insert(parts, result0); return parts end)()
      ;(function() table.insert(chars, result1); return chars end)()
      return true
    end
    return false
  end
  if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
    result0, result1 = table.unpack(self:parse_command_substitution())
    if (result0 ~= nil) then
      ;(function() table.insert(parts, result0); return parts end)()
      ;(function() table.insert(chars, result1); return chars end)()
      return true
    end
    return false
  end
  result0, result1 = table.unpack(self:parse_param_expansion(in_dquote))
  if (result0 ~= nil) then
    ;(function() table.insert(parts, result0); return parts end)()
    ;(function() table.insert(chars, result1); return chars end)()
    return true
  end
  return false
end

function Parser:parse_word_internal(ctx, at_command_start, in_array_literal)
  self.word_context = ctx
  return self:parse_word(at_command_start, in_array_literal, false)
end

function Parser:parse_word(at_command_start, in_array_literal, in_assign_builtin)
  local tok
  self:skip_whitespace()
  if self:at_end() then
    return nil
  end
  self.at_command_start = at_command_start
  self.in_array_literal = in_array_literal
  self.in_assign_builtin = in_assign_builtin
  tok = self:lex_peek_token()
  if tok.type_ ~= TOKENTYPE_WORD then
    self.at_command_start = false
    self.in_array_literal = false
    self.in_assign_builtin = false
    return nil
  end
  self:lex_next_token()
  self.at_command_start = false
  self.in_array_literal = false
  self.in_assign_builtin = false
  return tok.word
end

function Parser:parse_command_substitution()
  local cmd, saved, start, text, text_end
  if self:at_end() or self:peek() ~= "$" then
    return {nil, ""}
  end
  start = self.pos
  self:advance()
  if self:at_end() or self:peek() ~= "(" then
    self.pos = start
    return {nil, ""}
  end
  self:advance()
  saved = self:save_parser_state()
  self:set_state(PARSERSTATEFLAGS_PST_CMDSUBST | PARSERSTATEFLAGS_PST_EOFTOKEN)
  self.eof_token = ")"
  cmd = self:parse_list(true)
  if (cmd == nil) then
    cmd = Empty:new("empty")
  end
  self:skip_whitespace_and_newlines()
  if self:at_end() or self:peek() ~= ")" then
    self:restore_parser_state(saved)
    self.pos = start
    return {nil, ""}
  end
  self:advance()
  text_end = self.pos
  text = substring(self.source, start, text_end)
  self:restore_parser_state(saved)
  return {CommandSubstitution:new(cmd, nil, "cmdsub"), text}
end

function Parser:parse_funsub(start)
  local cmd, saved, text
  self:sync_parser()
  if not self:at_end() and self:peek() == "|" then
    self:advance()
  end
  saved = self:save_parser_state()
  self:set_state(PARSERSTATEFLAGS_PST_CMDSUBST | PARSERSTATEFLAGS_PST_EOFTOKEN)
  self.eof_token = "}"
  cmd = self:parse_list(true)
  if (cmd == nil) then
    cmd = Empty:new("empty")
  end
  self:skip_whitespace_and_newlines()
  if self:at_end() or self:peek() ~= "}" then
    self:restore_parser_state(saved)
    error({MatchedPairError = true, message = "unexpected EOF looking for `}'", pos = start})
  end
  self:advance()
  text = substring(self.source, start, self.pos)
  self:restore_parser_state(saved)
  self:sync_lexer()
  return {CommandSubstitution:new(cmd, true, "cmdsub"), text}
end

function Parser:is_assignment_word(word)
  return assignment(word.value, 0) ~= -1
end

function Parser:parse_backtick_substitution()
  local c, ch, check_line, closing, cmd, content, content_chars, current_heredoc_delim, current_heredoc_strip, dch, delimiter, delimiter_chars, end_pos, esc, escaped, heredoc_end, heredoc_start, i, in_heredoc_body, line, line_end, line_start, next_c, pending_heredocs, quote, start, strip_tabs, sub_parser, tabs_stripped, text, text_chars
  if self:at_end() or self:peek() ~= "`" then
    return {nil, ""}
  end
  start = self.pos
  self:advance()
  content_chars = {}
  text_chars = {"`"}
  pending_heredocs = {}
  in_heredoc_body = false
  current_heredoc_delim = ""
  current_heredoc_strip = false
  while not self:at_end() and (in_heredoc_body or self:peek() ~= "`") do
    if in_heredoc_body then
      line_start = self.pos
      line_end = line_start
      while line_end < self.length and string.sub(self.source, line_end + 1, line_end + 1) ~= "\n" do
        line_end = line_end + 1
      end
      line = substring(self.source, line_start, line_end)
      check_line = (current_heredoc_strip and (string.gsub(line, '^[' .. "\t" .. ']+', '')) or line)
      if check_line == current_heredoc_delim then
        for _ = 1, #line do
          local ch = string.sub(line, _, _)
          ;(function() table.insert(content_chars, ch); return content_chars end)()
          ;(function() table.insert(text_chars, ch); return text_chars end)()
        end
        self.pos = line_end
        if self.pos < self.length and string.sub(self.source, self.pos + 1, self.pos + 1) == "\n" then
          ;(function() table.insert(content_chars, "\n"); return content_chars end)()
          ;(function() table.insert(text_chars, "\n"); return text_chars end)()
          self:advance()
        end
        in_heredoc_body = false
        if #pending_heredocs > 0 then
          current_heredoc_delim, current_heredoc_strip = table.unpack(table.remove(pending_heredocs, 1))
          in_heredoc_body = true
        end
      elseif (string.sub(check_line, 1, #current_heredoc_delim) == current_heredoc_delim) and #check_line > #current_heredoc_delim then
        tabs_stripped = #line - #check_line
        end_pos = tabs_stripped + #current_heredoc_delim
        for i = 0, end_pos - 1 do
          ;(function() table.insert(content_chars, string.sub(line, i + 1, i + 1)); return content_chars end)()
          ;(function() table.insert(text_chars, string.sub(line, i + 1, i + 1)); return text_chars end)()
        end
        self.pos = line_start + end_pos
        in_heredoc_body = false
        if #pending_heredocs > 0 then
          current_heredoc_delim, current_heredoc_strip = table.unpack(table.remove(pending_heredocs, 1))
          in_heredoc_body = true
        end
      else
        for _ = 1, #line do
          local ch = string.sub(line, _, _)
          ;(function() table.insert(content_chars, ch); return content_chars end)()
          ;(function() table.insert(text_chars, ch); return text_chars end)()
        end
        self.pos = line_end
        if self.pos < self.length and string.sub(self.source, self.pos + 1, self.pos + 1) == "\n" then
          ;(function() table.insert(content_chars, "\n"); return content_chars end)()
          ;(function() table.insert(text_chars, "\n"); return text_chars end)()
          self:advance()
        end
      end
      goto continue
    end
    c = self:peek()
    if c == "\\" and self.pos + 1 < self.length then
      next_c = string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)
      if next_c == "\n" then
        self:advance()
        self:advance()
      elseif is_escape_char_in_backtick(next_c) then
        self:advance()
        escaped = self:advance()
        ;(function() table.insert(content_chars, escaped); return content_chars end)()
        ;(function() table.insert(text_chars, "\\"); return text_chars end)()
        ;(function() table.insert(text_chars, escaped); return text_chars end)()
      else
        ch = self:advance()
        ;(function() table.insert(content_chars, ch); return content_chars end)()
        ;(function() table.insert(text_chars, ch); return text_chars end)()
      end
      goto continue
    end
    if c == "<" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "<" then
      if self.pos + 2 < self.length and string.sub(self.source, self.pos + 2 + 1, self.pos + 2 + 1) == "<" then
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
        ;(function() table.insert(text_chars, "<"); return text_chars end)()
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
        ;(function() table.insert(text_chars, "<"); return text_chars end)()
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
        ;(function() table.insert(text_chars, "<"); return text_chars end)()
        while not self:at_end() and is_whitespace_no_newline(self:peek()) do
          ch = self:advance()
          ;(function() table.insert(content_chars, ch); return content_chars end)()
          ;(function() table.insert(text_chars, ch); return text_chars end)()
        end
        while not self:at_end() and not is_whitespace(self:peek()) and ((not (string.find("()", self:peek(), 1, true) ~= nil))) do
          if self:peek() == "\\" and self.pos + 1 < self.length then
            ch = self:advance()
            ;(function() table.insert(content_chars, ch); return content_chars end)()
            ;(function() table.insert(text_chars, ch); return text_chars end)()
            ch = self:advance()
            ;(function() table.insert(content_chars, ch); return content_chars end)()
            ;(function() table.insert(text_chars, ch); return text_chars end)()
          elseif ((string.find("\"'", self:peek(), 1, true) ~= nil)) then
            quote = self:peek()
            ch = self:advance()
            ;(function() table.insert(content_chars, ch); return content_chars end)()
            ;(function() table.insert(text_chars, ch); return text_chars end)()
            while not self:at_end() and self:peek() ~= quote do
              if quote == "\"" and self:peek() == "\\" then
                ch = self:advance()
                ;(function() table.insert(content_chars, ch); return content_chars end)()
                ;(function() table.insert(text_chars, ch); return text_chars end)()
              end
              ch = self:advance()
              ;(function() table.insert(content_chars, ch); return content_chars end)()
              ;(function() table.insert(text_chars, ch); return text_chars end)()
            end
            if not self:at_end() then
              ch = self:advance()
              ;(function() table.insert(content_chars, ch); return content_chars end)()
              ;(function() table.insert(text_chars, ch); return text_chars end)()
            end
          else
            ch = self:advance()
            ;(function() table.insert(content_chars, ch); return content_chars end)()
            ;(function() table.insert(text_chars, ch); return text_chars end)()
          end
        end
        goto continue
      end
      ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      ;(function() table.insert(text_chars, "<"); return text_chars end)()
      ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
      ;(function() table.insert(text_chars, "<"); return text_chars end)()
      strip_tabs = false
      if not self:at_end() and self:peek() == "-" then
        strip_tabs = true
        ;(function() table.insert(content_chars, self:advance()); return content_chars end)()
        ;(function() table.insert(text_chars, "-"); return text_chars end)()
      end
      while not self:at_end() and is_whitespace_no_newline(self:peek()) do
        ch = self:advance()
        ;(function() table.insert(content_chars, ch); return content_chars end)()
        ;(function() table.insert(text_chars, ch); return text_chars end)()
      end
      delimiter_chars = {}
      if not self:at_end() then
        ch = self:peek()
        if is_quote(ch) then
          quote = self:advance()
          ;(function() table.insert(content_chars, quote); return content_chars end)()
          ;(function() table.insert(text_chars, quote); return text_chars end)()
          while not self:at_end() and self:peek() ~= quote do
            dch = self:advance()
            ;(function() table.insert(content_chars, dch); return content_chars end)()
            ;(function() table.insert(text_chars, dch); return text_chars end)()
            ;(function() table.insert(delimiter_chars, dch); return delimiter_chars end)()
          end
          if not self:at_end() then
            closing = self:advance()
            ;(function() table.insert(content_chars, closing); return content_chars end)()
            ;(function() table.insert(text_chars, closing); return text_chars end)()
          end
        elseif ch == "\\" then
          esc = self:advance()
          ;(function() table.insert(content_chars, esc); return content_chars end)()
          ;(function() table.insert(text_chars, esc); return text_chars end)()
          if not self:at_end() then
            dch = self:advance()
            ;(function() table.insert(content_chars, dch); return content_chars end)()
            ;(function() table.insert(text_chars, dch); return text_chars end)()
            ;(function() table.insert(delimiter_chars, dch); return delimiter_chars end)()
          end
          while not self:at_end() and not is_metachar(self:peek()) do
            dch = self:advance()
            ;(function() table.insert(content_chars, dch); return content_chars end)()
            ;(function() table.insert(text_chars, dch); return text_chars end)()
            ;(function() table.insert(delimiter_chars, dch); return delimiter_chars end)()
          end
        else
          while not self:at_end() and not is_metachar(self:peek()) and self:peek() ~= "`" do
            ch = self:peek()
            if is_quote(ch) then
              quote = self:advance()
              ;(function() table.insert(content_chars, quote); return content_chars end)()
              ;(function() table.insert(text_chars, quote); return text_chars end)()
              while not self:at_end() and self:peek() ~= quote do
                dch = self:advance()
                ;(function() table.insert(content_chars, dch); return content_chars end)()
                ;(function() table.insert(text_chars, dch); return text_chars end)()
                ;(function() table.insert(delimiter_chars, dch); return delimiter_chars end)()
              end
              if not self:at_end() then
                closing = self:advance()
                ;(function() table.insert(content_chars, closing); return content_chars end)()
                ;(function() table.insert(text_chars, closing); return text_chars end)()
              end
            elseif ch == "\\" then
              esc = self:advance()
              ;(function() table.insert(content_chars, esc); return content_chars end)()
              ;(function() table.insert(text_chars, esc); return text_chars end)()
              if not self:at_end() then
                dch = self:advance()
                ;(function() table.insert(content_chars, dch); return content_chars end)()
                ;(function() table.insert(text_chars, dch); return text_chars end)()
                ;(function() table.insert(delimiter_chars, dch); return delimiter_chars end)()
              end
            else
              dch = self:advance()
              ;(function() table.insert(content_chars, dch); return content_chars end)()
              ;(function() table.insert(text_chars, dch); return text_chars end)()
              ;(function() table.insert(delimiter_chars, dch); return delimiter_chars end)()
            end
          end
        end
      end
      delimiter = table.concat(delimiter_chars, "")
      if (delimiter ~= nil and #(delimiter) > 0) then
        ;(function() table.insert(pending_heredocs, {delimiter, strip_tabs}); return pending_heredocs end)()
      end
      goto continue
    end
    if c == "\n" then
      ch = self:advance()
      ;(function() table.insert(content_chars, ch); return content_chars end)()
      ;(function() table.insert(text_chars, ch); return text_chars end)()
      if #pending_heredocs > 0 then
        current_heredoc_delim, current_heredoc_strip = table.unpack(table.remove(pending_heredocs, 1))
        in_heredoc_body = true
      end
      goto continue
    end
    ch = self:advance()
    ;(function() table.insert(content_chars, ch); return content_chars end)()
    ;(function() table.insert(text_chars, ch); return text_chars end)()
    ::continue::
  end
  if self:at_end() then
    error({ParseError = true, message = "Unterminated backtick", pos = start})
  end
  self:advance()
  ;(function() table.insert(text_chars, "`"); return text_chars end)()
  text = table.concat(text_chars, "")
  content = table.concat(content_chars, "")
  if #pending_heredocs > 0 then
    heredoc_start, heredoc_end = table.unpack(find_heredoc_content_end(self.source, self.pos, pending_heredocs))
    if heredoc_end > heredoc_start then
      content = content .. substring(self.source, heredoc_start, heredoc_end)
      if self.cmdsub_heredoc_end == -1 then
        self.cmdsub_heredoc_end = heredoc_end
      else
        self.cmdsub_heredoc_end = (self.cmdsub_heredoc_end > heredoc_end and self.cmdsub_heredoc_end or heredoc_end)
      end
    end
  end
  sub_parser = new_parser(content, false, self.extglob)
  cmd = sub_parser:parse_list(true)
  if (cmd == nil) then
    cmd = Empty:new("empty")
  end
  return {CommandSubstitution:new(cmd, nil, "cmdsub"), text}
end

function Parser:parse_process_substitution()
  local cmd, content_start_char, direction, e, old_in_process_sub, saved, start, text, text_end
  if self:at_end() or not is_redirect_char(self:peek()) then
    return {nil, ""}
  end
  start = self.pos
  direction = self:advance()
  if self:at_end() or self:peek() ~= "(" then
    self.pos = start
    return {nil, ""}
  end
  self:advance()
  saved = self:save_parser_state()
  old_in_process_sub = self.in_process_sub
  self.in_process_sub = true
  self:set_state(PARSERSTATEFLAGS_PST_EOFTOKEN)
  self.eof_token = ")"
  local _ok, _err = pcall(function()
    cmd = self:parse_list(true)
    if (cmd == nil) then
      cmd = Empty:new("empty")
    end
    self:skip_whitespace_and_newlines()
    if self:at_end() or self:peek() ~= ")" then
      error({ParseError = true, message = "Invalid process substitution", pos = start})
    end
    self:advance()
    text_end = self.pos
    text = substring(self.source, start, text_end)
    text = strip_line_continuations_comment_aware(text)
    self:restore_parser_state(saved)
    self.in_process_sub = old_in_process_sub
    return {ProcessSubstitution:new(direction, cmd, "procsub"), text}
  end)
  if not _ok then
    local e = _err
    self:restore_parser_state(saved)
    self.in_process_sub = old_in_process_sub
    content_start_char = (start + 2 < self.length and string.sub(self.source, start + 2 + 1, start + 2 + 1) or "")
    if ((string.find(" \t\n", content_start_char, 1, true) ~= nil)) then
      error(e)
    end
    self.pos = start + 2
    self.lexer.pos = self.pos
    self.lexer:parse_matched_pair("(", ")", 0, false)
    self.pos = self.lexer.pos
    text = substring(self.source, start, self.pos)
    text = strip_line_continuations_comment_aware(text)
    return {nil, text}
  end
  if _ok then return _err end
end

function Parser:parse_array_literal()
  local elements, start, text, word
  if self:at_end() or self:peek() ~= "(" then
    return {nil, ""}
  end
  start = self.pos
  self:advance()
  self:set_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
  elements = {}
  while true do
    self:skip_whitespace_and_newlines()
    if self:at_end() then
      self:clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
      error({ParseError = true, message = "Unterminated array literal", pos = start})
    end
    if self:peek() == ")" then
      break
    end
    word = self:parse_word(false, true, false)
    if (word == nil) then
      if self:peek() == ")" then
        break
      end
      self:clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
      error({ParseError = true, message = "Expected word in array literal", pos = self.pos})
    end
    ;(function() table.insert(elements, word); return elements end)()
  end
  if self:at_end() or self:peek() ~= ")" then
    self:clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
    error({ParseError = true, message = "Expected ) to close array literal", pos = self.pos})
  end
  self:advance()
  text = substring(self.source, start, self.pos)
  self:clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN)
  return {Array:new(elements, "array"), text}
end

function Parser:parse_arithmetic_expansion()
  local c, content, content_start, depth, expr, first_close_pos, start, text
  if self:at_end() or self:peek() ~= "$" then
    return {nil, ""}
  end
  start = self.pos
  if self.pos + 2 >= self.length or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) ~= "(" or string.sub(self.source, self.pos + 2 + 1, self.pos + 2 + 1) ~= "(" then
    return {nil, ""}
  end
  self:advance()
  self:advance()
  self:advance()
  content_start = self.pos
  depth = 2
  first_close_pos = -1
  while not self:at_end() and depth > 0 do
    c = self:peek()
    if c == "'" then
      self:advance()
      while not self:at_end() and self:peek() ~= "'" do
        self:advance()
      end
      if not self:at_end() then
        self:advance()
      end
    elseif c == "\"" then
      self:advance()
      while not self:at_end() do
        if self:peek() == "\\" and self.pos + 1 < self.length then
          self:advance()
          self:advance()
        elseif self:peek() == "\"" then
          self:advance()
          break
        else
          self:advance()
        end
      end
    elseif c == "\\" and self.pos + 1 < self.length then
      self:advance()
      self:advance()
    elseif c == "(" then
      depth = depth + 1
      self:advance()
    elseif c == ")" then
      if depth == 2 then
        first_close_pos = self.pos
      end
      depth = depth - 1
      if depth == 0 then
        break
      end
      self:advance()
    else
      if depth == 1 then
        first_close_pos = -1
      end
      self:advance()
    end
  end
  if depth ~= 0 then
    if self:at_end() then
      error({MatchedPairError = true, message = "unexpected EOF looking for `))'", pos = start})
    end
    self.pos = start
    return {nil, ""}
  end
  if first_close_pos ~= -1 then
    content = substring(self.source, content_start, first_close_pos)
  else
    content = substring(self.source, content_start, self.pos)
  end
  self:advance()
  text = substring(self.source, start, self.pos)
  local _ok, _err = pcall(function()
    expr = self:parse_arith_expr(content)
  end)
  if not _ok then
    self.pos = start
    return {nil, ""}
  end
  return {ArithmeticExpansion:new(expr, "arith"), text}
end

function Parser:parse_arith_expr(content)
  local result, saved_arith_len, saved_arith_pos, saved_arith_src, saved_parser_state
  saved_arith_src = self.arith_src
  saved_arith_pos = self.arith_pos
  saved_arith_len = self.arith_len
  saved_parser_state = self.parser_state
  self:set_state(PARSERSTATEFLAGS_PST_ARITH)
  self.arith_src = content
  self.arith_pos = 0
  self.arith_len = #content
  self:arith_skip_ws()
  if self:arith_at_end() then
    result = nil
  else
    result = self:arith_parse_comma()
  end
  self.parser_state = saved_parser_state
  if saved_arith_src ~= "" then
    self.arith_src = saved_arith_src
    self.arith_pos = saved_arith_pos
    self.arith_len = saved_arith_len
  end
  return result
end

function Parser:arith_at_end()
  return self.arith_pos >= self.arith_len
end

function Parser:arith_peek(offset)
  local pos
  pos = self.arith_pos + offset
  if pos >= self.arith_len then
    return ""
  end
  return string.sub(self.arith_src, pos + 1, pos + 1)
end

function Parser:arith_advance()
  local c
  if self:arith_at_end() then
    return ""
  end
  c = string.sub(self.arith_src, self.arith_pos + 1, self.arith_pos + 1)
  self.arith_pos = self.arith_pos + 1
  return c
end

function Parser:arith_skip_ws()
  local c
  while not self:arith_at_end() do
    c = string.sub(self.arith_src, self.arith_pos + 1, self.arith_pos + 1)
    if is_whitespace(c) then
      self.arith_pos = self.arith_pos + 1
    elseif c == "\\" and self.arith_pos + 1 < self.arith_len and string.sub(self.arith_src, self.arith_pos + 1 + 1, self.arith_pos + 1 + 1) == "\n" then
      self.arith_pos = self.arith_pos + 2
    else
      break
    end
  end
end

function Parser:arith_match(s)
  return starts_with_at(self.arith_src, self.arith_pos, s)
end

function Parser:arith_consume(s)
  if self:arith_match(s) then
    self.arith_pos = self.arith_pos + #s
    return true
  end
  return false
end

function Parser:arith_parse_comma()
  local left, right
  left = self:arith_parse_assign()
  while true do
    self:arith_skip_ws()
    if self:arith_consume(",") then
      self:arith_skip_ws()
      right = self:arith_parse_assign()
      left = ArithComma:new(left, right, "comma")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_assign()
  local assign_ops, left, op, right
  left = self:arith_parse_ternary()
  self:arith_skip_ws()
  assign_ops = {"<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="}
  for _, op in ipairs(assign_ops) do
    if self:arith_match(op) then
      if op == "=" and self:arith_peek(1) == "=" then
        break
      end
      self:arith_consume(op)
      self:arith_skip_ws()
      right = self:arith_parse_assign()
      return ArithAssign:new(op, left, right, "assign")
    end
  end
  return left
end

function Parser:arith_parse_ternary()
  local cond, if_false, if_true
  cond = self:arith_parse_logical_or()
  self:arith_skip_ws()
  if self:arith_consume("?") then
    self:arith_skip_ws()
    if self:arith_match(":") then
      if_true = nil
    else
      if_true = self:arith_parse_assign()
    end
    self:arith_skip_ws()
    if self:arith_consume(":") then
      self:arith_skip_ws()
      if self:arith_at_end() or self:arith_peek(0) == ")" then
        if_false = nil
      else
        if_false = self:arith_parse_ternary()
      end
    else
      if_false = nil
    end
    return ArithTernary:new(cond, if_true, if_false, "ternary")
  end
  return cond
end

function Parser:arith_parse_left_assoc(ops, parsefn)
  local left, matched, op
  left = parsefn()
  while true do
    self:arith_skip_ws()
    matched = false
    for _, op in ipairs(ops) do
      if self:arith_match(op) then
        self:arith_consume(op)
        self:arith_skip_ws()
        left = ArithBinaryOp:new(op, left, parsefn(), "binary-op")
        matched = true
        break
      end
    end
    if not matched then
      break
    end
  end
  return left
end

function Parser:arith_parse_logical_or()
  return self:arith_parse_left_assoc({"||"}, function(...) return self:arith_parse_logical_and(...) end)
end

function Parser:arith_parse_logical_and()
  return self:arith_parse_left_assoc({"&&"}, function(...) return self:arith_parse_bitwise_or(...) end)
end

function Parser:arith_parse_bitwise_or()
  local left, right
  left = self:arith_parse_bitwise_xor()
  while true do
    self:arith_skip_ws()
    if self:arith_peek(0) == "|" and self:arith_peek(1) ~= "|" and self:arith_peek(1) ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_bitwise_xor()
      left = ArithBinaryOp:new("|", left, right, "binary-op")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_bitwise_xor()
  local left, right
  left = self:arith_parse_bitwise_and()
  while true do
    self:arith_skip_ws()
    if self:arith_peek(0) == "^" and self:arith_peek(1) ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_bitwise_and()
      left = ArithBinaryOp:new("^", left, right, "binary-op")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_bitwise_and()
  local left, right
  left = self:arith_parse_equality()
  while true do
    self:arith_skip_ws()
    if self:arith_peek(0) == "&" and self:arith_peek(1) ~= "&" and self:arith_peek(1) ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_equality()
      left = ArithBinaryOp:new("&", left, right, "binary-op")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_equality()
  return self:arith_parse_left_assoc({"==", "!="}, function(...) return self:arith_parse_comparison(...) end)
end

function Parser:arith_parse_comparison()
  local left, right
  left = self:arith_parse_shift()
  while true do
    self:arith_skip_ws()
    if self:arith_match("<=") then
      self:arith_consume("<=")
      self:arith_skip_ws()
      right = self:arith_parse_shift()
      left = ArithBinaryOp:new("<=", left, right, "binary-op")
    elseif self:arith_match(">=") then
      self:arith_consume(">=")
      self:arith_skip_ws()
      right = self:arith_parse_shift()
      left = ArithBinaryOp:new(">=", left, right, "binary-op")
    elseif self:arith_peek(0) == "<" and self:arith_peek(1) ~= "<" and self:arith_peek(1) ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_shift()
      left = ArithBinaryOp:new("<", left, right, "binary-op")
    elseif self:arith_peek(0) == ">" and self:arith_peek(1) ~= ">" and self:arith_peek(1) ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_shift()
      left = ArithBinaryOp:new(">", left, right, "binary-op")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_shift()
  local left, right
  left = self:arith_parse_additive()
  while true do
    self:arith_skip_ws()
    if self:arith_match("<<=") then
      break
    end
    if self:arith_match(">>=") then
      break
    end
    if self:arith_match("<<") then
      self:arith_consume("<<")
      self:arith_skip_ws()
      right = self:arith_parse_additive()
      left = ArithBinaryOp:new("<<", left, right, "binary-op")
    elseif self:arith_match(">>") then
      self:arith_consume(">>")
      self:arith_skip_ws()
      right = self:arith_parse_additive()
      left = ArithBinaryOp:new(">>", left, right, "binary-op")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_additive()
  local c, c2, left, right
  left = self:arith_parse_multiplicative()
  while true do
    self:arith_skip_ws()
    c = self:arith_peek(0)
    c2 = self:arith_peek(1)
    if c == "+" and c2 ~= "+" and c2 ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_multiplicative()
      left = ArithBinaryOp:new("+", left, right, "binary-op")
    elseif c == "-" and c2 ~= "-" and c2 ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_multiplicative()
      left = ArithBinaryOp:new("-", left, right, "binary-op")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_multiplicative()
  local c, c2, left, right
  left = self:arith_parse_exponentiation()
  while true do
    self:arith_skip_ws()
    c = self:arith_peek(0)
    c2 = self:arith_peek(1)
    if c == "*" and c2 ~= "*" and c2 ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_exponentiation()
      left = ArithBinaryOp:new("*", left, right, "binary-op")
    elseif c == "/" and c2 ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_exponentiation()
      left = ArithBinaryOp:new("/", left, right, "binary-op")
    elseif c == "%" and c2 ~= "=" then
      self:arith_advance()
      self:arith_skip_ws()
      right = self:arith_parse_exponentiation()
      left = ArithBinaryOp:new("%", left, right, "binary-op")
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_exponentiation()
  local left, right
  left = self:arith_parse_unary()
  self:arith_skip_ws()
  if self:arith_match("**") then
    self:arith_consume("**")
    self:arith_skip_ws()
    right = self:arith_parse_exponentiation()
    return ArithBinaryOp:new("**", left, right, "binary-op")
  end
  return left
end

function Parser:arith_parse_unary()
  local c, operand
  self:arith_skip_ws()
  if self:arith_match("++") then
    self:arith_consume("++")
    self:arith_skip_ws()
    operand = self:arith_parse_unary()
    return ArithPreIncr:new(operand, "pre-incr")
  end
  if self:arith_match("--") then
    self:arith_consume("--")
    self:arith_skip_ws()
    operand = self:arith_parse_unary()
    return ArithPreDecr:new(operand, "pre-decr")
  end
  c = self:arith_peek(0)
  if c == "!" then
    self:arith_advance()
    self:arith_skip_ws()
    operand = self:arith_parse_unary()
    return ArithUnaryOp:new("!", operand, "unary-op")
  end
  if c == "~" then
    self:arith_advance()
    self:arith_skip_ws()
    operand = self:arith_parse_unary()
    return ArithUnaryOp:new("~", operand, "unary-op")
  end
  if c == "+" and self:arith_peek(1) ~= "+" then
    self:arith_advance()
    self:arith_skip_ws()
    operand = self:arith_parse_unary()
    return ArithUnaryOp:new("+", operand, "unary-op")
  end
  if c == "-" and self:arith_peek(1) ~= "-" then
    self:arith_advance()
    self:arith_skip_ws()
    operand = self:arith_parse_unary()
    return ArithUnaryOp:new("-", operand, "unary-op")
  end
  return self:arith_parse_postfix()
end

function Parser:arith_parse_postfix()
  local index, left
  left = self:arith_parse_primary()
  while true do
    self:arith_skip_ws()
    if self:arith_match("++") then
      self:arith_consume("++")
      left = ArithPostIncr:new(left, "post-incr")
    elseif self:arith_match("--") then
      self:arith_consume("--")
      left = ArithPostDecr:new(left, "post-decr")
    elseif self:arith_peek(0) == "[" then
      if (type(left) == 'table' and getmetatable(left) == ArithVar) then
        local left = left
        self:arith_advance()
        self:arith_skip_ws()
        index = self:arith_parse_comma()
        self:arith_skip_ws()
        if not self:arith_consume("]") then
          error({ParseError = true, message = "Expected ']' in array subscript", pos = self.arith_pos})
        end
        left = ArithSubscript:new(left.name, index, "subscript")
      else
        break
      end
    else
      break
    end
  end
  return left
end

function Parser:arith_parse_primary()
  local c, escaped_char, expr
  self:arith_skip_ws()
  c = self:arith_peek(0)
  if c == "(" then
    self:arith_advance()
    self:arith_skip_ws()
    expr = self:arith_parse_comma()
    self:arith_skip_ws()
    if not self:arith_consume(")") then
      error({ParseError = true, message = "Expected ')' in arithmetic expression", pos = self.arith_pos})
    end
    return expr
  end
  if c == "#" and self:arith_peek(1) == "$" then
    self:arith_advance()
    return self:arith_parse_expansion()
  end
  if c == "$" then
    return self:arith_parse_expansion()
  end
  if c == "'" then
    return self:arith_parse_single_quote()
  end
  if c == "\"" then
    return self:arith_parse_double_quote()
  end
  if c == "`" then
    return self:arith_parse_backtick()
  end
  if c == "\\" then
    self:arith_advance()
    if self:arith_at_end() then
      error({ParseError = true, message = "Unexpected end after backslash in arithmetic", pos = self.arith_pos})
    end
    escaped_char = self:arith_advance()
    return ArithEscape:new(escaped_char, "escape")
  end
  if self:arith_at_end() or (((string.find(")]:,;?|&<>=!+-*/%^~#{}", c, 1, true) ~= nil))) then
    return ArithEmpty:new("empty")
  end
  return self:arith_parse_number_or_var()
end

function Parser:arith_parse_expansion()
  local c, ch, name_chars
  if not self:arith_consume("$") then
    error({ParseError = true, message = "Expected '$'", pos = self.arith_pos})
  end
  c = self:arith_peek(0)
  if c == "(" then
    return self:arith_parse_cmdsub()
  end
  if c == "{" then
    return self:arith_parse_braced_param()
  end
  name_chars = {}
  while not self:arith_at_end() do
    ch = self:arith_peek(0)
    if (string.match(ch, '^%w+$') ~= nil) or ch == "_" then
      ;(function() table.insert(name_chars, self:arith_advance()); return name_chars end)()
    elseif (is_special_param_or_digit(ch) or ch == "#") and not (#(name_chars) > 0) then
      ;(function() table.insert(name_chars, self:arith_advance()); return name_chars end)()
      break
    else
      break
    end
  end
  if not (#(name_chars) > 0) then
    error({ParseError = true, message = "Expected variable name after $", pos = self.arith_pos})
  end
  return ParamExpansion:new(table.concat(name_chars, ""), nil, nil, "param")
end

function Parser:arith_parse_cmdsub()
  local ch, cmd, content, content_start, depth, inner_expr, sub_parser
  self:arith_advance()
  if self:arith_peek(0) == "(" then
    self:arith_advance()
    depth = 1
    content_start = self.arith_pos
    while not self:arith_at_end() and depth > 0 do
      ch = self:arith_peek(0)
      if ch == "(" then
        depth = depth + 1
        self:arith_advance()
      elseif ch == ")" then
        if depth == 1 and self:arith_peek(1) == ")" then
          break
        end
        depth = depth - 1
        self:arith_advance()
      else
        self:arith_advance()
      end
    end
    content = substring(self.arith_src, content_start, self.arith_pos)
    self:arith_advance()
    self:arith_advance()
    inner_expr = self:parse_arith_expr(content)
    return ArithmeticExpansion:new(inner_expr, "arith")
  end
  depth = 1
  content_start = self.arith_pos
  while not self:arith_at_end() and depth > 0 do
    ch = self:arith_peek(0)
    if ch == "(" then
      depth = depth + 1
      self:arith_advance()
    elseif ch == ")" then
      depth = depth - 1
      if depth == 0 then
        break
      end
      self:arith_advance()
    else
      self:arith_advance()
    end
  end
  content = substring(self.arith_src, content_start, self.arith_pos)
  self:arith_advance()
  sub_parser = new_parser(content, false, self.extglob)
  cmd = sub_parser:parse_list(true)
  return CommandSubstitution:new(cmd, nil, "cmdsub")
end

function Parser:arith_parse_braced_param()
  local ch, depth, name, name_chars, op_chars, op_str
  self:arith_advance()
  if self:arith_peek(0) == "!" then
    self:arith_advance()
    name_chars = {}
    while not self:arith_at_end() and self:arith_peek(0) ~= "}" do
      ;(function() table.insert(name_chars, self:arith_advance()); return name_chars end)()
    end
    self:arith_consume("}")
    return ParamIndirect:new(table.concat(name_chars, ""), nil, nil, "param-indirect")
  end
  if self:arith_peek(0) == "#" then
    self:arith_advance()
    name_chars = {}
    while not self:arith_at_end() and self:arith_peek(0) ~= "}" do
      ;(function() table.insert(name_chars, self:arith_advance()); return name_chars end)()
    end
    self:arith_consume("}")
    return ParamLength:new(table.concat(name_chars, ""), "param-len")
  end
  name_chars = {}
  while not self:arith_at_end() do
    ch = self:arith_peek(0)
    if ch == "}" then
      self:arith_advance()
      return ParamExpansion:new(table.concat(name_chars, ""), nil, nil, "param")
    end
    if is_param_expansion_op(ch) then
      break
    end
    ;(function() table.insert(name_chars, self:arith_advance()); return name_chars end)()
  end
  name = table.concat(name_chars, "")
  op_chars = {}
  depth = 1
  while not self:arith_at_end() and depth > 0 do
    ch = self:arith_peek(0)
    if ch == "{" then
      depth = depth + 1
      ;(function() table.insert(op_chars, self:arith_advance()); return op_chars end)()
    elseif ch == "}" then
      depth = depth - 1
      if depth == 0 then
        break
      end
      ;(function() table.insert(op_chars, self:arith_advance()); return op_chars end)()
    else
      ;(function() table.insert(op_chars, self:arith_advance()); return op_chars end)()
    end
  end
  self:arith_consume("}")
  op_str = table.concat(op_chars, "")
  if (string.sub(op_str, 1, #":-") == ":-") then
    return ParamExpansion:new(name, ":-", substring(op_str, 2, #op_str), "param")
  end
  if (string.sub(op_str, 1, #":=") == ":=") then
    return ParamExpansion:new(name, ":=", substring(op_str, 2, #op_str), "param")
  end
  if (string.sub(op_str, 1, #":+") == ":+") then
    return ParamExpansion:new(name, ":+", substring(op_str, 2, #op_str), "param")
  end
  if (string.sub(op_str, 1, #":?") == ":?") then
    return ParamExpansion:new(name, ":?", substring(op_str, 2, #op_str), "param")
  end
  if (string.sub(op_str, 1, #":") == ":") then
    return ParamExpansion:new(name, ":", substring(op_str, 1, #op_str), "param")
  end
  if (string.sub(op_str, 1, #"##") == "##") then
    return ParamExpansion:new(name, "##", substring(op_str, 2, #op_str), "param")
  end
  if (string.sub(op_str, 1, #"#") == "#") then
    return ParamExpansion:new(name, "#", substring(op_str, 1, #op_str), "param")
  end
  if (string.sub(op_str, 1, #"%%") == "%%") then
    return ParamExpansion:new(name, "%%", substring(op_str, 2, #op_str), "param")
  end
  if (string.sub(op_str, 1, #"%") == "%") then
    return ParamExpansion:new(name, "%", substring(op_str, 1, #op_str), "param")
  end
  if (string.sub(op_str, 1, #"//") == "//") then
    return ParamExpansion:new(name, "//", substring(op_str, 2, #op_str), "param")
  end
  if (string.sub(op_str, 1, #"/") == "/") then
    return ParamExpansion:new(name, "/", substring(op_str, 1, #op_str), "param")
  end
  return ParamExpansion:new(name, "", op_str, "param")
end

function Parser:arith_parse_single_quote()
  local content, content_start
  self:arith_advance()
  content_start = self.arith_pos
  while not self:arith_at_end() and self:arith_peek(0) ~= "'" do
    self:arith_advance()
  end
  content = substring(self.arith_src, content_start, self.arith_pos)
  if not self:arith_consume("'") then
    error({ParseError = true, message = "Unterminated single quote in arithmetic", pos = self.arith_pos})
  end
  return ArithNumber:new(content, "number")
end

function Parser:arith_parse_double_quote()
  local c, content, content_start
  self:arith_advance()
  content_start = self.arith_pos
  while not self:arith_at_end() and self:arith_peek(0) ~= "\"" do
    c = self:arith_peek(0)
    if c == "\\" and not self:arith_at_end() then
      self:arith_advance()
      self:arith_advance()
    else
      self:arith_advance()
    end
  end
  content = substring(self.arith_src, content_start, self.arith_pos)
  if not self:arith_consume("\"") then
    error({ParseError = true, message = "Unterminated double quote in arithmetic", pos = self.arith_pos})
  end
  return ArithNumber:new(content, "number")
end

function Parser:arith_parse_backtick()
  local c, cmd, content, content_start, sub_parser
  self:arith_advance()
  content_start = self.arith_pos
  while not self:arith_at_end() and self:arith_peek(0) ~= "`" do
    c = self:arith_peek(0)
    if c == "\\" and not self:arith_at_end() then
      self:arith_advance()
      self:arith_advance()
    else
      self:arith_advance()
    end
  end
  content = substring(self.arith_src, content_start, self.arith_pos)
  if not self:arith_consume("`") then
    error({ParseError = true, message = "Unterminated backtick in arithmetic", pos = self.arith_pos})
  end
  sub_parser = new_parser(content, false, self.extglob)
  cmd = sub_parser:parse_list(true)
  return CommandSubstitution:new(cmd, nil, "cmdsub")
end

function Parser:arith_parse_number_or_var()
  local c, ch, chars, expansion, prefix
  self:arith_skip_ws()
  chars = {}
  c = self:arith_peek(0)
  if (string.match(c, '^%d+$') ~= nil) then
    while not self:arith_at_end() do
      ch = self:arith_peek(0)
      if (string.match(ch, '^%w+$') ~= nil) or ch == "#" or ch == "_" then
        ;(function() table.insert(chars, self:arith_advance()); return chars end)()
      else
        break
      end
    end
    prefix = table.concat(chars, "")
    if not self:arith_at_end() and self:arith_peek(0) == "$" then
      expansion = self:arith_parse_expansion()
      return ArithConcat:new({ArithNumber:new(prefix, "number"), expansion}, "arith-concat")
    end
    return ArithNumber:new(prefix, "number")
  end
  if (string.match(c, '^%a+$') ~= nil) or c == "_" then
    while not self:arith_at_end() do
      ch = self:arith_peek(0)
      if (string.match(ch, '^%w+$') ~= nil) or ch == "_" then
        ;(function() table.insert(chars, self:arith_advance()); return chars end)()
      else
        break
      end
    end
    return ArithVar:new(table.concat(chars, ""), "var")
  end
  error({ParseError = true, message = "Unexpected character '" .. c .. "' in arithmetic expression", pos = self.arith_pos})
end

function Parser:parse_deprecated_arithmetic()
  local content, start, text
  if self:at_end() or self:peek() ~= "$" then
    return {nil, ""}
  end
  start = self.pos
  if self.pos + 1 >= self.length or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) ~= "[" then
    return {nil, ""}
  end
  self:advance()
  self:advance()
  self.lexer.pos = self.pos
  content = self.lexer:parse_matched_pair("[", "]", MATCHEDPAIRFLAGS_ARITH, false)
  self.pos = self.lexer.pos
  text = substring(self.source, start, self.pos)
  return {ArithDeprecated:new(content, "arith-deprecated"), text}
end

function Parser:parse_param_expansion(in_dquote)
  local result0, result1
  self:sync_lexer()
  result0, result1 = table.unpack(self.lexer:read_param_expansion(in_dquote))
  self:sync_parser()
  return {result0, result1}
end

function Parser:parse_redirect()
  local base, c, ch, fd, fd_chars, fd_target, in_bracket, inner_word, is_valid_varfd, left, next_ch, op, right, saved, start, strip_tabs, target, varfd, varname, varname_chars, word_start
  self:skip_whitespace()
  if self:at_end() then
    return nil
  end
  start = self.pos
  fd = -1
  varfd = ""
  if self:peek() == "{" then
    saved = self.pos
    self:advance()
    varname_chars = {}
    in_bracket = false
    while not self:at_end() and not is_redirect_char(self:peek()) do
      ch = self:peek()
      if ch == "}" and not in_bracket then
        break
      elseif ch == "[" then
        in_bracket = true
        ;(function() table.insert(varname_chars, self:advance()); return varname_chars end)()
      elseif ch == "]" then
        in_bracket = false
        ;(function() table.insert(varname_chars, self:advance()); return varname_chars end)()
      elseif (string.match(ch, '^%w+$') ~= nil) or ch == "_" then
        ;(function() table.insert(varname_chars, self:advance()); return varname_chars end)()
      elseif in_bracket and not is_metachar(ch) then
        ;(function() table.insert(varname_chars, self:advance()); return varname_chars end)()
      else
        break
      end
    end
    varname = table.concat(varname_chars, "")
    is_valid_varfd = false
    if (varname ~= nil and #(varname) > 0) then
      if (string.match(string.sub(varname, 0 + 1, 0 + 1), '^%a+$') ~= nil) or string.sub(varname, 0 + 1, 0 + 1) == "_" then
        if (((string.find(varname, "[", 1, true) ~= nil))) or (((string.find(varname, "]", 1, true) ~= nil))) then
          left = _string_find(varname, "[")
          right = _string_rfind(varname, "]")
          if left ~= -1 and right == #varname - 1 and right > left + 1 then
            base = string.sub(varname, 1, left)
            if (base ~= nil and #(base) > 0) and ((string.match(string.sub(base, 0 + 1, 0 + 1), '^%a+$') ~= nil) or string.sub(base, 0 + 1, 0 + 1) == "_") then
              is_valid_varfd = true
              for _ = 1, #string.sub(base, (1) + 1, #base) do
                local c = string.sub(string.sub(base, (1) + 1, #base), _, _)
                if not ((string.match(c, '^%w+$') ~= nil) or c == "_") then
                  is_valid_varfd = false
                  break
                end
              end
            end
          end
        else
          is_valid_varfd = true
          for _ = 1, #string.sub(varname, (1) + 1, #varname) do
            local c = string.sub(string.sub(varname, (1) + 1, #varname), _, _)
            if not ((string.match(c, '^%w+$') ~= nil) or c == "_") then
              is_valid_varfd = false
              break
            end
          end
        end
      end
    end
    if not self:at_end() and self:peek() == "}" and is_valid_varfd then
      self:advance()
      varfd = varname
    else
      self.pos = saved
    end
  end
  if varfd == "" and (self:peek() ~= nil and #(self:peek()) > 0) and (string.match(self:peek(), '^%d+$') ~= nil) then
    fd_chars = {}
    while not self:at_end() and (string.match(self:peek(), '^%d+$') ~= nil) do
      ;(function() table.insert(fd_chars, self:advance()); return fd_chars end)()
    end
    fd = tonumber(table.concat(fd_chars, ""))
  end
  ch = self:peek()
  if ch == "&" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == ">" then
    if fd ~= -1 or varfd ~= "" then
      self.pos = start
      return nil
    end
    self:advance()
    self:advance()
    if not self:at_end() and self:peek() == ">" then
      self:advance()
      op = "&>>"
    else
      op = "&>"
    end
    self:skip_whitespace()
    target = self:parse_word(false, false, false)
    if (target == nil) then
      error({ParseError = true, message = "Expected target for redirect " .. op, pos = self.pos})
    end
    return Redirect:new(op, target, nil, "redirect")
  end
  if ch == "" or not is_redirect_char(ch) then
    self.pos = start
    return nil
  end
  if fd == -1 and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
    self.pos = start
    return nil
  end
  op = self:advance()
  strip_tabs = false
  if not self:at_end() then
    next_ch = self:peek()
    if op == ">" and next_ch == ">" then
      self:advance()
      op = ">>"
    elseif op == "<" and next_ch == "<" then
      self:advance()
      if not self:at_end() and self:peek() == "<" then
        self:advance()
        op = "<<<"
      elseif not self:at_end() and self:peek() == "-" then
        self:advance()
        op = "<<"
        strip_tabs = true
      else
        op = "<<"
      end
    elseif op == "<" and next_ch == ">" then
      self:advance()
      op = "<>"
    elseif op == ">" and next_ch == "|" then
      self:advance()
      op = ">|"
    elseif fd == -1 and varfd == "" and op == ">" and next_ch == "&" then
      if self.pos + 1 >= self.length or not is_digit_or_dash(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)) then
        self:advance()
        op = ">&"
      end
    elseif fd == -1 and varfd == "" and op == "<" and next_ch == "&" then
      if self.pos + 1 >= self.length or not is_digit_or_dash(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)) then
        self:advance()
        op = "<&"
      end
    end
  end
  if op == "<<" then
    return self:parse_heredoc(((fd) == -1 and nil or (fd)), strip_tabs)
  end
  if varfd ~= "" then
    op = "{" .. varfd .. "}" .. op
  elseif fd ~= -1 then
    op = tostring(fd) .. op
  end
  if not self:at_end() and self:peek() == "&" then
    self:advance()
    self:skip_whitespace()
    if not self:at_end() and self:peek() == "-" then
      if self.pos + 1 < self.length and not is_metachar(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)) then
        self:advance()
        target = Word:new("&-", nil, "word")
      else
        target = nil
      end
    else
      target = nil
    end
    if (target == nil) then
      if not self:at_end() and ((string.match(self:peek(), '^%d+$') ~= nil) or self:peek() == "-") then
        word_start = self.pos
        fd_chars = {}
        while not self:at_end() and (string.match(self:peek(), '^%d+$') ~= nil) do
          ;(function() table.insert(fd_chars, self:advance()); return fd_chars end)()
        end
        if (#(fd_chars) > 0) then
          fd_target = table.concat(fd_chars, "")
        else
          fd_target = ""
        end
        if not self:at_end() and self:peek() == "-" then
          fd_target = fd_target .. self:advance()
        end
        if fd_target ~= "-" and not self:at_end() and not is_metachar(self:peek()) then
          self.pos = word_start
          inner_word = self:parse_word(false, false, false)
          if (inner_word ~= nil) then
            target = Word:new("&" .. inner_word.value, nil, "word")
            target.parts = inner_word.parts
          else
            error({ParseError = true, message = "Expected target for redirect " .. op, pos = self.pos})
          end
        else
          target = Word:new("&" .. fd_target, nil, "word")
        end
      else
        inner_word = self:parse_word(false, false, false)
        if (inner_word ~= nil) then
          target = Word:new("&" .. inner_word.value, nil, "word")
          target.parts = inner_word.parts
        else
          error({ParseError = true, message = "Expected target for redirect " .. op, pos = self.pos})
        end
      end
    end
  else
    self:skip_whitespace()
    if (op == ">&" or op == "<&") and not self:at_end() and self:peek() == "-" then
      if self.pos + 1 < self.length and not is_metachar(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)) then
        self:advance()
        target = Word:new("&-", nil, "word")
      else
        target = self:parse_word(false, false, false)
      end
    else
      target = self:parse_word(false, false, false)
    end
  end
  if (target == nil) then
    error({ParseError = true, message = "Expected target for redirect " .. op, pos = self.pos})
  end
  return Redirect:new(op, target, nil, "redirect")
end

function Parser:parse_heredoc_delimiter()
  local c, ch, delimiter_chars, depth, dollar_count, esc, esc_val, j, next_ch, quoted
  self:skip_whitespace()
  quoted = false
  delimiter_chars = {}
  while true do
    while not self:at_end() and not is_metachar(self:peek()) do
      ch = self:peek()
      if ch == "\"" then
        quoted = true
        self:advance()
        while not self:at_end() and self:peek() ~= "\"" do
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        end
        if not self:at_end() then
          self:advance()
        end
      elseif ch == "'" then
        quoted = true
        self:advance()
        while not self:at_end() and self:peek() ~= "'" do
          c = self:advance()
          if c == "\n" then
            self.saw_newline_in_single_quote = true
          end
          ;(function() table.insert(delimiter_chars, c); return delimiter_chars end)()
        end
        if not self:at_end() then
          self:advance()
        end
      elseif ch == "\\" then
        self:advance()
        if not self:at_end() then
          next_ch = self:peek()
          if next_ch == "\n" then
            self:advance()
          else
            quoted = true
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          end
        end
      elseif ch == "$" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "'" then
        quoted = true
        self:advance()
        self:advance()
        while not self:at_end() and self:peek() ~= "'" do
          c = self:peek()
          if c == "\\" and self.pos + 1 < self.length then
            self:advance()
            esc = self:peek()
            esc_val = get_ansi_escape(esc)
            if esc_val >= 0 then
              ;(function() table.insert(delimiter_chars, utf8.char(esc_val)); return delimiter_chars end)()
              self:advance()
            elseif esc == "'" then
              ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            else
              ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            end
          else
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          end
        end
        if not self:at_end() then
          self:advance()
        end
      elseif is_expansion_start(self.source, self.pos, "$(") then
        ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        depth = 1
        while not self:at_end() and depth > 0 do
          c = self:peek()
          if c == "(" then
            depth = depth + 1
          elseif c == ")" then
            depth = depth - 1
          end
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        end
      elseif ch == "$" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "{" then
        dollar_count = 0
        j = self.pos - 1
        while j >= 0 and string.sub(self.source, j + 1, j + 1) == "$" do
          dollar_count = dollar_count + 1
          j = j - 1
        end
        if j >= 0 and string.sub(self.source, j + 1, j + 1) == "\\" then
          dollar_count = dollar_count - 1
        end
        if dollar_count % 2 == 1 then
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        else
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          depth = 0
          while not self:at_end() do
            c = self:peek()
            if c == "{" then
              depth = depth + 1
            elseif c == "}" then
              ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
              if depth == 0 then
                break
              end
              depth = depth - 1
              if depth == 0 and not self:at_end() and is_metachar(self:peek()) then
                break
              end
              goto continue
            end
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            ::continue::
          end
        end
      elseif ch == "$" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "[" then
        dollar_count = 0
        j = self.pos - 1
        while j >= 0 and string.sub(self.source, j + 1, j + 1) == "$" do
          dollar_count = dollar_count + 1
          j = j - 1
        end
        if j >= 0 and string.sub(self.source, j + 1, j + 1) == "\\" then
          dollar_count = dollar_count - 1
        end
        if dollar_count % 2 == 1 then
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        else
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          depth = 1
          while not self:at_end() and depth > 0 do
            c = self:peek()
            if c == "[" then
              depth = depth + 1
            elseif c == "]" then
              depth = depth - 1
            end
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          end
        end
      elseif ch == "`" then
        ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        while not self:at_end() and self:peek() ~= "`" do
          c = self:peek()
          if c == "'" then
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            while not self:at_end() and self:peek() ~= "'" and self:peek() ~= "`" do
              ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            end
            if not self:at_end() and self:peek() == "'" then
              ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            end
          elseif c == "\"" then
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            while not self:at_end() and self:peek() ~= "\"" and self:peek() ~= "`" do
              if self:peek() == "\\" and self.pos + 1 < self.length then
                ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
              end
              ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            end
            if not self:at_end() and self:peek() == "\"" then
              ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            end
          elseif c == "\\" and self.pos + 1 < self.length then
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          else
            ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
          end
        end
        if not self:at_end() then
          ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
        end
      else
        ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
      end
    end
    if not self:at_end() and (((string.find("<>", self:peek(), 1, true) ~= nil))) and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
      ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
      ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
      depth = 1
      while not self:at_end() and depth > 0 do
        c = self:peek()
        if c == "(" then
          depth = depth + 1
        elseif c == ")" then
          depth = depth - 1
        end
        ;(function() table.insert(delimiter_chars, self:advance()); return delimiter_chars end)()
      end
      goto continue
    end
    break
    ::continue::
  end
  return {table.concat(delimiter_chars, ""), quoted}
end

function Parser:read_heredoc_line(quoted)
  local line, line_end, line_start, next_line_start, trailing_bs
  line_start = self.pos
  line_end = self.pos
  while line_end < self.length and string.sub(self.source, line_end + 1, line_end + 1) ~= "\n" do
    line_end = line_end + 1
  end
  line = substring(self.source, line_start, line_end)
  if not quoted then
    while line_end < self.length do
      trailing_bs = count_trailing_backslashes(line)
      if trailing_bs % 2 == 0 then
        break
      end
      line = substring(line, 0, #line - 1)
      line_end = line_end + 1
      next_line_start = line_end
      while line_end < self.length and string.sub(self.source, line_end + 1, line_end + 1) ~= "\n" do
        line_end = line_end + 1
      end
      line = line .. substring(self.source, next_line_start, line_end)
    end
  end
  return {line, line_end}
end

function Parser:line_matches_delimiter(line, delimiter, strip_tabs)
  local check_line, normalized_check, normalized_delim
  check_line = (strip_tabs and (string.gsub(line, '^[' .. "\t" .. ']+', '')) or line)
  normalized_check = normalize_heredoc_delimiter(check_line)
  normalized_delim = normalize_heredoc_delimiter(delimiter)
  return {normalized_check == normalized_delim, check_line}
end

function Parser:gather_heredoc_bodies()
  local add_newline, check_line, content_lines, heredoc, line, line_end, line_start, matches, normalized_check, normalized_delim, tabs_stripped
  for _, heredoc in ipairs(self.pending_heredocs) do
    content_lines = {}
    line_start = self.pos
    while self.pos < self.length do
      line_start = self.pos
      line, line_end = table.unpack(self:read_heredoc_line(heredoc.quoted))
      matches, check_line = table.unpack(self:line_matches_delimiter(line, heredoc.delimiter, heredoc.strip_tabs))
      if matches then
        self.pos = (line_end < self.length and line_end + 1 or line_end)
        break
      end
      normalized_check = normalize_heredoc_delimiter(check_line)
      normalized_delim = normalize_heredoc_delimiter(heredoc.delimiter)
      if self.eof_token == ")" and (string.sub(normalized_check, 1, #normalized_delim) == normalized_delim) then
        tabs_stripped = #line - #check_line
        self.pos = line_start + tabs_stripped + #heredoc.delimiter
        break
      end
      if line_end >= self.length and (string.sub(normalized_check, 1, #normalized_delim) == normalized_delim) and self.in_process_sub then
        tabs_stripped = #line - #check_line
        self.pos = line_start + tabs_stripped + #heredoc.delimiter
        break
      end
      if heredoc.strip_tabs then
        line = (string.gsub(line, '^[' .. "\t" .. ']+', ''))
      end
      if line_end < self.length then
        ;(function() table.insert(content_lines, line .. "\n"); return content_lines end)()
        self.pos = line_end + 1
      else
        add_newline = true
        if not heredoc.quoted and count_trailing_backslashes(line) % 2 == 1 then
          add_newline = false
        end
        ;(function() table.insert(content_lines, line .. ((add_newline and "\n" or ""))); return content_lines end)()
        self.pos = self.length
      end
    end
    heredoc.content = table.concat(content_lines, "")
  end
  self.pending_heredocs = {}
end

function Parser:parse_heredoc(fd, strip_tabs)
  local delimiter, existing, heredoc, quoted, start_pos
  start_pos = self.pos
  self:set_state(PARSERSTATEFLAGS_PST_HEREDOC)
  delimiter, quoted = table.unpack(self:parse_heredoc_delimiter())
  for _, existing in ipairs(self.pending_heredocs) do
    if existing.start_pos == start_pos and existing.delimiter == delimiter then
      self:clear_state(PARSERSTATEFLAGS_PST_HEREDOC)
      return existing
    end
  end
  heredoc = HereDoc:new(delimiter, "", strip_tabs, quoted, fd, false, nil, "heredoc")
  heredoc.start_pos = start_pos
  ;(function() table.insert(self.pending_heredocs, heredoc); return self.pending_heredocs end)()
  self:clear_state(PARSERSTATEFLAGS_PST_HEREDOC)
  return heredoc
end

function Parser:parse_command()
  local all_assignments, in_assign_builtin, redirect, redirects, reserved, w, word, words
  words = {}
  redirects = {}
  while true do
    self:skip_whitespace()
    if self:lex_is_command_terminator() then
      break
    end
    if #words == 0 then
      reserved = self:lex_peek_reserved_word()
      if reserved == "}" or reserved == "]]" then
        break
      end
    end
    redirect = self:parse_redirect()
    if (redirect ~= nil) then
      ;(function() table.insert(redirects, redirect); return redirects end)()
      goto continue
    end
    all_assignments = true
    for _, w in ipairs(words) do
      if not self:is_assignment_word(w) then
        all_assignments = false
        break
      end
    end
    in_assign_builtin = #words > 0 and (_set_contains(ASSIGNMENT_BUILTINS, words[0 + 1].value))
    word = self:parse_word(not (#(words) > 0) or all_assignments and #redirects == 0, false, in_assign_builtin)
    if (word == nil) then
      break
    end
    ;(function() table.insert(words, word); return words end)()
    ::continue::
  end
  if not (#(words) > 0) and not (#(redirects) > 0) then
    return nil
  end
  return Command:new(words, redirects, "command")
end

function Parser:parse_subshell()
  local body
  self:skip_whitespace()
  if self:at_end() or self:peek() ~= "(" then
    return nil
  end
  self:advance()
  self:set_state(PARSERSTATEFLAGS_PST_SUBSHELL)
  body = self:parse_list(true)
  if (body == nil) then
    self:clear_state(PARSERSTATEFLAGS_PST_SUBSHELL)
    error({ParseError = true, message = "Expected command in subshell", pos = self.pos})
  end
  self:skip_whitespace()
  if self:at_end() or self:peek() ~= ")" then
    self:clear_state(PARSERSTATEFLAGS_PST_SUBSHELL)
    error({ParseError = true, message = "Expected ) to close subshell", pos = self.pos})
  end
  self:advance()
  self:clear_state(PARSERSTATEFLAGS_PST_SUBSHELL)
  return Subshell:new(body, self:collect_redirects(), "subshell")
end

function Parser:parse_arithmetic_command()
  local c, content, content_start, depth, expr, saved_pos
  self:skip_whitespace()
  if self:at_end() or self:peek() ~= "(" or self.pos + 1 >= self.length or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) ~= "(" then
    return nil
  end
  saved_pos = self.pos
  self:advance()
  self:advance()
  content_start = self.pos
  depth = 1
  while not self:at_end() and depth > 0 do
    c = self:peek()
    if c == "'" then
      self:advance()
      while not self:at_end() and self:peek() ~= "'" do
        self:advance()
      end
      if not self:at_end() then
        self:advance()
      end
    elseif c == "\"" then
      self:advance()
      while not self:at_end() do
        if self:peek() == "\\" and self.pos + 1 < self.length then
          self:advance()
          self:advance()
        elseif self:peek() == "\"" then
          self:advance()
          break
        else
          self:advance()
        end
      end
    elseif c == "\\" and self.pos + 1 < self.length then
      self:advance()
      self:advance()
    elseif c == "(" then
      depth = depth + 1
      self:advance()
    elseif c == ")" then
      if depth == 1 and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == ")" then
        break
      end
      depth = depth - 1
      if depth == 0 then
        self.pos = saved_pos
        return nil
      end
      self:advance()
    else
      self:advance()
    end
  end
  if self:at_end() then
    error({MatchedPairError = true, message = "unexpected EOF looking for `))'", pos = saved_pos})
  end
  if depth ~= 1 then
    self.pos = saved_pos
    return nil
  end
  content = substring(self.source, content_start, self.pos)
  content = (string.gsub(content, "\\\n", ""))
  self:advance()
  self:advance()
  expr = self:parse_arith_expr(content)
  return ArithmeticCommand:new(expr, self:collect_redirects(), content, "arith-cmd")
end

function Parser:parse_conditional_expr()
  local body, next_pos
  self:skip_whitespace()
  if self:at_end() or self:peek() ~= "[" or self.pos + 1 >= self.length or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) ~= "[" then
    return nil
  end
  next_pos = self.pos + 2
  if next_pos < self.length and not (is_whitespace(string.sub(self.source, next_pos + 1, next_pos + 1)) or string.sub(self.source, next_pos + 1, next_pos + 1) == "\\" and next_pos + 1 < self.length and string.sub(self.source, next_pos + 1 + 1, next_pos + 1 + 1) == "\n") then
    return nil
  end
  self:advance()
  self:advance()
  self:set_state(PARSERSTATEFLAGS_PST_CONDEXPR)
  self.word_context = WORD_CTX_COND
  body = self:parse_cond_or()
  while not self:at_end() and is_whitespace_no_newline(self:peek()) do
    self:advance()
  end
  if self:at_end() or self:peek() ~= "]" or self.pos + 1 >= self.length or string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) ~= "]" then
    self:clear_state(PARSERSTATEFLAGS_PST_CONDEXPR)
    self.word_context = WORD_CTX_NORMAL
    error({ParseError = true, message = "Expected ]] to close conditional expression", pos = self.pos})
  end
  self:advance()
  self:advance()
  self:clear_state(PARSERSTATEFLAGS_PST_CONDEXPR)
  self.word_context = WORD_CTX_NORMAL
  return ConditionalExpr:new(body, self:collect_redirects(), "cond-expr")
end

function Parser:cond_skip_whitespace()
  while not self:at_end() do
    if is_whitespace_no_newline(self:peek()) then
      self:advance()
    elseif self:peek() == "\\" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "\n" then
      self:advance()
      self:advance()
    elseif self:peek() == "\n" then
      self:advance()
    else
      break
    end
  end
end

function Parser:cond_at_end()
  return self:at_end() or self:peek() == "]" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "]"
end

function Parser:parse_cond_or()
  local left, right
  self:cond_skip_whitespace()
  left = self:parse_cond_and()
  self:cond_skip_whitespace()
  if not self:cond_at_end() and self:peek() == "|" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "|" then
    self:advance()
    self:advance()
    right = self:parse_cond_or()
    return CondOr:new(left, right, "cond-or")
  end
  return left
end

function Parser:parse_cond_and()
  local left, right
  self:cond_skip_whitespace()
  left = self:parse_cond_term()
  self:cond_skip_whitespace()
  if not self:cond_at_end() and self:peek() == "&" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "&" then
    self:advance()
    self:advance()
    right = self:parse_cond_and()
    return CondAnd:new(left, right, "cond-and")
  end
  return left
end

function Parser:parse_cond_term()
  local inner, op, op_word, operand, saved_pos, word1, word2
  self:cond_skip_whitespace()
  if self:cond_at_end() then
    error({ParseError = true, message = "Unexpected end of conditional expression", pos = self.pos})
  end
  if self:peek() == "!" then
    if self.pos + 1 < self.length and not is_whitespace_no_newline(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1)) then
      -- empty then
    else
      self:advance()
      operand = self:parse_cond_term()
      return CondNot:new(operand, "cond-not")
    end
  end
  if self:peek() == "(" then
    self:advance()
    inner = self:parse_cond_or()
    self:cond_skip_whitespace()
    if self:at_end() or self:peek() ~= ")" then
      error({ParseError = true, message = "Expected ) in conditional expression", pos = self.pos})
    end
    self:advance()
    return CondParen:new(inner, "cond-paren")
  end
  word1 = self:parse_cond_word()
  if (word1 == nil) then
    error({ParseError = true, message = "Expected word in conditional expression", pos = self.pos})
  end
  self:cond_skip_whitespace()
  if _set_contains(COND_UNARY_OPS, word1.value) then
    operand = self:parse_cond_word()
    if (operand == nil) then
      error({ParseError = true, message = "Expected operand after " .. word1.value, pos = self.pos})
    end
    return UnaryTest:new(word1.value, operand, "unary-test")
  end
  if not self:cond_at_end() and self:peek() ~= "&" and self:peek() ~= "|" and self:peek() ~= ")" then
    if is_redirect_char(self:peek()) and not (self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(") then
      op = self:advance()
      self:cond_skip_whitespace()
      word2 = self:parse_cond_word()
      if (word2 == nil) then
        error({ParseError = true, message = "Expected operand after " .. op, pos = self.pos})
      end
      return BinaryTest:new(op, word1, word2, "binary-test")
    end
    saved_pos = self.pos
    op_word = self:parse_cond_word()
    if (op_word ~= nil) and (_set_contains(COND_BINARY_OPS, op_word.value)) then
      self:cond_skip_whitespace()
      if op_word.value == "=~" then
        word2 = self:parse_cond_regex_word()
      else
        word2 = self:parse_cond_word()
      end
      if (word2 == nil) then
        error({ParseError = true, message = "Expected operand after " .. op_word.value, pos = self.pos})
      end
      return BinaryTest:new(op_word.value, word1, word2, "binary-test")
    else
      self.pos = saved_pos
    end
  end
  return UnaryTest:new("-n", word1, "unary-test")
end

function Parser:parse_cond_word()
  local c
  self:cond_skip_whitespace()
  if self:cond_at_end() then
    return nil
  end
  c = self:peek()
  if is_paren(c) then
    return nil
  end
  if c == "&" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "&" then
    return nil
  end
  if c == "|" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "|" then
    return nil
  end
  return self:parse_word_internal(WORD_CTX_COND, false, false)
end

function Parser:parse_cond_regex_word()
  local result
  self:cond_skip_whitespace()
  if self:cond_at_end() then
    return nil
  end
  self:set_state(PARSERSTATEFLAGS_PST_REGEXP)
  result = self:parse_word_internal(WORD_CTX_REGEX, false, false)
  self:clear_state(PARSERSTATEFLAGS_PST_REGEXP)
  self.word_context = WORD_CTX_COND
  return result
end

function Parser:parse_brace_group()
  local body
  self:skip_whitespace()
  if not self:lex_consume_word("{") then
    return nil
  end
  self:skip_whitespace_and_newlines()
  body = self:parse_list(true)
  if (body == nil) then
    error({ParseError = true, message = "Expected command in brace group", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace()
  if not self:lex_consume_word("}") then
    error({ParseError = true, message = "Expected } to close brace group", pos = self:lex_peek_token().pos})
  end
  return BraceGroup:new(body, self:collect_redirects(), "brace-group")
end

function Parser:parse_if()
  local condition, elif_condition, elif_then_body, else_body, inner_else, then_body
  self:skip_whitespace()
  if not self:lex_consume_word("if") then
    return nil
  end
  condition = self:parse_list_until({["then"] = true})
  if (condition == nil) then
    error({ParseError = true, message = "Expected condition after 'if'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("then") then
    error({ParseError = true, message = "Expected 'then' after if condition", pos = self:lex_peek_token().pos})
  end
  then_body = self:parse_list_until({["elif"] = true, ["else"] = true, ["fi"] = true})
  if (then_body == nil) then
    error({ParseError = true, message = "Expected commands after 'then'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  else_body = nil
  if self:lex_is_at_reserved_word("elif") then
    self:lex_consume_word("elif")
    elif_condition = self:parse_list_until({["then"] = true})
    if (elif_condition == nil) then
      error({ParseError = true, message = "Expected condition after 'elif'", pos = self:lex_peek_token().pos})
    end
    self:skip_whitespace_and_newlines()
    if not self:lex_consume_word("then") then
      error({ParseError = true, message = "Expected 'then' after elif condition", pos = self:lex_peek_token().pos})
    end
    elif_then_body = self:parse_list_until({["elif"] = true, ["else"] = true, ["fi"] = true})
    if (elif_then_body == nil) then
      error({ParseError = true, message = "Expected commands after 'then'", pos = self:lex_peek_token().pos})
    end
    self:skip_whitespace_and_newlines()
    inner_else = nil
    if self:lex_is_at_reserved_word("elif") then
      inner_else = self:parse_elif_chain()
    elseif self:lex_is_at_reserved_word("else") then
      self:lex_consume_word("else")
      inner_else = self:parse_list_until({["fi"] = true})
      if (inner_else == nil) then
        error({ParseError = true, message = "Expected commands after 'else'", pos = self:lex_peek_token().pos})
      end
    end
    else_body = If:new(elif_condition, elif_then_body, inner_else, nil, "if")
  elseif self:lex_is_at_reserved_word("else") then
    self:lex_consume_word("else")
    else_body = self:parse_list_until({["fi"] = true})
    if (else_body == nil) then
      error({ParseError = true, message = "Expected commands after 'else'", pos = self:lex_peek_token().pos})
    end
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("fi") then
    error({ParseError = true, message = "Expected 'fi' to close if statement", pos = self:lex_peek_token().pos})
  end
  return If:new(condition, then_body, else_body, self:collect_redirects(), "if")
end

function Parser:parse_elif_chain()
  local condition, else_body, then_body
  self:lex_consume_word("elif")
  condition = self:parse_list_until({["then"] = true})
  if (condition == nil) then
    error({ParseError = true, message = "Expected condition after 'elif'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("then") then
    error({ParseError = true, message = "Expected 'then' after elif condition", pos = self:lex_peek_token().pos})
  end
  then_body = self:parse_list_until({["elif"] = true, ["else"] = true, ["fi"] = true})
  if (then_body == nil) then
    error({ParseError = true, message = "Expected commands after 'then'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  else_body = nil
  if self:lex_is_at_reserved_word("elif") then
    else_body = self:parse_elif_chain()
  elseif self:lex_is_at_reserved_word("else") then
    self:lex_consume_word("else")
    else_body = self:parse_list_until({["fi"] = true})
    if (else_body == nil) then
      error({ParseError = true, message = "Expected commands after 'else'", pos = self:lex_peek_token().pos})
    end
  end
  return If:new(condition, then_body, else_body, nil, "if")
end

function Parser:parse_while()
  local body, condition
  self:skip_whitespace()
  if not self:lex_consume_word("while") then
    return nil
  end
  condition = self:parse_list_until({["do"] = true})
  if (condition == nil) then
    error({ParseError = true, message = "Expected condition after 'while'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("do") then
    error({ParseError = true, message = "Expected 'do' after while condition", pos = self:lex_peek_token().pos})
  end
  body = self:parse_list_until({["done"] = true})
  if (body == nil) then
    error({ParseError = true, message = "Expected commands after 'do'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("done") then
    error({ParseError = true, message = "Expected 'done' to close while loop", pos = self:lex_peek_token().pos})
  end
  return While:new(condition, body, self:collect_redirects(), "while")
end

function Parser:parse_until()
  local body, condition
  self:skip_whitespace()
  if not self:lex_consume_word("until") then
    return nil
  end
  condition = self:parse_list_until({["do"] = true})
  if (condition == nil) then
    error({ParseError = true, message = "Expected condition after 'until'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("do") then
    error({ParseError = true, message = "Expected 'do' after until condition", pos = self:lex_peek_token().pos})
  end
  body = self:parse_list_until({["done"] = true})
  if (body == nil) then
    error({ParseError = true, message = "Expected commands after 'do'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("done") then
    error({ParseError = true, message = "Expected 'done' to close until loop", pos = self:lex_peek_token().pos})
  end
  return Until:new(condition, body, self:collect_redirects(), "until")
end

function Parser:parse_for()
  local body, brace_group, saw_delimiter, var_name, var_word, word, words
  self:skip_whitespace()
  if not self:lex_consume_word("for") then
    return nil
  end
  self:skip_whitespace()
  if self:peek() == "(" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
    return self:parse_for_arith()
  end
  if self:peek() == "$" then
    var_word = self:parse_word(false, false, false)
    if (var_word == nil) then
      error({ParseError = true, message = "Expected variable name after 'for'", pos = self:lex_peek_token().pos})
    end
    var_name = var_word.value
  else
    var_name = self:peek_word()
    if var_name == "" then
      error({ParseError = true, message = "Expected variable name after 'for'", pos = self:lex_peek_token().pos})
    end
    self:consume_word(var_name)
  end
  self:skip_whitespace()
  if self:peek() == ";" then
    self:advance()
  end
  self:skip_whitespace_and_newlines()
  words = nil
  if self:lex_is_at_reserved_word("in") then
    self:lex_consume_word("in")
    self:skip_whitespace()
    saw_delimiter = is_semicolon_or_newline(self:peek())
    if self:peek() == ";" then
      self:advance()
    end
    self:skip_whitespace_and_newlines()
    words = {}
    while true do
      self:skip_whitespace()
      if self:at_end() then
        break
      end
      if is_semicolon_or_newline(self:peek()) then
        saw_delimiter = true
        if self:peek() == ";" then
          self:advance()
        end
        break
      end
      if self:lex_is_at_reserved_word("do") then
        if saw_delimiter then
          break
        end
        error({ParseError = true, message = "Expected ';' or newline before 'do'", pos = self:lex_peek_token().pos})
      end
      word = self:parse_word(false, false, false)
      if (word == nil) then
        break
      end
      ;(function() table.insert(words, word); return words end)()
    end
  end
  self:skip_whitespace_and_newlines()
  if self:peek() == "{" then
    brace_group = self:parse_brace_group()
    if (brace_group == nil) then
      error({ParseError = true, message = "Expected brace group in for loop", pos = self:lex_peek_token().pos})
    end
    return For:new(var_name, words, brace_group.body, self:collect_redirects(), "for")
  end
  if not self:lex_consume_word("do") then
    error({ParseError = true, message = "Expected 'do' in for loop", pos = self:lex_peek_token().pos})
  end
  body = self:parse_list_until({["done"] = true})
  if (body == nil) then
    error({ParseError = true, message = "Expected commands after 'do'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("done") then
    error({ParseError = true, message = "Expected 'done' to close for loop", pos = self:lex_peek_token().pos})
  end
  return For:new(var_name, words, body, self:collect_redirects(), "for")
end

function Parser:parse_for_arith()
  local body, ch, cond, current, incr, init, paren_depth, parts
  self:advance()
  self:advance()
  parts = {}
  current = {}
  paren_depth = 0
  while not self:at_end() do
    ch = self:peek()
    if ch == "(" then
      paren_depth = paren_depth + 1
      ;(function() table.insert(current, self:advance()); return current end)()
    elseif ch == ")" then
      if paren_depth > 0 then
        paren_depth = paren_depth - 1
        ;(function() table.insert(current, self:advance()); return current end)()
      elseif self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == ")" then
        ;(function() table.insert(parts, (string.gsub(table.concat(current, ""), '^[' .. " \t" .. ']+', ''))); return parts end)()
        self:advance()
        self:advance()
        break
      else
        ;(function() table.insert(current, self:advance()); return current end)()
      end
    elseif ch == ";" and paren_depth == 0 then
      ;(function() table.insert(parts, (string.gsub(table.concat(current, ""), '^[' .. " \t" .. ']+', ''))); return parts end)()
      current = {}
      self:advance()
    else
      ;(function() table.insert(current, self:advance()); return current end)()
    end
  end
  if #parts ~= 3 then
    error({ParseError = true, message = "Expected three expressions in for ((;;))", pos = self.pos})
  end
  init = parts[0 + 1]
  cond = parts[1 + 1]
  incr = parts[2 + 1]
  self:skip_whitespace()
  if not self:at_end() and self:peek() == ";" then
    self:advance()
  end
  self:skip_whitespace_and_newlines()
  body = self:parse_loop_body("for loop")
  return ForArith:new(init, cond, incr, body, self:collect_redirects(), "for-arith")
end

function Parser:parse_select()
  local body, var_name, word, words
  self:skip_whitespace()
  if not self:lex_consume_word("select") then
    return nil
  end
  self:skip_whitespace()
  var_name = self:peek_word()
  if var_name == "" then
    error({ParseError = true, message = "Expected variable name after 'select'", pos = self:lex_peek_token().pos})
  end
  self:consume_word(var_name)
  self:skip_whitespace()
  if self:peek() == ";" then
    self:advance()
  end
  self:skip_whitespace_and_newlines()
  words = nil
  if self:lex_is_at_reserved_word("in") then
    self:lex_consume_word("in")
    self:skip_whitespace_and_newlines()
    words = {}
    while true do
      self:skip_whitespace()
      if self:at_end() then
        break
      end
      if is_semicolon_newline_brace(self:peek()) then
        if self:peek() == ";" then
          self:advance()
        end
        break
      end
      if self:lex_is_at_reserved_word("do") then
        break
      end
      word = self:parse_word(false, false, false)
      if (word == nil) then
        break
      end
      ;(function() table.insert(words, word); return words end)()
    end
  end
  self:skip_whitespace_and_newlines()
  body = self:parse_loop_body("select")
  return Select:new(var_name, words, body, self:collect_redirects(), "select")
end

function Parser:consume_case_terminator()
  local term
  term = self:lex_peek_case_terminator()
  if term ~= "" then
    self:lex_next_token()
    return term
  end
  return ";;"
end

function Parser:parse_case()
  local body, c, ch, extglob_depth, has_first_bracket_literal, is_at_terminator, is_char_class, is_empty_body, is_pattern, next_ch, paren_depth, pattern, pattern_chars, patterns, saved, sc, scan_depth, scan_pos, terminator, word
  if not self:consume_word("case") then
    return nil
  end
  self:set_state(PARSERSTATEFLAGS_PST_CASESTMT)
  self:skip_whitespace()
  word = self:parse_word(false, false, false)
  if (word == nil) then
    error({ParseError = true, message = "Expected word after 'case'", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("in") then
    error({ParseError = true, message = "Expected 'in' after case word", pos = self:lex_peek_token().pos})
  end
  self:skip_whitespace_and_newlines()
  patterns = {}
  self:set_state(PARSERSTATEFLAGS_PST_CASEPAT)
  while true do
    self:skip_whitespace_and_newlines()
    if self:lex_is_at_reserved_word("esac") then
      saved = self.pos
      self:skip_whitespace()
      while not self:at_end() and not is_metachar(self:peek()) and not is_quote(self:peek()) do
        self:advance()
      end
      self:skip_whitespace()
      is_pattern = false
      if not self:at_end() and self:peek() == ")" then
        if self.eof_token == ")" then
          is_pattern = false
        else
          self:advance()
          self:skip_whitespace()
          if not self:at_end() then
            next_ch = self:peek()
            if next_ch == ";" then
              is_pattern = true
            elseif not is_newline_or_right_paren(next_ch) then
              is_pattern = true
            end
          end
        end
      end
      self.pos = saved
      if not is_pattern then
        break
      end
    end
    self:skip_whitespace_and_newlines()
    if not self:at_end() and self:peek() == "(" then
      self:advance()
      self:skip_whitespace_and_newlines()
    end
    pattern_chars = {}
    extglob_depth = 0
    while not self:at_end() do
      ch = self:peek()
      if ch == ")" then
        if extglob_depth > 0 then
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          extglob_depth = extglob_depth - 1
        else
          self:advance()
          break
        end
      elseif ch == "\\" then
        if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "\n" then
          self:advance()
          self:advance()
        else
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          if not self:at_end() then
            ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          end
        end
      elseif is_expansion_start(self.source, self.pos, "$(") then
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        if not self:at_end() and self:peek() == "(" then
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          paren_depth = 2
          while not self:at_end() and paren_depth > 0 do
            c = self:peek()
            if c == "(" then
              paren_depth = paren_depth + 1
            elseif c == ")" then
              paren_depth = paren_depth - 1
            end
            ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          end
        else
          extglob_depth = extglob_depth + 1
        end
      elseif ch == "(" and extglob_depth > 0 then
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        extglob_depth = extglob_depth + 1
      elseif self.extglob and is_extglob_prefix(ch) and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        extglob_depth = extglob_depth + 1
      elseif ch == "[" then
        is_char_class = false
        scan_pos = self.pos + 1
        scan_depth = 0
        has_first_bracket_literal = false
        if scan_pos < self.length and is_caret_or_bang(string.sub(self.source, scan_pos + 1, scan_pos + 1)) then
          scan_pos = scan_pos + 1
        end
        if scan_pos < self.length and string.sub(self.source, scan_pos + 1, scan_pos + 1) == "]" then
          if _string_find(self.source, "]", scan_pos + 1) ~= -1 then
            scan_pos = scan_pos + 1
            has_first_bracket_literal = true
          end
        end
        while scan_pos < self.length do
          sc = string.sub(self.source, scan_pos + 1, scan_pos + 1)
          if sc == "]" and scan_depth == 0 then
            is_char_class = true
            break
          elseif sc == "[" then
            scan_depth = scan_depth + 1
          elseif sc == ")" and scan_depth == 0 then
            break
          elseif sc == "|" and scan_depth == 0 then
            break
          end
          scan_pos = scan_pos + 1
        end
        if is_char_class then
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          if not self:at_end() and is_caret_or_bang(self:peek()) then
            ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          end
          if has_first_bracket_literal and not self:at_end() and self:peek() == "]" then
            ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          end
          while not self:at_end() and self:peek() ~= "]" do
            ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          end
          if not self:at_end() then
            ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          end
        else
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        end
      elseif ch == "'" then
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        while not self:at_end() and self:peek() ~= "'" do
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        end
        if not self:at_end() then
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        end
      elseif ch == "\"" then
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        while not self:at_end() and self:peek() ~= "\"" do
          if self:peek() == "\\" and self.pos + 1 < self.length then
            ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
          end
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        end
        if not self:at_end() then
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        end
      elseif is_whitespace(ch) then
        if extglob_depth > 0 then
          ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
        else
          self:advance()
        end
      else
        ;(function() table.insert(pattern_chars, self:advance()); return pattern_chars end)()
      end
    end
    pattern = table.concat(pattern_chars, "")
    if not (pattern ~= nil and #(pattern) > 0) then
      error({ParseError = true, message = "Expected pattern in case statement", pos = self:lex_peek_token().pos})
    end
    self:skip_whitespace()
    body = nil
    is_empty_body = self:lex_peek_case_terminator() ~= ""
    if not is_empty_body then
      self:skip_whitespace_and_newlines()
      if not self:at_end() and not self:lex_is_at_reserved_word("esac") then
        is_at_terminator = self:lex_peek_case_terminator() ~= ""
        if not is_at_terminator then
          body = self:parse_list_until({["esac"] = true})
          self:skip_whitespace()
        end
      end
    end
    terminator = self:consume_case_terminator()
    self:skip_whitespace_and_newlines()
    ;(function() table.insert(patterns, CasePattern:new(pattern, body, terminator, "pattern")); return patterns end)()
  end
  self:clear_state(PARSERSTATEFLAGS_PST_CASEPAT)
  self:skip_whitespace_and_newlines()
  if not self:lex_consume_word("esac") then
    self:clear_state(PARSERSTATEFLAGS_PST_CASESTMT)
    error({ParseError = true, message = "Expected 'esac' to close case statement", pos = self:lex_peek_token().pos})
  end
  self:clear_state(PARSERSTATEFLAGS_PST_CASESTMT)
  return Case:new(word, patterns, self:collect_redirects(), "case")
end

function Parser:parse_coproc()
  local body, ch, name, next_word, potential_name, word_start
  self:skip_whitespace()
  if not self:lex_consume_word("coproc") then
    return nil
  end
  self:skip_whitespace()
  name = ""
  ch = ""
  if not self:at_end() then
    ch = self:peek()
  end
  if ch == "{" then
    body = self:parse_brace_group()
    if (body ~= nil) then
      return Coproc:new(body, name, "coproc")
    end
  end
  if ch == "(" then
    if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
      body = self:parse_arithmetic_command()
      if (body ~= nil) then
        return Coproc:new(body, name, "coproc")
      end
    end
    body = self:parse_subshell()
    if (body ~= nil) then
      return Coproc:new(body, name, "coproc")
    end
  end
  next_word = self:lex_peek_reserved_word()
  if next_word ~= "" and (_set_contains(COMPOUND_KEYWORDS, next_word)) then
    body = self:parse_compound_command()
    if (body ~= nil) then
      return Coproc:new(body, name, "coproc")
    end
  end
  word_start = self.pos
  potential_name = self:peek_word()
  if (potential_name ~= nil and #(potential_name) > 0) then
    while not self:at_end() and not is_metachar(self:peek()) and not is_quote(self:peek()) do
      self:advance()
    end
    self:skip_whitespace()
    ch = ""
    if not self:at_end() then
      ch = self:peek()
    end
    next_word = self:lex_peek_reserved_word()
    if is_valid_identifier(potential_name) then
      if ch == "{" then
        name = potential_name
        body = self:parse_brace_group()
        if (body ~= nil) then
          return Coproc:new(body, name, "coproc")
        end
      elseif ch == "(" then
        name = potential_name
        if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
          body = self:parse_arithmetic_command()
        else
          body = self:parse_subshell()
        end
        if (body ~= nil) then
          return Coproc:new(body, name, "coproc")
        end
      elseif next_word ~= "" and (_set_contains(COMPOUND_KEYWORDS, next_word)) then
        name = potential_name
        body = self:parse_compound_command()
        if (body ~= nil) then
          return Coproc:new(body, name, "coproc")
        end
      end
    end
    self.pos = word_start
  end
  body = self:parse_command()
  if (body ~= nil) then
    return Coproc:new(body, name, "coproc")
  end
  error({ParseError = true, message = "Expected command after coproc", pos = self.pos})
end

function Parser:parse_function()
  local body, brace_depth, has_whitespace, i, name, name_start, pos_after_name, saved_pos
  self:skip_whitespace()
  if self:at_end() then
    return nil
  end
  saved_pos = self.pos
  if self:lex_is_at_reserved_word("function") then
    self:lex_consume_word("function")
    self:skip_whitespace()
    name = self:peek_word()
    if name == "" then
      self.pos = saved_pos
      return nil
    end
    self:consume_word(name)
    self:skip_whitespace()
    if not self:at_end() and self:peek() == "(" then
      if self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == ")" then
        self:advance()
        self:advance()
      end
    end
    self:skip_whitespace_and_newlines()
    body = self:parse_compound_command()
    if (body == nil) then
      error({ParseError = true, message = "Expected function body", pos = self.pos})
    end
    return Function:new(name, body, "function")
  end
  name = self:peek_word()
  if name == "" or (_set_contains(RESERVED_WORDS, name)) then
    return nil
  end
  if looks_like_assignment(name) then
    return nil
  end
  self:skip_whitespace()
  name_start = self.pos
  while not self:at_end() and not is_metachar(self:peek()) and not is_quote(self:peek()) and not is_paren(self:peek()) do
    self:advance()
  end
  name = substring(self.source, name_start, self.pos)
  if not (name ~= nil and #(name) > 0) then
    self.pos = saved_pos
    return nil
  end
  brace_depth = 0
  i = 0
  while i < #name do
    if is_expansion_start(name, i, "${") then
      brace_depth = brace_depth + 1
      i = i + 2
      goto continue
    end
    if string.sub(name, i + 1, i + 1) == "}" then
      brace_depth = brace_depth - 1
    end
    i = i + 1
    ::continue::
  end
  if brace_depth > 0 then
    self.pos = saved_pos
    return nil
  end
  pos_after_name = self.pos
  self:skip_whitespace()
  has_whitespace = self.pos > pos_after_name
  if not has_whitespace and (name ~= nil and #(name) > 0) and (((string.find("*?@+!$", string.sub(name, #name - 1 + 1, #name - 1 + 1), 1, true) ~= nil))) then
    self.pos = saved_pos
    return nil
  end
  if self:at_end() or self:peek() ~= "(" then
    self.pos = saved_pos
    return nil
  end
  self:advance()
  self:skip_whitespace()
  if self:at_end() or self:peek() ~= ")" then
    self.pos = saved_pos
    return nil
  end
  self:advance()
  self:skip_whitespace_and_newlines()
  body = self:parse_compound_command()
  if (body == nil) then
    error({ParseError = true, message = "Expected function body", pos = self.pos})
  end
  return Function:new(name, body, "function")
end

function Parser:parse_compound_command()
  local result
  result = self:parse_brace_group()
  if (result ~= nil) then
    return result
  end
  if not self:at_end() and self:peek() == "(" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
    result = self:parse_arithmetic_command()
    if (result ~= nil) then
      return result
    end
  end
  result = self:parse_subshell()
  if (result ~= nil) then
    return result
  end
  result = self:parse_conditional_expr()
  if (result ~= nil) then
    return result
  end
  result = self:parse_if()
  if (result ~= nil) then
    return result
  end
  result = self:parse_while()
  if (result ~= nil) then
    return result
  end
  result = self:parse_until()
  if (result ~= nil) then
    return result
  end
  result = self:parse_for()
  if (result ~= nil) then
    return result
  end
  result = self:parse_case()
  if (result ~= nil) then
    return result
  end
  result = self:parse_select()
  if (result ~= nil) then
    return result
  end
  return nil
end

function Parser:at_list_until_terminator(stop_words)
  local next_pos, reserved
  if self:at_end() then
    return true
  end
  if self:peek() == ")" then
    return true
  end
  if self:peek() == "}" then
    next_pos = self.pos + 1
    if next_pos >= self.length or is_word_end_context(string.sub(self.source, next_pos + 1, next_pos + 1)) then
      return true
    end
  end
  reserved = self:lex_peek_reserved_word()
  if reserved ~= "" and (_set_contains(stop_words, reserved)) then
    return true
  end
  if self:lex_peek_case_terminator() ~= "" then
    return true
  end
  return false
end

function Parser:parse_list_until(stop_words)
  local next_op, op, parts, pipeline, reserved
  self:skip_whitespace_and_newlines()
  reserved = self:lex_peek_reserved_word()
  if reserved ~= "" and (_set_contains(stop_words, reserved)) then
    return nil
  end
  pipeline = self:parse_pipeline()
  if (pipeline == nil) then
    return nil
  end
  parts = {pipeline}
  while true do
    self:skip_whitespace()
    op = self:parse_list_operator()
    if op == "" then
      if not self:at_end() and self:peek() == "\n" then
        self:advance()
        self:gather_heredoc_bodies()
        if self.cmdsub_heredoc_end ~= -1 and self.cmdsub_heredoc_end > self.pos then
          self.pos = self.cmdsub_heredoc_end
          self.cmdsub_heredoc_end = -1
        end
        self:skip_whitespace_and_newlines()
        if self:at_list_until_terminator(stop_words) then
          break
        end
        next_op = self:peek_list_operator()
        if next_op == "&" or next_op == ";" then
          break
        end
        op = "\n"
      else
        break
      end
    end
    if op == "" then
      break
    end
    if op == ";" then
      self:skip_whitespace_and_newlines()
      if self:at_list_until_terminator(stop_words) then
        break
      end
      ;(function() table.insert(parts, Operator:new(op, "operator")); return parts end)()
    elseif op == "&" then
      ;(function() table.insert(parts, Operator:new(op, "operator")); return parts end)()
      self:skip_whitespace_and_newlines()
      if self:at_list_until_terminator(stop_words) then
        break
      end
    elseif op == "&&" or op == "||" then
      ;(function() table.insert(parts, Operator:new(op, "operator")); return parts end)()
      self:skip_whitespace_and_newlines()
    else
      ;(function() table.insert(parts, Operator:new(op, "operator")); return parts end)()
    end
    if self:at_list_until_terminator(stop_words) then
      break
    end
    pipeline = self:parse_pipeline()
    if (pipeline == nil) then
      error({ParseError = true, message = "Expected command after " .. op, pos = self.pos})
    end
    ;(function() table.insert(parts, pipeline); return parts end)()
  end
  if #parts == 1 then
    return parts[0 + 1]
  end
  return List:new(parts, "list")
end

function Parser:parse_compound_command()
  local ch, func, keyword_word, reserved, result, word
  self:skip_whitespace()
  if self:at_end() then
    return nil
  end
  ch = self:peek()
  if ch == "(" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "(" then
    result = self:parse_arithmetic_command()
    if (result ~= nil) then
      return result
    end
  end
  if ch == "(" then
    return self:parse_subshell()
  end
  if ch == "{" then
    result = self:parse_brace_group()
    if (result ~= nil) then
      return result
    end
  end
  if ch == "[" and self.pos + 1 < self.length and string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1) == "[" then
    result = self:parse_conditional_expr()
    if (result ~= nil) then
      return result
    end
  end
  reserved = self:lex_peek_reserved_word()
  if reserved == "" and self.in_process_sub then
    word = self:peek_word()
    if word ~= "" and #word > 1 and string.sub(word, 0 + 1, 0 + 1) == "}" then
      keyword_word = string.sub(word, (1) + 1, #word)
      if (_set_contains(RESERVED_WORDS, keyword_word)) or keyword_word == "{" or keyword_word == "}" or keyword_word == "[[" or keyword_word == "]]" or keyword_word == "!" or keyword_word == "time" then
        reserved = keyword_word
      end
    end
  end
  if reserved == "fi" or reserved == "then" or reserved == "elif" or reserved == "else" or reserved == "done" or reserved == "esac" or reserved == "do" or reserved == "in" then
    error({ParseError = true, message = string.format("Unexpected reserved word '%s'", reserved), pos = self:lex_peek_token().pos})
  end
  if reserved == "if" then
    return self:parse_if()
  end
  if reserved == "while" then
    return self:parse_while()
  end
  if reserved == "until" then
    return self:parse_until()
  end
  if reserved == "for" then
    return self:parse_for()
  end
  if reserved == "select" then
    return self:parse_select()
  end
  if reserved == "case" then
    return self:parse_case()
  end
  if reserved == "function" then
    return self:parse_function()
  end
  if reserved == "coproc" then
    return self:parse_coproc()
  end
  func = self:parse_function()
  if (func ~= nil) then
    return func
  end
  return self:parse_command()
end

function Parser:parse_pipeline()
  local inner, prefix_order, result, saved, time_posix
  self:skip_whitespace()
  prefix_order = ""
  time_posix = false
  if self:lex_is_at_reserved_word("time") then
    self:lex_consume_word("time")
    prefix_order = "time"
    self:skip_whitespace()
    if not self:at_end() and self:peek() == "-" then
      saved = self.pos
      self:advance()
      if not self:at_end() and self:peek() == "p" then
        self:advance()
        if self:at_end() or is_metachar(self:peek()) then
          time_posix = true
        else
          self.pos = saved
        end
      else
        self.pos = saved
      end
    end
    self:skip_whitespace()
    if not self:at_end() and starts_with_at(self.source, self.pos, "--") then
      if self.pos + 2 >= self.length or is_whitespace(string.sub(self.source, self.pos + 2 + 1, self.pos + 2 + 1)) then
        self:advance()
        self:advance()
        time_posix = true
        self:skip_whitespace()
      end
    end
    while self:lex_is_at_reserved_word("time") do
      self:lex_consume_word("time")
      self:skip_whitespace()
      if not self:at_end() and self:peek() == "-" then
        saved = self.pos
        self:advance()
        if not self:at_end() and self:peek() == "p" then
          self:advance()
          if self:at_end() or is_metachar(self:peek()) then
            time_posix = true
          else
            self.pos = saved
          end
        else
          self.pos = saved
        end
      end
    end
    self:skip_whitespace()
    if not self:at_end() and self:peek() == "!" then
      if (self.pos + 1 >= self.length or is_negation_boundary(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1))) and not self:is_bang_followed_by_procsub() then
        self:advance()
        prefix_order = "time_negation"
        self:skip_whitespace()
      end
    end
  elseif not self:at_end() and self:peek() == "!" then
    if (self.pos + 1 >= self.length or is_negation_boundary(string.sub(self.source, self.pos + 1 + 1, self.pos + 1 + 1))) and not self:is_bang_followed_by_procsub() then
      self:advance()
      self:skip_whitespace()
      inner = self:parse_pipeline()
      if (inner ~= nil) and inner.kind == "negation" then
        if (inner.pipeline ~= nil) then
          return inner.pipeline
        else
          return Command:new({}, nil, "command")
        end
      end
      return Negation:new(inner, "negation")
    end
  end
  result = self:parse_simple_pipeline()
  if prefix_order == "time" then
    result = Time:new(result, time_posix, "time")
  elseif prefix_order == "negation" then
    result = Negation:new(result, "negation")
  elseif prefix_order == "time_negation" then
    result = Time:new(result, time_posix, "time")
    result = Negation:new(result, "negation")
  elseif prefix_order == "negation_time" then
    result = Time:new(result, time_posix, "time")
    result = Negation:new(result, "negation")
  elseif (result == nil) then
    return nil
  end
  return result
end

function Parser:parse_simple_pipeline()
  local cmd, commands, is_pipe_both, token_type, value
  cmd = self:parse_compound_command()
  if (cmd == nil) then
    return nil
  end
  commands = {cmd}
  while true do
    self:skip_whitespace()
    token_type, value = table.unpack(self:lex_peek_operator())
    if token_type == 0 then
      break
    end
    if token_type ~= TOKENTYPE_PIPE and token_type ~= TOKENTYPE_PIPE_AMP then
      break
    end
    self:lex_next_token()
    is_pipe_both = token_type == TOKENTYPE_PIPE_AMP
    self:skip_whitespace_and_newlines()
    if is_pipe_both then
      ;(function() table.insert(commands, PipeBoth:new("pipe-both")); return commands end)()
    end
    cmd = self:parse_compound_command()
    if (cmd == nil) then
      error({ParseError = true, message = "Expected command after |", pos = self.pos})
    end
    ;(function() table.insert(commands, cmd); return commands end)()
  end
  if #commands == 1 then
    return commands[0 + 1]
  end
  return Pipeline:new(commands, "pipeline")
end

function Parser:parse_list_operator()
  local token_type
  self:skip_whitespace()
  token_type, _ = table.unpack(self:lex_peek_operator())
  if token_type == 0 then
    return ""
  end
  if token_type == TOKENTYPE_AND_AND then
    self:lex_next_token()
    return "&&"
  end
  if token_type == TOKENTYPE_OR_OR then
    self:lex_next_token()
    return "||"
  end
  if token_type == TOKENTYPE_SEMI then
    self:lex_next_token()
    return ";"
  end
  if token_type == TOKENTYPE_AMP then
    self:lex_next_token()
    return "&"
  end
  return ""
end

function Parser:peek_list_operator()
  local op, saved_pos
  saved_pos = self.pos
  op = self:parse_list_operator()
  self.pos = saved_pos
  return op
end

function Parser:parse_list(newline_as_separator)
  local next_op, op, parts, pipeline
  if newline_as_separator then
    self:skip_whitespace_and_newlines()
  else
    self:skip_whitespace()
  end
  pipeline = self:parse_pipeline()
  if (pipeline == nil) then
    return nil
  end
  parts = {pipeline}
  if self:in_state(PARSERSTATEFLAGS_PST_EOFTOKEN) and self:at_eof_token() then
    return (#parts == 1 and parts[0 + 1] or List:new(parts, "list"))
  end
  while true do
    self:skip_whitespace()
    op = self:parse_list_operator()
    if op == "" then
      if not self:at_end() and self:peek() == "\n" then
        if not newline_as_separator then
          break
        end
        self:advance()
        self:gather_heredoc_bodies()
        if self.cmdsub_heredoc_end ~= -1 and self.cmdsub_heredoc_end > self.pos then
          self.pos = self.cmdsub_heredoc_end
          self.cmdsub_heredoc_end = -1
        end
        self:skip_whitespace_and_newlines()
        if self:at_end() or self:at_list_terminating_bracket() then
          break
        end
        next_op = self:peek_list_operator()
        if next_op == "&" or next_op == ";" then
          break
        end
        op = "\n"
      else
        break
      end
    end
    if op == "" then
      break
    end
    ;(function() table.insert(parts, Operator:new(op, "operator")); return parts end)()
    if op == "&&" or op == "||" then
      self:skip_whitespace_and_newlines()
    elseif op == "&" then
      self:skip_whitespace()
      if self:at_end() or self:at_list_terminating_bracket() then
        break
      end
      if self:peek() == "\n" then
        if newline_as_separator then
          self:skip_whitespace_and_newlines()
          if self:at_end() or self:at_list_terminating_bracket() then
            break
          end
        else
          break
        end
      end
    elseif op == ";" then
      self:skip_whitespace()
      if self:at_end() or self:at_list_terminating_bracket() then
        break
      end
      if self:peek() == "\n" then
        if newline_as_separator then
          self:skip_whitespace_and_newlines()
          if self:at_end() or self:at_list_terminating_bracket() then
            break
          end
        else
          break
        end
      end
    end
    pipeline = self:parse_pipeline()
    if (pipeline == nil) then
      error({ParseError = true, message = "Expected command after " .. op, pos = self.pos})
    end
    ;(function() table.insert(parts, pipeline); return parts end)()
    if self:in_state(PARSERSTATEFLAGS_PST_EOFTOKEN) and self:at_eof_token() then
      break
    end
  end
  if #parts == 1 then
    return parts[0 + 1]
  end
  return List:new(parts, "list")
end

function Parser:parse_comment()
  local start, text
  if self:at_end() or self:peek() ~= "#" then
    return nil
  end
  start = self.pos
  while not self:at_end() and self:peek() ~= "\n" do
    self:advance()
  end
  text = substring(self.source, start, self.pos)
  return Comment:new(text, "comment")
end

function Parser:parse()
  local comment, found_newline, result, results, source
  source = (string.gsub((string.gsub(self.source, '^[' .. " \t\n\r" .. ']+', '')), '[' .. " \t\n\r" .. ']+$', ''))
  if not (source ~= nil and #(source) > 0) then
    return {Empty:new("empty")}
  end
  results = {}
  while true do
    self:skip_whitespace()
    while not self:at_end() and self:peek() == "\n" do
      self:advance()
    end
    if self:at_end() then
      break
    end
    comment = self:parse_comment()
    if not (comment ~= nil) then
      break
    end
  end
  while not self:at_end() do
    result = self:parse_list(false)
    if (result ~= nil) then
      ;(function() table.insert(results, result); return results end)()
    end
    self:skip_whitespace()
    found_newline = false
    while not self:at_end() and self:peek() == "\n" do
      found_newline = true
      self:advance()
      self:gather_heredoc_bodies()
      if self.cmdsub_heredoc_end ~= -1 and self.cmdsub_heredoc_end > self.pos then
        self.pos = self.cmdsub_heredoc_end
        self.cmdsub_heredoc_end = -1
      end
      self:skip_whitespace()
    end
    if not found_newline and not self:at_end() then
      error({ParseError = true, message = "Syntax error", pos = self.pos})
    end
  end
  if not (#(results) > 0) then
    return {Empty:new("empty")}
  end
  if self.saw_newline_in_single_quote and (self.source ~= nil and #(self.source) > 0) and string.sub(self.source, #self.source - 1 + 1, #self.source - 1 + 1) == "\\" and not (#self.source >= 3 and string.sub(self.source, (#self.source - 3) + 1, #self.source - 1) == "\\\n") then
    if not self:last_word_on_own_line(results) then
      self:strip_trailing_backslash_from_last_word(results)
    end
  end
  return results
end

function Parser:last_word_on_own_line(nodes)
  return #nodes >= 2
end

function Parser:strip_trailing_backslash_from_last_word(nodes)
  local last_node, last_word
  if not (#(nodes) > 0) then
    return
  end
  last_node = nodes[#nodes - 1 + 1]
  last_word = self:find_last_word(last_node)
  if (last_word ~= nil) and (string.sub(last_word.value, -#"\\") == "\\") then
    last_word.value = substring(last_word.value, 0, #last_word.value - 1)
    if not (last_word.value ~= nil and #(last_word.value) > 0) and (type(last_node) == 'table' and getmetatable(last_node) == Command) and (last_node.words ~= nil) then
      table.remove(last_node.words)
    end
  end
end

function Parser:find_last_word(node)
  local last_redirect, last_word
  if (type(node) == 'table' and getmetatable(node) == Word) then
    local node = node
    return node
  end
  if (type(node) == 'table' and getmetatable(node) == Command) then
    local node = node
    if (#(node.words) > 0) then
      last_word = node.words[#node.words - 1 + 1]
      if (string.sub(last_word.value, -#"\\") == "\\") then
        return last_word
      end
    end
    if (#(node.redirects) > 0) then
      last_redirect = node.redirects[#node.redirects - 1 + 1]
      if (type(last_redirect) == 'table' and getmetatable(last_redirect) == Redirect) then
        local last_redirect = last_redirect
        return last_redirect.target
      end
    end
    if (#(node.words) > 0) then
      return node.words[#node.words - 1 + 1]
    end
  end
  if (type(node) == 'table' and getmetatable(node) == Pipeline) then
    local node = node
    if (#(node.commands) > 0) then
      return self:find_last_word(node.commands[#node.commands - 1 + 1])
    end
  end
  if (type(node) == 'table' and getmetatable(node) == List) then
    local node = node
    if (#(node.parts) > 0) then
      return self:find_last_word(node.parts[#node.parts - 1 + 1])
    end
  end
  return nil
end

function is_hex_digit(c)
  return c >= "0" and c <= "9" or c >= "a" and c <= "f" or c >= "A" and c <= "F"
end

function is_octal_digit(c)
  return c >= "0" and c <= "7"
end

function get_ansi_escape(c)
  return _map_get(ANSI_C_ESCAPES, c, -1)
end

function is_whitespace(c)
  return c == " " or c == "\t" or c == "\n"
end

function string_to_bytes(s)
  return (function() local t = {}; for i, v in ipairs(({string.byte(s, 1, -1)})) do t[i] = v end; return t end)()
end

function is_whitespace_no_newline(c)
  return c == " " or c == "\t"
end

function substring(s, start, end_)
  return string.sub(s, (start) + 1, end_)
end

function starts_with_at(s, pos, prefix)
  return (string.sub(s, pos + 1, pos + #prefix) == prefix)
end

function count_consecutive_dollars_before(s, pos)
  local bs_count, count, j, k
  count = 0
  k = pos - 1
  while k >= 0 and string.sub(s, k + 1, k + 1) == "$" do
    bs_count = 0
    j = k - 1
    while j >= 0 and string.sub(s, j + 1, j + 1) == "\\" do
      bs_count = bs_count + 1
      j = j - 1
    end
    if bs_count % 2 == 1 then
      break
    end
    count = count + 1
    k = k - 1
  end
  return count
end

function is_expansion_start(s, pos, delimiter)
  if not starts_with_at(s, pos, delimiter) then
    return false
  end
  return count_consecutive_dollars_before(s, pos) % 2 == 0
end

function sublist(lst, start, end_)
  return _table_slice(lst, (start) + 1, end_)
end

function repeat_str(s, n)
  local i, result
  result = {}
  i = 0
  while i < n do
    ;(function() table.insert(result, s); return result end)()
    i = i + 1
  end
  return table.concat(result, "")
end

function strip_line_continuations_comment_aware(text)
  local c, i, in_comment, j, num_preceding_backslashes, quote, result
  result = {}
  i = 0
  in_comment = false
  quote = new_quote_state()
  while i < #text do
    c = string.sub(text, i + 1, i + 1)
    if c == "\\" and i + 1 < #text and string.sub(text, i + 1 + 1, i + 1 + 1) == "\n" then
      num_preceding_backslashes = 0
      j = i - 1
      while j >= 0 and string.sub(text, j + 1, j + 1) == "\\" do
        num_preceding_backslashes = num_preceding_backslashes + 1
        j = j - 1
      end
      if num_preceding_backslashes % 2 == 0 then
        if in_comment then
          ;(function() table.insert(result, "\n"); return result end)()
        end
        i = i + 2
        in_comment = false
        goto continue
      end
    end
    if c == "\n" then
      in_comment = false
      ;(function() table.insert(result, c); return result end)()
      i = i + 1
      goto continue
    end
    if c == "'" and not quote.double and not in_comment then
      quote.single = not quote.single
    elseif c == "\"" and not quote.single and not in_comment then
      quote.double = not quote.double
    elseif c == "#" and not quote.single and not in_comment then
      in_comment = true
    end
    ;(function() table.insert(result, c); return result end)()
    i = i + 1
    ::continue::
  end
  return table.concat(result, "")
end

function append_redirects(base, redirects)
  local parts, r
  if (#(redirects) > 0) then
    parts = {}
    for _, r in ipairs(redirects) do
      ;(function() table.insert(parts, r:to_sexp()); return parts end)()
    end
    return base .. " " .. table.concat(parts, " ")
  end
  return base
end

function format_arith_val(s)
  local val, w
  w = Word:new(s, {}, "word")
  val = w:expand_all_ansi_c_quotes(s)
  val = w:strip_locale_string_dollars(val)
  val = w:format_command_substitutions(val, false)
  val = (string.gsub((string.gsub(val, "\\", "\\\\")), "\"", "\\\""))
  val = (string.gsub((string.gsub(val, "\n", "\\n")), "\t", "\\t"))
  return val
end

function consume_single_quote(s, start)
  local chars, i
  chars = {"'"}
  i = start + 1
  while i < #s and string.sub(s, i + 1, i + 1) ~= "'" do
    ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
    i = i + 1
  end
  if i < #s then
    ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
    i = i + 1
  end
  return {i, chars}
end

function consume_double_quote(s, start)
  local chars, i
  chars = {"\""}
  i = start + 1
  while i < #s and string.sub(s, i + 1, i + 1) ~= "\"" do
    if string.sub(s, i + 1, i + 1) == "\\" and i + 1 < #s then
      ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
      i = i + 1
    end
    ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
    i = i + 1
  end
  if i < #s then
    ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
    i = i + 1
  end
  return {i, chars}
end

function has_bracket_close(s, start, depth)
  local i
  i = start
  while i < #s do
    if string.sub(s, i + 1, i + 1) == "]" then
      return true
    end
    if (string.sub(s, i + 1, i + 1) == "|" or string.sub(s, i + 1, i + 1) == ")") and depth == 0 then
      return false
    end
    i = i + 1
  end
  return false
end

function consume_bracket_class(s, start, depth)
  local chars, i, is_bracket, scan_pos
  scan_pos = start + 1
  if scan_pos < #s and (string.sub(s, scan_pos + 1, scan_pos + 1) == "!" or string.sub(s, scan_pos + 1, scan_pos + 1) == "^") then
    scan_pos = scan_pos + 1
  end
  if scan_pos < #s and string.sub(s, scan_pos + 1, scan_pos + 1) == "]" then
    if has_bracket_close(s, scan_pos + 1, depth) then
      scan_pos = scan_pos + 1
    end
  end
  is_bracket = false
  while scan_pos < #s do
    if string.sub(s, scan_pos + 1, scan_pos + 1) == "]" then
      is_bracket = true
      break
    end
    if string.sub(s, scan_pos + 1, scan_pos + 1) == ")" and depth == 0 then
      break
    end
    if string.sub(s, scan_pos + 1, scan_pos + 1) == "|" and depth == 0 then
      break
    end
    scan_pos = scan_pos + 1
  end
  if not is_bracket then
    return {start + 1, {"["}, false}
  end
  chars = {"["}
  i = start + 1
  if i < #s and (string.sub(s, i + 1, i + 1) == "!" or string.sub(s, i + 1, i + 1) == "^") then
    ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
    i = i + 1
  end
  if i < #s and string.sub(s, i + 1, i + 1) == "]" then
    if has_bracket_close(s, i + 1, depth) then
      ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
      i = i + 1
    end
  end
  while i < #s and string.sub(s, i + 1, i + 1) ~= "]" do
    ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
    i = i + 1
  end
  if i < #s then
    ;(function() table.insert(chars, string.sub(s, i + 1, i + 1)); return chars end)()
    i = i + 1
  end
  return {i, chars, true}
end

function format_cond_body(node)
  local kind, left_val, operand_val, right_val
  kind = node.kind
  if kind == "unary-test" then
    operand_val = node.operand:get_cond_formatted_value()
    return node.op .. " " .. operand_val
  end
  if kind == "binary-test" then
    left_val = node.left:get_cond_formatted_value()
    right_val = node.right:get_cond_formatted_value()
    return left_val .. " " .. node.op .. " " .. right_val
  end
  if kind == "cond-and" then
    return format_cond_body(node.left) .. " && " .. format_cond_body(node.right)
  end
  if kind == "cond-or" then
    return format_cond_body(node.left) .. " || " .. format_cond_body(node.right)
  end
  if kind == "cond-not" then
    return "! " .. format_cond_body(node.operand)
  end
  if kind == "cond-paren" then
    return "( " .. format_cond_body(node.inner) .. " )"
  end
  return ""
end

function starts_with_subshell(node)
  local p
  if (type(node) == 'table' and getmetatable(node) == Subshell) then
    local node = node
    return true
  end
  if (type(node) == 'table' and getmetatable(node) == List) then
    local node = node
    for _, p in ipairs(node.parts) do
      if p.kind ~= "operator" then
        return starts_with_subshell(p)
      end
    end
    return false
  end
  if (type(node) == 'table' and getmetatable(node) == Pipeline) then
    local node = node
    if (#(node.commands) > 0) then
      return starts_with_subshell(node.commands[0 + 1])
    end
    return false
  end
  return false
end

function format_cmdsub_node(node, indent, in_procsub, compact_redirects, procsub_first)
  local entry, body, body_part, cmd, cmd_count, cmds, compact_pipe, cond, else_body, first_nl, formatted, formatted_cmd, h, has_heredoc, heredocs, i, idx, inner_body, inner_sp, is_last, last, name, needs_redirect, p, part, parts, pat, pat_indent, pattern_str, patterns, prefix, r, redirect_parts, redirects, result, result_parts, s, skipped_semi, sp, term, term_indent, terminator, then_body, val, var, w, word, word_parts, word_vals, words
  if (node == nil) then
    return ""
  end
  sp = repeat_str(" ", indent)
  inner_sp = repeat_str(" ", indent + 4)
  if (type(node) == 'table' and getmetatable(node) == ArithEmpty) then
    local node = node
    return ""
  end
  if (type(node) == 'table' and getmetatable(node) == Command) then
    local node = node
    parts = {}
    for _, w in ipairs(node.words) do
      val = w:expand_all_ansi_c_quotes(w.value)
      val = w:strip_locale_string_dollars(val)
      val = w:normalize_array_whitespace(val)
      val = w:format_command_substitutions(val, false)
      ;(function() table.insert(parts, val); return parts end)()
    end
    heredocs = {}
    for _, r in ipairs(node.redirects) do
      if (type(r) == 'table' and getmetatable(r) == HereDoc) then
        local r = r
        ;(function() table.insert(heredocs, r); return heredocs end)()
      end
    end
    for _, r in ipairs(node.redirects) do
      ;(function() table.insert(parts, format_redirect(r, compact_redirects, true)); return parts end)()
    end
    if compact_redirects and (#(node.words) > 0) and (#(node.redirects) > 0) then
      word_parts = _table_slice(parts, 1, #node.words)
      redirect_parts = _table_slice(parts, (#node.words) + 1, #parts)
      result = table.concat(word_parts, " ") .. table.concat(redirect_parts, "")
    else
      result = table.concat(parts, " ")
    end
    for _, h in ipairs(heredocs) do
      result = result .. format_heredoc_body(h)
    end
    return result
  end
  if (type(node) == 'table' and getmetatable(node) == Pipeline) then
    local node = node
    cmds = {}
    i = 0
    while i < #node.commands do
      cmd = node.commands[i + 1]
      if (type(cmd) == 'table' and getmetatable(cmd) == PipeBoth) then
        local cmd = cmd
        i = i + 1
        goto continue
      end
      needs_redirect = i + 1 < #node.commands and node.commands[i + 1 + 1].kind == "pipe-both"
      ;(function() table.insert(cmds, {cmd, needs_redirect}); return cmds end)()
      i = i + 1
      ::continue::
    end
    result_parts = {}
    idx = 0
    while idx < #cmds do
      entry = cmds[idx + 1]
      cmd = entry[1]
      needs_redirect = entry[2]
      formatted = format_cmdsub_node(cmd, indent, in_procsub, false, procsub_first and idx == 0)
      is_last = idx == #cmds - 1
      has_heredoc = false
      if cmd.kind == "command" and (cmd.redirects ~= nil) then
        for _, r in ipairs(cmd.redirects) do
          if (type(r) == 'table' and getmetatable(r) == HereDoc) then
            local r = r
            has_heredoc = true
            break
          end
        end
      end
      if needs_redirect then
        if has_heredoc then
          first_nl = _string_find(formatted, "\n")
          if first_nl ~= -1 then
            formatted = string.sub(formatted, 1, first_nl) .. " 2>&1" .. string.sub(formatted, (first_nl) + 1, #formatted)
          else
            formatted = formatted .. " 2>&1"
          end
        else
          formatted = formatted .. " 2>&1"
        end
      end
      if not is_last and has_heredoc then
        first_nl = _string_find(formatted, "\n")
        if first_nl ~= -1 then
          formatted = string.sub(formatted, 1, first_nl) .. " |" .. string.sub(formatted, (first_nl) + 1, #formatted)
        end
        ;(function() table.insert(result_parts, formatted); return result_parts end)()
      else
        ;(function() table.insert(result_parts, formatted); return result_parts end)()
      end
      idx = idx + 1
    end
    compact_pipe = in_procsub and (#(cmds) > 0) and cmds[0 + 1][1].kind == "subshell"
    result = ""
    idx = 0
    while idx < #result_parts do
      part = result_parts[idx + 1]
      if idx > 0 then
        if (string.sub(result, -#"\n") == "\n") then
          result = result .. "  " .. part
        elseif compact_pipe then
          result = result .. "|" .. part
        else
          result = result .. " | " .. part
        end
      else
        result = part
      end
      idx = idx + 1
    end
    return result
  end
  if (type(node) == 'table' and getmetatable(node) == List) then
    local node = node
    has_heredoc = false
    for _, p in ipairs(node.parts) do
      if p.kind == "command" and (p.redirects ~= nil) then
        for _, r in ipairs(p.redirects) do
          if (type(r) == 'table' and getmetatable(r) == HereDoc) then
            local r = r
            has_heredoc = true
            break
          end
        end
      else
        if (type(p) == 'table' and getmetatable(p) == Pipeline) then
          local p = p
          for _, cmd in ipairs(p.commands) do
            if cmd.kind == "command" and (cmd.redirects ~= nil) then
              for _, r in ipairs(cmd.redirects) do
                if (type(r) == 'table' and getmetatable(r) == HereDoc) then
                  local r = r
                  has_heredoc = true
                  break
                end
              end
            end
            if has_heredoc then
              break
            end
          end
        end
      end
    end
    result = {}
    skipped_semi = false
    cmd_count = 0
    for _, p in ipairs(node.parts) do
      if (type(p) == 'table' and getmetatable(p) == Operator) then
        local p = p
        if p.op == ";" then
          if (#(result) > 0) and (string.sub(result[#result - 1 + 1], -#"\n") == "\n") then
            skipped_semi = true
            goto continue
          end
          if #result >= 3 and result[#result - 2 + 1] == "\n" and (string.sub(result[#result - 3 + 1], -#"\n") == "\n") then
            skipped_semi = true
            goto continue
          end
          ;(function() table.insert(result, ";"); return result end)()
          skipped_semi = false
        elseif p.op == "\n" then
          if (#(result) > 0) and result[#result - 1 + 1] == ";" then
            skipped_semi = false
            goto continue
          end
          if (#(result) > 0) and (string.sub(result[#result - 1 + 1], -#"\n") == "\n") then
            ;(function() table.insert(result, (skipped_semi and " " or "\n")); return result end)()
            skipped_semi = false
            goto continue
          end
          ;(function() table.insert(result, "\n"); return result end)()
          skipped_semi = false
        elseif p.op == "&" then
          if (#(result) > 0) and (((string.find(result[#result - 1 + 1], "<<", 1, true) ~= nil))) and (((string.find(result[#result - 1 + 1], "\n", 1, true) ~= nil))) then
            last = result[#result - 1 + 1]
            if (((string.find(last, " |", 1, true) ~= nil))) or (string.sub(last, 1, #"|") == "|") then
              result[#result - 1 + 1] = last .. " &"
            else
              first_nl = _string_find(last, "\n")
              result[#result - 1 + 1] = string.sub(last, 1, first_nl) .. " &" .. string.sub(last, (first_nl) + 1, #last)
            end
          else
            ;(function() table.insert(result, " &"); return result end)()
          end
        elseif (#(result) > 0) and (((string.find(result[#result - 1 + 1], "<<", 1, true) ~= nil))) and (((string.find(result[#result - 1 + 1], "\n", 1, true) ~= nil))) then
          last = result[#result - 1 + 1]
          first_nl = _string_find(last, "\n")
          result[#result - 1 + 1] = string.sub(last, 1, first_nl) .. " " .. p.op .. " " .. string.sub(last, (first_nl) + 1, #last)
        else
          ;(function() table.insert(result, " " .. p.op); return result end)()
        end
      else
        if (#(result) > 0) and not (string.sub(result[#result - 1 + 1], -#" ") == " " or string.sub(result[#result - 1 + 1], -#"\n") == "\n") then
          ;(function() table.insert(result, " "); return result end)()
        end
        formatted_cmd = format_cmdsub_node(p, indent, in_procsub, compact_redirects, procsub_first and cmd_count == 0)
        if #result > 0 then
          last = result[#result - 1 + 1]
          if (((string.find(last, " || \n", 1, true) ~= nil))) or (((string.find(last, " && \n", 1, true) ~= nil))) then
            formatted_cmd = " " .. formatted_cmd
          end
        end
        if skipped_semi then
          formatted_cmd = " " .. formatted_cmd
          skipped_semi = false
        end
        ;(function() table.insert(result, formatted_cmd); return result end)()
        cmd_count = cmd_count + 1
      end
      ::continue::
    end
    s = table.concat(result, "")
    if (((string.find(s, " &\n", 1, true) ~= nil))) and (string.sub(s, -#"\n") == "\n") then
      return s .. " "
    end
    while (string.sub(s, -#";") == ";") do
      s = substring(s, 0, #s - 1)
    end
    if not has_heredoc then
      while (string.sub(s, -#"\n") == "\n") do
        s = substring(s, 0, #s - 1)
      end
    end
    return s
  end
  if (type(node) == 'table' and getmetatable(node) == If) then
    local node = node
    cond = format_cmdsub_node(node.condition, indent, false, false, false)
    then_body = format_cmdsub_node(node.then_body, indent + 4, false, false, false)
    result = "if " .. cond .. "; then\n" .. inner_sp .. then_body .. ";"
    if (node.else_body ~= nil) then
      else_body = format_cmdsub_node(node.else_body, indent + 4, false, false, false)
      result = result .. "\n" .. sp .. "else\n" .. inner_sp .. else_body .. ";"
    end
    result = result .. "\n" .. sp .. "fi"
    return result
  end
  if (type(node) == 'table' and getmetatable(node) == While) then
    local node = node
    cond = format_cmdsub_node(node.condition, indent, false, false, false)
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    result = "while " .. cond .. "; do\n" .. inner_sp .. body .. ";\n" .. sp .. "done"
    if (#(node.redirects) > 0) then
      for _, r in ipairs(node.redirects) do
        result = result .. " " .. format_redirect(r, false, false)
      end
    end
    return result
  end
  if (type(node) == 'table' and getmetatable(node) == Until) then
    local node = node
    cond = format_cmdsub_node(node.condition, indent, false, false, false)
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    result = "until " .. cond .. "; do\n" .. inner_sp .. body .. ";\n" .. sp .. "done"
    if (#(node.redirects) > 0) then
      for _, r in ipairs(node.redirects) do
        result = result .. " " .. format_redirect(r, false, false)
      end
    end
    return result
  end
  if (type(node) == 'table' and getmetatable(node) == For) then
    local node = node
    var = node.var
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    if (node.words ~= nil) then
      word_vals = {}
      for _, w in ipairs(node.words) do
        ;(function() table.insert(word_vals, w.value); return word_vals end)()
      end
      words = table.concat(word_vals, " ")
      if (words ~= nil and #(words) > 0) then
        result = "for " .. var .. " in " .. words .. ";\n" .. sp .. "do\n" .. inner_sp .. body .. ";\n" .. sp .. "done"
      else
        result = "for " .. var .. " in ;\n" .. sp .. "do\n" .. inner_sp .. body .. ";\n" .. sp .. "done"
      end
    else
      result = "for " .. var .. " in \"$@\";\n" .. sp .. "do\n" .. inner_sp .. body .. ";\n" .. sp .. "done"
    end
    if (#(node.redirects) > 0) then
      for _, r in ipairs(node.redirects) do
        result = result .. " " .. format_redirect(r, false, false)
      end
    end
    return result
  end
  if (type(node) == 'table' and getmetatable(node) == ForArith) then
    local node = node
    body = format_cmdsub_node(node.body, indent + 4, false, false, false)
    result = "for ((" .. node.init .. "; " .. node.cond .. "; " .. node.incr .. "))\ndo\n" .. inner_sp .. body .. ";\n" .. sp .. "done"
    if (#(node.redirects) > 0) then
      for _, r in ipairs(node.redirects) do
        result = result .. " " .. format_redirect(r, false, false)
      end
    end
    return result
  end
  if (type(node) == 'table' and getmetatable(node) == Case) then
    local node = node
    word = node.word.value
    patterns = {}
    i = 0
    while i < #node.patterns do
      p = node.patterns[i + 1]
      pat = (string.gsub(p.pattern, "|", " | "))
      if (p.body ~= nil) then
        body = format_cmdsub_node(p.body, indent + 8, false, false, false)
      else
        body = ""
      end
      term = p.terminator
      pat_indent = repeat_str(" ", indent + 8)
      term_indent = repeat_str(" ", indent + 4)
      body_part = ((body ~= nil and #(body) > 0) and pat_indent .. body .. "\n" or "\n")
      if i == 0 then
        ;(function() table.insert(patterns, " " .. pat .. ")\n" .. body_part .. term_indent .. term); return patterns end)()
      else
        ;(function() table.insert(patterns, pat .. ")\n" .. body_part .. term_indent .. term); return patterns end)()
      end
      i = i + 1
    end
    pattern_str = table.concat(patterns, "\n" .. repeat_str(" ", indent + 4))
    redirects = ""
    if (#(node.redirects) > 0) then
      redirect_parts = {}
      for _, r in ipairs(node.redirects) do
        ;(function() table.insert(redirect_parts, format_redirect(r, false, false)); return redirect_parts end)()
      end
      redirects = " " .. table.concat(redirect_parts, " ")
    end
    return "case " .. word .. " in" .. pattern_str .. "\n" .. sp .. "esac" .. redirects
  end
  if (type(node) == 'table' and getmetatable(node) == Function) then
    local node = node
    name = node.name
    inner_body = (node.body.kind == "brace-group" and node.body.body or node.body)
    body = (string.gsub(format_cmdsub_node(inner_body, indent + 4, false, false, false), '[' .. ";" .. ']+$', ''))
    return string.format("function %s () \n{ \n%s%s\n}", name, inner_sp, body)
  end
  if (type(node) == 'table' and getmetatable(node) == Subshell) then
    local node = node
    body = format_cmdsub_node(node.body, indent, in_procsub, compact_redirects, false)
    redirects = ""
    if (#(node.redirects) > 0) then
      redirect_parts = {}
      for _, r in ipairs(node.redirects) do
        ;(function() table.insert(redirect_parts, format_redirect(r, false, false)); return redirect_parts end)()
      end
      redirects = table.concat(redirect_parts, " ")
    end
    if procsub_first then
      if (redirects ~= nil and #(redirects) > 0) then
        return "(" .. body .. ") " .. redirects
      end
      return "(" .. body .. ")"
    end
    if (redirects ~= nil and #(redirects) > 0) then
      return "( " .. body .. " ) " .. redirects
    end
    return "( " .. body .. " )"
  end
  if (type(node) == 'table' and getmetatable(node) == BraceGroup) then
    local node = node
    body = format_cmdsub_node(node.body, indent, false, false, false)
    body = (string.gsub(body, '[' .. ";" .. ']+$', ''))
    terminator = ((string.sub(body, -#" &") == " &") and " }" or "; }")
    redirects = ""
    if (#(node.redirects) > 0) then
      redirect_parts = {}
      for _, r in ipairs(node.redirects) do
        ;(function() table.insert(redirect_parts, format_redirect(r, false, false)); return redirect_parts end)()
      end
      redirects = table.concat(redirect_parts, " ")
    end
    if (redirects ~= nil and #(redirects) > 0) then
      return "{ " .. body .. terminator .. " " .. redirects
    end
    return "{ " .. body .. terminator
  end
  if (type(node) == 'table' and getmetatable(node) == ArithmeticCommand) then
    local node = node
    return "((" .. node.raw_content .. "))"
  end
  if (type(node) == 'table' and getmetatable(node) == ConditionalExpr) then
    local node = node
    body = format_cond_body(node.body)
    return "[[ " .. body .. " ]]"
  end
  if (type(node) == 'table' and getmetatable(node) == Negation) then
    local node = node
    if (node.pipeline ~= nil) then
      return "! " .. format_cmdsub_node(node.pipeline, indent, false, false, false)
    end
    return "! "
  end
  if (type(node) == 'table' and getmetatable(node) == Time) then
    local node = node
    prefix = (node.posix and "time -p " or "time ")
    if (node.pipeline ~= nil) then
      return prefix .. format_cmdsub_node(node.pipeline, indent, false, false, false)
    end
    return prefix
  end
  return ""
end

function format_redirect(r, compact, heredoc_op_only)
  local after_amp, delim, is_literal_fd, op, target, was_input_close
  if (type(r) == 'table' and getmetatable(r) == HereDoc) then
    local r = r
    if r.strip_tabs then
      op = "<<-"
    else
      op = "<<"
    end
    if (r.fd ~= nil) and r.fd > 0 then
      op = tostring(r.fd) .. op
    end
    if r.quoted then
      delim = "'" .. r.delimiter .. "'"
    else
      delim = r.delimiter
    end
    if heredoc_op_only then
      return op .. delim
    end
    return op .. delim .. "\n" .. r.content .. r.delimiter .. "\n"
  end
  op = r.op
  if op == "1>" then
    op = ">"
  elseif op == "0<" then
    op = "<"
  end
  target = r.target.value
  target = r.target:expand_all_ansi_c_quotes(target)
  target = r.target:strip_locale_string_dollars(target)
  target = r.target:format_command_substitutions(target, false)
  if (string.sub(target, 1, #"&") == "&") then
    was_input_close = false
    if target == "&-" and (string.sub(op, -#"<") == "<") then
      was_input_close = true
      op = substring(op, 0, #op - 1) .. ">"
    end
    after_amp = substring(target, 1, #target)
    is_literal_fd = after_amp == "-" or #after_amp > 0 and (string.match(string.sub(after_amp, 0 + 1, 0 + 1), '^%d+$') ~= nil)
    if is_literal_fd then
      if op == ">" or op == ">&" then
        op = (was_input_close and "0>" or "1>")
      elseif op == "<" or op == "<&" then
        op = "0<"
      end
    elseif op == "1>" then
      op = ">"
    elseif op == "0<" then
      op = "<"
    end
    return op .. target
  end
  if (string.sub(op, -#"&") == "&") then
    return op .. target
  end
  if compact then
    return op .. target
  end
  return op .. " " .. target
end

function format_heredoc_body(r)
  return "\n" .. r.content .. r.delimiter .. "\n"
end

function lookahead_for_esac(value, start, case_depth)
  local c, depth, i, quote
  i = start
  depth = case_depth
  quote = new_quote_state()
  while i < #value do
    c = string.sub(value, i + 1, i + 1)
    if c == "\\" and i + 1 < #value and quote.double then
      i = i + 2
      goto continue
    end
    if c == "'" and not quote.double then
      quote.single = not quote.single
      i = i + 1
      goto continue
    end
    if c == "\"" and not quote.single then
      quote.double = not quote.double
      i = i + 1
      goto continue
    end
    if quote.single or quote.double then
      i = i + 1
      goto continue
    end
    if starts_with_at(value, i, "case") and is_word_boundary(value, i, 4) then
      depth = depth + 1
      i = i + 4
    elseif starts_with_at(value, i, "esac") and is_word_boundary(value, i, 4) then
      depth = depth - 1
      if depth == 0 then
        return true
      end
      i = i + 4
    elseif c == "(" then
      i = i + 1
    elseif c == ")" then
      if depth > 0 then
        i = i + 1
      else
        break
      end
    else
      i = i + 1
    end
    ::continue::
  end
  return false
end

function skip_backtick(value, start)
  local i
  i = start + 1
  while i < #value and string.sub(value, i + 1, i + 1) ~= "`" do
    if string.sub(value, i + 1, i + 1) == "\\" and i + 1 < #value then
      i = i + 2
    else
      i = i + 1
    end
  end
  if i < #value then
    i = i + 1
  end
  return i
end

function skip_single_quoted(s, start)
  local i
  i = start
  while i < #s and string.sub(s, i + 1, i + 1) ~= "'" do
    i = i + 1
  end
  return (i < #s and i + 1 or i)
end

function skip_double_quoted(s, start)
  local backq, c, i, n, pass_next
  i = start
  n = #s
  pass_next = false
  backq = false
  while i < n do
    c = string.sub(s, i + 1, i + 1)
    if pass_next then
      pass_next = false
      i = i + 1
      goto continue
    end
    if c == "\\" then
      pass_next = true
      i = i + 1
      goto continue
    end
    if backq then
      if c == "`" then
        backq = false
      end
      i = i + 1
      goto continue
    end
    if c == "`" then
      backq = true
      i = i + 1
      goto continue
    end
    if c == "$" and i + 1 < n then
      if string.sub(s, i + 1 + 1, i + 1 + 1) == "(" then
        i = find_cmdsub_end(s, i + 2)
        goto continue
      end
      if string.sub(s, i + 1 + 1, i + 1 + 1) == "{" then
        i = find_braced_param_end(s, i + 2)
        goto continue
      end
    end
    if c == "\"" then
      return i + 1
    end
    i = i + 1
    ::continue::
  end
  return i
end

function is_valid_arithmetic_start(value, start)
  local scan_c, scan_i, scan_paren
  scan_paren = 0
  scan_i = start + 3
  while scan_i < #value do
    scan_c = string.sub(value, scan_i + 1, scan_i + 1)
    if is_expansion_start(value, scan_i, "$(") then
      scan_i = find_cmdsub_end(value, scan_i + 2)
      goto continue
    end
    if scan_c == "(" then
      scan_paren = scan_paren + 1
    elseif scan_c == ")" then
      if scan_paren > 0 then
        scan_paren = scan_paren - 1
      elseif scan_i + 1 < #value and string.sub(value, scan_i + 1 + 1, scan_i + 1 + 1) == ")" then
        return true
      else
        return false
      end
    end
    scan_i = scan_i + 1
    ::continue::
  end
  return false
end

function find_funsub_end(value, start)
  local c, depth, i, quote
  depth = 1
  i = start
  quote = new_quote_state()
  while i < #value and depth > 0 do
    c = string.sub(value, i + 1, i + 1)
    if c == "\\" and i + 1 < #value and not quote.single then
      i = i + 2
      goto continue
    end
    if c == "'" and not quote.double then
      quote.single = not quote.single
      i = i + 1
      goto continue
    end
    if c == "\"" and not quote.single then
      quote.double = not quote.double
      i = i + 1
      goto continue
    end
    if quote.single or quote.double then
      i = i + 1
      goto continue
    end
    if c == "{" then
      depth = depth + 1
    elseif c == "}" then
      depth = depth - 1
      if depth == 0 then
        return i + 1
      end
    end
    i = i + 1
    ::continue::
  end
  return #value
end

function find_cmdsub_end(value, start)
  local arith_depth, arith_paren_depth, c, case_depth, depth, i, in_case_patterns, j
  depth = 1
  i = start
  case_depth = 0
  in_case_patterns = false
  arith_depth = 0
  arith_paren_depth = 0
  while i < #value and depth > 0 do
    c = string.sub(value, i + 1, i + 1)
    if c == "\\" and i + 1 < #value then
      i = i + 2
      goto continue
    end
    if c == "'" then
      i = skip_single_quoted(value, i + 1)
      goto continue
    end
    if c == "\"" then
      i = skip_double_quoted(value, i + 1)
      goto continue
    end
    if c == "#" and arith_depth == 0 and (i == start or string.sub(value, i - 1 + 1, i - 1 + 1) == " " or string.sub(value, i - 1 + 1, i - 1 + 1) == "\t" or string.sub(value, i - 1 + 1, i - 1 + 1) == "\n" or string.sub(value, i - 1 + 1, i - 1 + 1) == ";" or string.sub(value, i - 1 + 1, i - 1 + 1) == "|" or string.sub(value, i - 1 + 1, i - 1 + 1) == "&" or string.sub(value, i - 1 + 1, i - 1 + 1) == "(" or string.sub(value, i - 1 + 1, i - 1 + 1) == ")") then
      while i < #value and string.sub(value, i + 1, i + 1) ~= "\n" do
        i = i + 1
      end
      goto continue
    end
    if starts_with_at(value, i, "<<<") then
      i = i + 3
      while i < #value and (string.sub(value, i + 1, i + 1) == " " or string.sub(value, i + 1, i + 1) == "\t") do
        i = i + 1
      end
      if i < #value and string.sub(value, i + 1, i + 1) == "\"" then
        i = i + 1
        while i < #value and string.sub(value, i + 1, i + 1) ~= "\"" do
          if string.sub(value, i + 1, i + 1) == "\\" and i + 1 < #value then
            i = i + 2
          else
            i = i + 1
          end
        end
        if i < #value then
          i = i + 1
        end
      elseif i < #value and string.sub(value, i + 1, i + 1) == "'" then
        i = i + 1
        while i < #value and string.sub(value, i + 1, i + 1) ~= "'" do
          i = i + 1
        end
        if i < #value then
          i = i + 1
        end
      else
        while i < #value and ((not (string.find(" \t\n;|&<>()", string.sub(value, i + 1, i + 1), 1, true) ~= nil))) do
          i = i + 1
        end
      end
      goto continue
    end
    if is_expansion_start(value, i, "$((") then
      if is_valid_arithmetic_start(value, i) then
        arith_depth = arith_depth + 1
        i = i + 3
        goto continue
      end
      j = find_cmdsub_end(value, i + 2)
      i = j
      goto continue
    end
    if arith_depth > 0 and arith_paren_depth == 0 and starts_with_at(value, i, "))") then
      arith_depth = arith_depth - 1
      i = i + 2
      goto continue
    end
    if c == "`" then
      i = skip_backtick(value, i)
      goto continue
    end
    if arith_depth == 0 and starts_with_at(value, i, "<<") then
      i = skip_heredoc(value, i)
      goto continue
    end
    if starts_with_at(value, i, "case") and is_word_boundary(value, i, 4) then
      case_depth = case_depth + 1
      in_case_patterns = false
      i = i + 4
      goto continue
    end
    if case_depth > 0 and starts_with_at(value, i, "in") and is_word_boundary(value, i, 2) then
      in_case_patterns = true
      i = i + 2
      goto continue
    end
    if starts_with_at(value, i, "esac") and is_word_boundary(value, i, 4) then
      if case_depth > 0 then
        case_depth = case_depth - 1
        in_case_patterns = false
      end
      i = i + 4
      goto continue
    end
    if starts_with_at(value, i, ";;") then
      i = i + 2
      goto continue
    end
    if c == "(" then
      if not (in_case_patterns and case_depth > 0) then
        if arith_depth > 0 then
          arith_paren_depth = arith_paren_depth + 1
        else
          depth = depth + 1
        end
      end
    elseif c == ")" then
      if in_case_patterns and case_depth > 0 then
        if not lookahead_for_esac(value, i + 1, case_depth) then
          depth = depth - 1
        end
      elseif arith_depth > 0 then
        if arith_paren_depth > 0 then
          arith_paren_depth = arith_paren_depth - 1
        end
      else
        depth = depth - 1
      end
    end
    i = i + 1
    ::continue::
  end
  return i
end

function find_braced_param_end(value, start)
  local c, depth, dolbrace_state, end_, i, in_double
  depth = 1
  i = start
  in_double = false
  dolbrace_state = DOLBRACESTATE_PARAM
  while i < #value and depth > 0 do
    c = string.sub(value, i + 1, i + 1)
    if c == "\\" and i + 1 < #value then
      i = i + 2
      goto continue
    end
    if c == "'" and dolbrace_state == DOLBRACESTATE_QUOTE and not in_double then
      i = skip_single_quoted(value, i + 1)
      goto continue
    end
    if c == "\"" then
      in_double = not in_double
      i = i + 1
      goto continue
    end
    if in_double then
      i = i + 1
      goto continue
    end
    if dolbrace_state == DOLBRACESTATE_PARAM and (((string.find("%#^,", c, 1, true) ~= nil))) then
      dolbrace_state = DOLBRACESTATE_QUOTE
    elseif dolbrace_state == DOLBRACESTATE_PARAM and (((string.find(":-=?+/", c, 1, true) ~= nil))) then
      dolbrace_state = DOLBRACESTATE_WORD
    end
    if c == "[" and dolbrace_state == DOLBRACESTATE_PARAM and not in_double then
      end_ = skip_subscript(value, i, 0)
      if end_ ~= -1 then
        i = end_
        goto continue
      end
    end
    if (c == "<" or c == ">") and i + 1 < #value and string.sub(value, i + 1 + 1, i + 1 + 1) == "(" then
      i = find_cmdsub_end(value, i + 2)
      goto continue
    end
    if c == "{" then
      depth = depth + 1
    elseif c == "}" then
      depth = depth - 1
      if depth == 0 then
        return i + 1
      end
    end
    if is_expansion_start(value, i, "$(") then
      i = find_cmdsub_end(value, i + 2)
      goto continue
    end
    if is_expansion_start(value, i, "${") then
      i = find_braced_param_end(value, i + 2)
      goto continue
    end
    i = i + 1
    ::continue::
  end
  return i
end

function skip_heredoc(value, start)
  local c, delim_start, delimiter, i, in_backtick, j, line, line_end, line_start, next_line_start, paren_depth, quote, quote_char, stripped, tabs_stripped, trailing_bs
  i = start + 2
  if i < #value and string.sub(value, i + 1, i + 1) == "-" then
    i = i + 1
  end
  while i < #value and is_whitespace_no_newline(string.sub(value, i + 1, i + 1)) do
    i = i + 1
  end
  delim_start = i
  quote_char = nil
  if i < #value and (string.sub(value, i + 1, i + 1) == "\"" or string.sub(value, i + 1, i + 1) == "'") then
    quote_char = string.sub(value, i + 1, i + 1)
    i = i + 1
    delim_start = i
    while i < #value and string.sub(value, i + 1, i + 1) ~= quote_char do
      i = i + 1
    end
    delimiter = substring(value, delim_start, i)
    if i < #value then
      i = i + 1
    end
  elseif i < #value and string.sub(value, i + 1, i + 1) == "\\" then
    i = i + 1
    delim_start = i
    if i < #value then
      i = i + 1
    end
    while i < #value and not is_metachar(string.sub(value, i + 1, i + 1)) do
      i = i + 1
    end
    delimiter = substring(value, delim_start, i)
  else
    while i < #value and not is_metachar(string.sub(value, i + 1, i + 1)) do
      i = i + 1
    end
    delimiter = substring(value, delim_start, i)
  end
  paren_depth = 0
  quote = new_quote_state()
  in_backtick = false
  while i < #value and string.sub(value, i + 1, i + 1) ~= "\n" do
    c = string.sub(value, i + 1, i + 1)
    if c == "\\" and i + 1 < #value and (quote.double or in_backtick) then
      i = i + 2
      goto continue
    end
    if c == "'" and not quote.double and not in_backtick then
      quote.single = not quote.single
      i = i + 1
      goto continue
    end
    if c == "\"" and not quote.single and not in_backtick then
      quote.double = not quote.double
      i = i + 1
      goto continue
    end
    if c == "`" and not quote.single then
      in_backtick = not in_backtick
      i = i + 1
      goto continue
    end
    if quote.single or quote.double or in_backtick then
      i = i + 1
      goto continue
    end
    if c == "(" then
      paren_depth = paren_depth + 1
    elseif c == ")" then
      if paren_depth == 0 then
        break
      end
      paren_depth = paren_depth - 1
    end
    i = i + 1
    ::continue::
  end
  if i < #value and string.sub(value, i + 1, i + 1) == ")" then
    return i
  end
  if i < #value and string.sub(value, i + 1, i + 1) == "\n" then
    i = i + 1
  end
  while i < #value do
    line_start = i
    line_end = i
    while line_end < #value and string.sub(value, line_end + 1, line_end + 1) ~= "\n" do
      line_end = line_end + 1
    end
    line = substring(value, line_start, line_end)
    while line_end < #value do
      trailing_bs = 0
      j = #line - 1
      while j > -1 do
        if string.sub(line, j + 1, j + 1) == "\\" then
          trailing_bs = trailing_bs + 1
        else
          break
        end
        j = j + -1
      end
      if trailing_bs % 2 == 0 then
        break
      end
      line = string.sub(line, 1, #line - 1)
      line_end = line_end + 1
      next_line_start = line_end
      while line_end < #value and string.sub(value, line_end + 1, line_end + 1) ~= "\n" do
        line_end = line_end + 1
      end
      line = line .. substring(value, next_line_start, line_end)
    end
    if start + 2 < #value and string.sub(value, start + 2 + 1, start + 2 + 1) == "-" then
      stripped = (string.gsub(line, '^[' .. "\t" .. ']+', ''))
    else
      stripped = line
    end
    if stripped == delimiter then
      if line_end < #value then
        return line_end + 1
      else
        return line_end
      end
    end
    if (string.sub(stripped, 1, #delimiter) == delimiter) and #stripped > #delimiter then
      tabs_stripped = #line - #stripped
      return line_start + tabs_stripped + #delimiter
    end
    if line_end < #value then
      i = line_end + 1
    else
      i = line_end
    end
  end
  return i
end

function find_heredoc_content_end(source, start, delimiters)
  local item, content_start, delimiter, j, line, line_end, line_start, line_stripped, next_line_start, pos, strip_tabs, tabs_stripped, trailing_bs
  if not (#(delimiters) > 0) then
    return {start, start}
  end
  pos = start
  while pos < #source and string.sub(source, pos + 1, pos + 1) ~= "\n" do
    pos = pos + 1
  end
  if pos >= #source then
    return {start, start}
  end
  content_start = pos
  pos = pos + 1
  for _, item in ipairs(delimiters) do
    delimiter = item[1]
    strip_tabs = item[2]
    while pos < #source do
      line_start = pos
      line_end = pos
      while line_end < #source and string.sub(source, line_end + 1, line_end + 1) ~= "\n" do
        line_end = line_end + 1
      end
      line = substring(source, line_start, line_end)
      while line_end < #source do
        trailing_bs = 0
        j = #line - 1
        while j > -1 do
          if string.sub(line, j + 1, j + 1) == "\\" then
            trailing_bs = trailing_bs + 1
          else
            break
          end
          j = j + -1
        end
        if trailing_bs % 2 == 0 then
          break
        end
        line = string.sub(line, 1, #line - 1)
        line_end = line_end + 1
        next_line_start = line_end
        while line_end < #source and string.sub(source, line_end + 1, line_end + 1) ~= "\n" do
          line_end = line_end + 1
        end
        line = line .. substring(source, next_line_start, line_end)
      end
      if strip_tabs then
        line_stripped = (string.gsub(line, '^[' .. "\t" .. ']+', ''))
      else
        line_stripped = line
      end
      if line_stripped == delimiter then
        pos = (line_end < #source and line_end + 1 or line_end)
        break
      end
      if (string.sub(line_stripped, 1, #delimiter) == delimiter) and #line_stripped > #delimiter then
        tabs_stripped = #line - #line_stripped
        pos = line_start + tabs_stripped + #delimiter
        break
      end
      pos = (line_end < #source and line_end + 1 or line_end)
    end
  end
  return {content_start, pos}
end

function is_word_boundary(s, pos, word_len)
  local end_, prev
  if pos > 0 then
    prev = string.sub(s, pos - 1 + 1, pos - 1 + 1)
    if (string.match(prev, '^%w+$') ~= nil) or prev == "_" then
      return false
    end
    if ((string.find("{}!", prev, 1, true) ~= nil)) then
      return false
    end
  end
  end_ = pos + word_len
  if end_ < #s and ((string.match(string.sub(s, end_ + 1, end_ + 1), '^%w+$') ~= nil) or string.sub(s, end_ + 1, end_ + 1) == "_") then
    return false
  end
  return true
end

function is_quote(c)
  return c == "'" or c == "\""
end

function collapse_whitespace(s)
  local c, joined, prev_was_ws, result
  result = {}
  prev_was_ws = false
  for _ = 1, #s do
    local c = string.sub(s, _, _)
    if c == " " or c == "\t" then
      if not prev_was_ws then
        ;(function() table.insert(result, " "); return result end)()
      end
      prev_was_ws = true
    else
      ;(function() table.insert(result, c); return result end)()
      prev_was_ws = false
    end
  end
  joined = table.concat(result, "")
  return (string.gsub((string.gsub(joined, '^[' .. " \t" .. ']+', '')), '[' .. " \t" .. ']+$', ''))
end

function count_trailing_backslashes(s)
  local count, i
  count = 0
  i = #s - 1
  while i > -1 do
    if string.sub(s, i + 1, i + 1) == "\\" then
      count = count + 1
    else
      break
    end
    i = i + -1
  end
  return count
end

function normalize_heredoc_delimiter(delimiter)
  local depth, i, inner, inner_str, result
  result = {}
  i = 0
  while i < #delimiter do
    if i + 1 < #delimiter and string.sub(delimiter, (i) + 1, i + 2) == "$(" then
      ;(function() table.insert(result, "$("); return result end)()
      i = i + 2
      depth = 1
      inner = {}
      while i < #delimiter and depth > 0 do
        if string.sub(delimiter, i + 1, i + 1) == "(" then
          depth = depth + 1
          ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
        elseif string.sub(delimiter, i + 1, i + 1) == ")" then
          depth = depth - 1
          if depth == 0 then
            inner_str = table.concat(inner, "")
            inner_str = collapse_whitespace(inner_str)
            ;(function() table.insert(result, inner_str); return result end)()
            ;(function() table.insert(result, ")"); return result end)()
          else
            ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
          end
        else
          ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
        end
        i = i + 1
      end
    elseif i + 1 < #delimiter and string.sub(delimiter, (i) + 1, i + 2) == "${" then
      ;(function() table.insert(result, "${"); return result end)()
      i = i + 2
      depth = 1
      inner = {}
      while i < #delimiter and depth > 0 do
        if string.sub(delimiter, i + 1, i + 1) == "{" then
          depth = depth + 1
          ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
        elseif string.sub(delimiter, i + 1, i + 1) == "}" then
          depth = depth - 1
          if depth == 0 then
            inner_str = table.concat(inner, "")
            inner_str = collapse_whitespace(inner_str)
            ;(function() table.insert(result, inner_str); return result end)()
            ;(function() table.insert(result, "}"); return result end)()
          else
            ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
          end
        else
          ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
        end
        i = i + 1
      end
    elseif i + 1 < #delimiter and (((string.find("<>", string.sub(delimiter, i + 1, i + 1), 1, true) ~= nil))) and string.sub(delimiter, i + 1 + 1, i + 1 + 1) == "(" then
      ;(function() table.insert(result, string.sub(delimiter, i + 1, i + 1)); return result end)()
      ;(function() table.insert(result, "("); return result end)()
      i = i + 2
      depth = 1
      inner = {}
      while i < #delimiter and depth > 0 do
        if string.sub(delimiter, i + 1, i + 1) == "(" then
          depth = depth + 1
          ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
        elseif string.sub(delimiter, i + 1, i + 1) == ")" then
          depth = depth - 1
          if depth == 0 then
            inner_str = table.concat(inner, "")
            inner_str = collapse_whitespace(inner_str)
            ;(function() table.insert(result, inner_str); return result end)()
            ;(function() table.insert(result, ")"); return result end)()
          else
            ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
          end
        else
          ;(function() table.insert(inner, string.sub(delimiter, i + 1, i + 1)); return inner end)()
        end
        i = i + 1
      end
    else
      ;(function() table.insert(result, string.sub(delimiter, i + 1, i + 1)); return result end)()
      i = i + 1
    end
  end
  return table.concat(result, "")
end

function is_metachar(c)
  return c == " " or c == "\t" or c == "\n" or c == "|" or c == "&" or c == ";" or c == "(" or c == ")" or c == "<" or c == ">"
end

function is_funsub_char(c)
  return c == " " or c == "\t" or c == "\n" or c == "|"
end

function is_extglob_prefix(c)
  return c == "@" or c == "?" or c == "*" or c == "+" or c == "!"
end

function is_redirect_char(c)
  return c == "<" or c == ">"
end

function is_special_param(c)
  return c == "?" or c == "$" or c == "!" or c == "#" or c == "@" or c == "*" or c == "-" or c == "&"
end

function is_special_param_unbraced(c)
  return c == "?" or c == "$" or c == "!" or c == "#" or c == "@" or c == "*" or c == "-"
end

function is_digit(c)
  return c >= "0" and c <= "9"
end

function is_semicolon_or_newline(c)
  return c == ";" or c == "\n"
end

function is_word_end_context(c)
  return c == " " or c == "\t" or c == "\n" or c == ";" or c == "|" or c == "&" or c == "<" or c == ">" or c == "(" or c == ")"
end

function skip_matched_pair(s, start, open, close, flags)
  local backq, c, depth, i, literal, n, pass_next
  n = #s
  if (flags & SMP_PAST_OPEN ~= 0) then
    i = start
  else
    if start >= n or string.sub(s, start + 1, start + 1) ~= open then
      return -1
    end
    i = start + 1
  end
  depth = 1
  pass_next = false
  backq = false
  while i < n and depth > 0 do
    c = string.sub(s, i + 1, i + 1)
    if pass_next then
      pass_next = false
      i = i + 1
      goto continue
    end
    literal = flags & SMP_LITERAL
    if (literal == 0) and c == "\\" then
      pass_next = true
      i = i + 1
      goto continue
    end
    if backq then
      if c == "`" then
        backq = false
      end
      i = i + 1
      goto continue
    end
    if (literal == 0) and c == "`" then
      backq = true
      i = i + 1
      goto continue
    end
    if (literal == 0) and c == "'" then
      i = skip_single_quoted(s, i + 1)
      goto continue
    end
    if (literal == 0) and c == "\"" then
      i = skip_double_quoted(s, i + 1)
      goto continue
    end
    if (literal == 0) and is_expansion_start(s, i, "$(") then
      i = find_cmdsub_end(s, i + 2)
      goto continue
    end
    if (literal == 0) and is_expansion_start(s, i, "${") then
      i = find_braced_param_end(s, i + 2)
      goto continue
    end
    if (literal == 0) and c == open then
      depth = depth + 1
    elseif c == close then
      depth = depth - 1
    end
    i = i + 1
    ::continue::
  end
  return (depth == 0 and i or -1)
end

function skip_subscript(s, start, flags)
  return skip_matched_pair(s, start, "[", "]", flags)
end

function assignment(s, flags)
  local c, end_, i, sub_flags
  if not (s ~= nil and #(s) > 0) then
    return -1
  end
  if not ((string.match(string.sub(s, 0 + 1, 0 + 1), '^%a+$') ~= nil) or string.sub(s, 0 + 1, 0 + 1) == "_") then
    return -1
  end
  i = 1
  while i < #s do
    c = string.sub(s, i + 1, i + 1)
    if c == "=" then
      return i
    end
    if c == "[" then
      sub_flags = ((flags & 2 ~= 0) and SMP_LITERAL or 0)
      end_ = skip_subscript(s, i, sub_flags)
      if end_ == -1 then
        return -1
      end
      i = end_
      if i < #s and string.sub(s, i + 1, i + 1) == "+" then
        i = i + 1
      end
      if i < #s and string.sub(s, i + 1, i + 1) == "=" then
        return i
      end
      return -1
    end
    if c == "+" then
      if i + 1 < #s and string.sub(s, i + 1 + 1, i + 1 + 1) == "=" then
        return i + 1
      end
      return -1
    end
    if not ((string.match(c, '^%w+$') ~= nil) or c == "_") then
      return -1
    end
    i = i + 1
  end
  return -1
end

function is_array_assignment_prefix(chars)
  local end_, i, s
  if not (#(chars) > 0) then
    return false
  end
  if not ((string.match(chars[0 + 1], '^%a+$') ~= nil) or chars[0 + 1] == "_") then
    return false
  end
  s = table.concat(chars, "")
  i = 1
  while i < #s and ((string.match(string.sub(s, i + 1, i + 1), '^%w+$') ~= nil) or string.sub(s, i + 1, i + 1) == "_") do
    i = i + 1
  end
  while i < #s do
    if string.sub(s, i + 1, i + 1) ~= "[" then
      return false
    end
    end_ = skip_subscript(s, i, SMP_LITERAL)
    if end_ == -1 then
      return false
    end
    i = end_
  end
  return true
end

function is_special_param_or_digit(c)
  return is_special_param(c) or is_digit(c)
end

function is_param_expansion_op(c)
  return c == ":" or c == "-" or c == "=" or c == "+" or c == "?" or c == "#" or c == "%" or c == "/" or c == "^" or c == "," or c == "@" or c == "*" or c == "["
end

function is_simple_param_op(c)
  return c == "-" or c == "=" or c == "?" or c == "+"
end

function is_escape_char_in_backtick(c)
  return c == "$" or c == "`" or c == "\\"
end

function is_negation_boundary(c)
  return is_whitespace(c) or c == ";" or c == "|" or c == ")" or c == "&" or c == ">" or c == "<"
end

function is_backslash_escaped(value, idx)
  local bs_count, j
  bs_count = 0
  j = idx - 1
  while j >= 0 and string.sub(value, j + 1, j + 1) == "\\" do
    bs_count = bs_count + 1
    j = j - 1
  end
  return bs_count % 2 == 1
end

function is_dollar_dollar_paren(value, idx)
  local dollar_count, j
  dollar_count = 0
  j = idx - 1
  while j >= 0 and string.sub(value, j + 1, j + 1) == "$" do
    dollar_count = dollar_count + 1
    j = j - 1
  end
  return dollar_count % 2 == 1
end

function is_paren(c)
  return c == "(" or c == ")"
end

function is_caret_or_bang(c)
  return c == "!" or c == "^"
end

function is_at_or_star(c)
  return c == "@" or c == "*"
end

function is_digit_or_dash(c)
  return is_digit(c) or c == "-"
end

function is_newline_or_right_paren(c)
  return c == "\n" or c == ")"
end

function is_semicolon_newline_brace(c)
  return c == ";" or c == "\n" or c == "{"
end

function looks_like_assignment(s)
  return assignment(s, 0) ~= -1
end

function is_valid_identifier(name)
  local c
  if not (name ~= nil and #(name) > 0) then
    return false
  end
  if not ((string.match(string.sub(name, 0 + 1, 0 + 1), '^%a+$') ~= nil) or string.sub(name, 0 + 1, 0 + 1) == "_") then
    return false
  end
  for _ = 1, #string.sub(name, (1) + 1, #name) do
    local c = string.sub(string.sub(name, (1) + 1, #name), _, _)
    if not ((string.match(c, '^%w+$') ~= nil) or c == "_") then
      return false
    end
  end
  return true
end

function parse(source, extglob)
  local parser
  parser = new_parser(source, false, extglob)
  return parser:parse()
end

function new_parse_error(message, pos, line)
  local self
  self = ParseError:new(nil, nil, nil)
  self.message = message
  self.pos = pos
  self.line = line
  return self
end

function new_matched_pair_error(message, pos, line)
  return MatchedPairError:new()
end

function new_quote_state()
  local self
  self = QuoteState:new(nil, nil, nil)
  self.single = false
  self.double = false
  self.stack = {}
  return self
end

function new_parse_context(kind)
  local self
  self = ParseContext:new(nil, nil, nil, nil, nil, nil, nil, nil)
  self.kind = kind
  self.paren_depth = 0
  self.brace_depth = 0
  self.bracket_depth = 0
  self.case_depth = 0
  self.arith_depth = 0
  self.arith_paren_depth = 0
  self.quote = new_quote_state()
  return self
end

function new_context_stack()
  local self
  self = ContextStack:new(nil)
  self.stack = {new_parse_context(0)}
  return self
end

function new_lexer(source, extglob)
  local self
  self = Lexer:new(nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil)
  self.source = source
  self.pos = 0
  self.length = #source
  self.quote = new_quote_state()
  self.token_cache = nil
  self.parser_state = PARSERSTATEFLAGS_NONE
  self.dolbrace_state = DOLBRACESTATE_NONE
  self.pending_heredocs = {}
  self.extglob = extglob
  self.parser = nil
  self.eof_token = ""
  self.last_read_token = nil
  self.word_context = WORD_CTX_NORMAL
  self.at_command_start = false
  self.in_array_literal = false
  self.in_assign_builtin = false
  self.post_read_pos = 0
  self.cached_word_context = WORD_CTX_NORMAL
  self.cached_at_command_start = false
  self.cached_in_array_literal = false
  self.cached_in_assign_builtin = false
  return self
end

function new_parser(source, in_process_sub, extglob)
  local self
  self = Parser:new(nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil)
  self.source = source
  self.pos = 0
  self.length = #source
  self.pending_heredocs = {}
  self.cmdsub_heredoc_end = -1
  self.saw_newline_in_single_quote = false
  self.in_process_sub = in_process_sub
  self.extglob = extglob
  self.ctx = new_context_stack()
  self.lexer = new_lexer(source, extglob)
  self.lexer.parser = self
  self.token_history = {nil, nil, nil, nil}
  self.parser_state = PARSERSTATEFLAGS_NONE
  self.dolbrace_state = DOLBRACESTATE_NONE
  self.eof_token = ""
  self.word_context = WORD_CTX_NORMAL
  self.at_command_start = false
  self.in_array_literal = false
  self.in_assign_builtin = false
  self.arith_src = ""
  self.arith_pos = 0
  self.arith_len = 0
  return self
end
