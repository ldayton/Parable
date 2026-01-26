"""Tests for Zig backend."""

from src.backend.zig import ZigBackend
from tests.fixture import make_fixture

EXPECTED = """\
const std = @import("std");
const mem = std.mem;
const Allocator = std.mem.Allocator;
const ArrayList = std.ArrayList;

var gpa = std.heap.GeneralPurposeAllocator(.{}){};
const allocator = gpa.allocator();

pub const EOF: i64 = -1;

pub const Token = struct {
    kind: []const u8,
    text: []const u8,
    pos: i64,

    pub fn is_word(self: *Token) bool {
        return mem.eql(u8, self.kind, "word");
    }
};

pub const Lexer = struct {
    source: []const u8,
    pos: i64,
    current: ?Token,

    pub fn peek(self: *Lexer) i64 {
        if ((self.pos >= self.source.len)) {
            return EOF;
        }
        return self.source[self.pos];
    }

    pub fn advance(self: *Lexer) void {
        self.pos += 1;
    }

    pub fn scan_word(self: *Lexer) struct { @"0": Token, @"1": bool } {
        var start: i64 = self.pos;
        while (((self.peek() != EOF) and !is_space(self.peek()))) {
            _ = self.advance();
        }
        if ((self.pos == start)) {
            return .{ Token{}, false };
        }
        var text: []const u8 = self.source[start..self.pos];
        return .{ Token{ .kind = "word", .text = text, .pos = start }, true };
    }
};

pub fn is_space(ch: i64) bool {
    return ((ch == 32) or (ch == 10));
}

pub fn tokenize(source: []const u8) []const Token {
    var lx: Lexer = Lexer{ .source = source, .pos = 0, .current = null };
    var tokens: []const Token = &[_]Token{};
    while ((lx.peek() != EOF)) {
        var ch: i64 = lx.peek();
        if (is_space(ch)) {
            _ = lx.advance();
            continue;
        }
        var result: struct { @"0": Token, @"1": bool } = lx.scan_word();
        var tok: Token = result.@"0";
        var ok: bool = result.@"1";
        if (!ok) {
            @panic("unexpected character");
        }
        _ = tokens.append(tok) catch unreachable;
    }
    return tokens;
}

pub fn count_words(tokens: []const Token) i64 {
    var count: i64 = 0;
    for (tokens) |tok| {
        if (mem.eql(u8, tok.kind, "word")) {
            count += 1;
        }
    }
    return count;
}

pub fn format_token(tok: Token) []const u8 {
    return tok.kind ++ ":" ++ tok.text;
}

pub fn find_token(tokens: []const Token, kind: []const u8) ?Token {
    for (tokens) |tok| {
        if (mem.eql(u8, tok.kind, kind)) {
            return tok;
        }
    }
    return null;
}

pub fn example_nil_check(tokens: []const Token) []const u8 {
    var tok: ?Token = find_token(tokens, "word");
    if (tok == null) {
        return "";
    }
    return tok.text;
}

pub fn sum_positions(tokens: []const Token) i64 {
    var sum: i64 = 0;
    var i: i64 = 0;
    while ((i < tokens.len)) {
        sum = (sum + tokens[i].pos);
        i = (i + 1);
    }
    return sum;
}

pub fn first_word_pos(tokens: []const Token) i64 {
    var pos: i64 = -1;
    for (tokens) |tok| {
        if (mem.eql(u8, tok.kind, "word")) {
            pos = tok.pos;
            break;
        }
    }
    return pos;
}

pub fn max_int(a: i64, b: i64) i64 {
    return if ((a > b)) a else b;
}

pub fn default_kinds() std.StringHashMap(i64) {
    return std.StringHashMap(i64).init(allocator);
}

pub fn scoped_work(x: i64) i64 {
    var result: i64 = 0;
    {
        var temp: i64 = (x * 2);
        result = (temp + 1);
    }
    return result;
}

pub fn kind_priority(kind: []const u8) i64 {
    if (mem.eql(u8, kind, "word")) {
        return 1;
    } else if (mem.eql(u8, kind, "num") or mem.eql(u8, kind, "float")) {
        return 2;
    } else if (mem.eql(u8, kind, "op")) {
        return 3;
    } else {
        return 0;
    }
}

pub fn safe_tokenize(source: []const u8) []const Token {
    var tokens: []const Token = &[_]Token{};
    // try-catch block
    {
        tokens = tokenize(source);
    }
    return tokens;
}

pub fn pi() f64 {
    return 3.14159;
}

pub fn describe_token(tok: Token) []const u8 {
    return std.fmt.allocPrint(allocator, "Token({}, {}, {})", .{ tok.kind, tok.text, tok.pos }) catch unreachable;
}

pub fn set_first_kind(tokens: []const Token, kind: []const u8) void {
    if ((tokens.len > 0)) {
        tokens[0] = Token{ .kind = kind, .text = "", .pos = 0 };
    }
}

pub fn make_int_slice(n: i64) []const i64 {
    return allocator.alloc(i64, @intCast(n)) catch unreachable;
}

pub fn int_to_float(n: i64) f64 {
    return @floatCast(n);
}

pub fn known_kinds() std.AutoHashMap([]const u8, void) {
    return std.AutoHashMap([]const u8, void).init(allocator);
}

pub fn call_static() Token {
    return Token.empty();
}

pub fn new_kind_map() std.StringHashMap(i64) {
    return std.StringHashMap(i64).init(allocator);
}

pub fn get_array_first(arr: [10]i64) i64 {
    return arr[0];
}

pub fn maybe_get(tokens: []const Token, idx: i64) ?Token {
    if ((idx >= tokens.len)) {
        return null;
    }
    return tokens[idx];
}

pub fn set_via_ptr(ptr: *i64, val: i64) void {
    ptr.* = val;
}

pub fn identity_str(s: []const u8) []const u8 {
    return s;
}

pub fn accept_union(obj: union(enum) { v0: Token, v1: Lexer }) bool {
    return true;
}
"""


def test_fixture_emits_correct_zig() -> None:
    module = make_fixture()
    backend = ZigBackend()
    output = backend.emit(module)
    assert output == EXPECTED
