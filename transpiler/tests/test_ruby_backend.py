"""Tests for Ruby backend."""

from src.backend.ruby import RubyBackend
from tests.fixture import make_fixture

EXPECTED = """\
module Fixture
  EOF = -1

  module Scanner
    def peek
      raise NotImplementedError
    end
    def advance
      raise NotImplementedError
    end
  end

  class Token
    attr_accessor :kind, :text, :pos

    def initialize(kind, text, pos)
      @kind = kind
      @text = text
      @pos = pos
    end

    def is_word
      @kind == "word"
    end
  end

  class Lexer
    attr_accessor :source, :pos, :current

    def initialize(source, pos, current)
      @source = source
      @pos = pos
      @current = current
    end

    def peek
      if @pos >= @source.length
        return EOF
      end
      @source[@pos]
    end

    def advance
      @pos += 1
    end

    def scan_word
      start = @pos
      while self.peek != EOF && !is_space(self.peek)
        self.advance
      end
      if @pos == start
        return [Token.new, false]
      end
      text = @source[start...@pos]
      [Token.new("word", text, start), true]
    end
  end

  def self.is_space(ch)
    ch == 32 || ch == 10
  end

  def self.tokenize(source)
    lx = Lexer.new(source, 0, nil)
    tokens = []
    while lx.peek != EOF
      ch = lx.peek
      if is_space(ch)
        lx.advance
        next
      end
      result = lx.scan_word
      tok = result[0]
      ok = result[1]
      if !ok
        raise "unexpected character"
      end
      tokens.push(tok)
    end
    tokens
  end

  def self.count_words(tokens)
    count = 0
    tokens.each do |tok|
      if tok.kind == "word"
        count += 1
      end
    end
    count
  end

  def self.format_token(tok)
    tok.kind + ":" + tok.text
  end

  def self.find_token(tokens, kind)
    tokens.each do |tok|
      if tok.kind == kind
        return tok
      end
    end
    nil
  end

  def self.example_nil_check(tokens)
    tok = find_token(tokens, "word")
    if tok.nil?
      return ""
    end
    tok.text
  end

  def self.sum_positions(tokens)
    sum = 0
    i = 0
    while i < tokens.length
      sum = sum + tokens[i].pos
      i = i + 1
    end
    sum
  end

  def self.first_word_pos(tokens)
    pos = -1
    tokens.each do |tok|
      if tok.kind == "word"
        pos = tok.pos
        break
      end
    end
    pos
  end

  def self.max_int(a, b)
    a > b ? a : b
  end

  def self.default_kinds
    {"word" => 1, "num" => 2, "op" => 3}
  end

  def self.scoped_work(x)
    result = 0
    temp = x * 2
    result = temp + 1
    result
  end

  def self.kind_priority(kind)
    case kind
    when "word"
      1
    when "num", "float"
      2
    when "op"
      3
    else
      0
    end
  end

  def self.safe_tokenize(source)
    tokens = []
    begin
      tokens = tokenize(source)
    rescue => e
      tokens = []
    end
    tokens
  end

  def self.pi
    3.14159
  end

  def self.describe_token(tok)
    "Token(#{tok.kind}, #{tok.text}, #{tok.pos})"
  end

  def self.set_first_kind(tokens, kind)
    if tokens.length > 0
      tokens[0] = Token.new(kind, "", 0)
    end
  end

  def self.make_int_slice(n)
    Array.new(n)
  end

  def self.int_to_float(n)
    n.to_f
  end

  def self.known_kinds
    Set.new(["word", "num", "op"])
  end

  def self.call_static
    Token.empty
  end

  def self.new_kind_map
    {}
  end

  def self.get_array_first(arr)
    arr[0]
  end

  def self.maybe_get(tokens, idx)
    if idx >= tokens.length
      return nil
    end
    tokens[idx]
  end

  def self.set_via_ptr(ptr, val)
    ptr = val
  end

  def self.identity_str(s)
    s
  end

  def self.accept_union(obj)
    true
  end
end"""


def test_fixture_emits_correct_ruby() -> None:
    module = make_fixture()
    backend = RubyBackend()
    output = backend.emit(module)
    assert output == EXPECTED
