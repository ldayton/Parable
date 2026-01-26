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

    pub fn is_word(self: *const Token) bool {
        return mem.eql(u8, self.kind, "word");
    }
};

pub const Lexer = struct {
    source: []const u8,
    pos: i64,
    current: ?Token,

    pub fn peek(self: *Lexer) i64 {
        if (@as(usize, @intCast(self.pos)) >= self.source.len) {
            return EOF;
        }
        return self.source[@as(usize, @intCast(self.pos))];
    }

    pub fn advance(self: *Lexer) void {
        self.pos += 1;
    }

    pub fn scan_word(self: *Lexer) struct { f0: Token, f1: bool } {
        const start = self.pos;
        while (self.peek() != EOF and !is_space(self.peek())) {
            self.advance();
        }
        if (self.pos == start) {
            return .{ .f0 = Token{}, .f1 = false };
        }
        const text: []const u8 = self.source[@as(usize, @intCast(start))..@as(usize, @intCast(self.pos))];
        return .{ .f0 = Token{ .kind = "word", .text = text, .pos = start }, .f1 = true };
    }
};

pub fn is_space(ch: i64) bool {
    return ch == ' ' or ch == '\n';
}

pub fn tokenize(source: []const u8) ArrayList(Token) {
    var lx = Lexer{ .source = source, .pos = 0, .current = null };
    var tokens: ArrayList(Token) = ArrayList(Token).init(allocator);
    while (lx.peek() != EOF) {
        const ch = lx.peek();
        if (is_space(ch)) {
            lx.advance();
            continue;
        }
        const result = lx.scan_word();
        const tok = result.f0;
        const ok = result.f1;
        if (!ok) {
            @panic("unexpected character");
        }
        tokens.append(tok) catch unreachable;
    }
    return tokens;
}

pub fn count_words(tokens: ArrayList(Token)) i64 {
    var count: i64 = 0;
    for (tokens.items) |tok| {
        if (mem.eql(u8, tok.kind, "word")) {
            count += 1;
        }
    }
    return count;
}

pub fn format_token(tok: Token) []const u8 {
    return tok.kind ++ ":" ++ tok.text;
}

pub fn find_token(tokens: ArrayList(Token), kind: []const u8) ?Token {
    for (tokens.items) |tok| {
        if (mem.eql(u8, tok.kind, kind)) {
            return tok;
        }
    }
    return null;
}

pub fn example_nil_check(tokens: ArrayList(Token)) []const u8 {
    const tok = find_token(tokens, "word");
    if (tok == null) {
        return "";
    }
    return tok.?.text;
}

pub fn sum_positions(tokens: ArrayList(Token)) i64 {
    var sum: i64 = 0;
    var i: i64 = 0;
    while (@as(usize, @intCast(i)) < tokens.items.len) {
        sum += tokens.items[@as(usize, @intCast(i))].pos;
        i += 1;
    }
    return sum;
}

pub fn first_word_pos(tokens: ArrayList(Token)) i64 {
    var pos: i64 = -1;
    for (tokens.items) |tok| {
        if (mem.eql(u8, tok.kind, "word")) {
            pos = tok.pos;
            break;
        }
    }
    return pos;
}

pub fn max_int(a: i64, b: i64) i64 {
    return if (a > b) a else b;
}

pub fn default_kinds() std.StringHashMap(i64) {
    return blk: { var m = std.StringHashMap(i64).init(allocator); m.put("word", 1) catch unreachable; m.put("num", 2) catch unreachable; m.put("op", 3) catch unreachable; break :blk m; };
}

pub fn scoped_work(x: i64) i64 {
    var result: i64 = 0;
    {
        const temp: i64 = x * 2;
        result = temp + 1;
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

pub fn safe_tokenize(source: []const u8) ArrayList(Token) {
    var tokens: ArrayList(Token) = ArrayList(Token).init(allocator);
    // Note: error handling simplified - Zig uses error unions
    tokens = tokenize(source);
    return tokens;
}

pub fn pi() f64 {
    return 3.14159;
}

pub fn describe_token(tok: Token) []const u8 {
    return std.fmt.allocPrint(allocator, "Token({}, {}, {})", .{ tok.kind, tok.text, tok.pos }) catch unreachable;
}

pub fn set_first_kind(tokens: ArrayList(Token), kind: []const u8) void {
    if (tokens.items.len > 0) {
        tokens.items[0] = Token{ .kind = kind, .text = "", .pos = 0 };
    }
}

pub fn make_int_slice(n: i64) ArrayList(i64) {
    return ArrayList(i64).initCapacity(allocator, @as(usize, @intCast(n))) catch unreachable;
}

pub fn int_to_float(n: i64) f64 {
    return @as(f64, @floatFromInt(n));
}

pub fn known_kinds() std.StringHashMap(void) {
    return blk: { var s = std.StringHashMap(void).init(allocator); s.put("word", {}) catch unreachable; s.put("num", {}) catch unreachable; s.put("op", {}) catch unreachable; break :blk s; };
}

pub fn new_kind_map() std.StringHashMap(i64) {
    return std.StringHashMap(i64).init(allocator);
}

pub fn get_array_first(arr: [10]i64) i64 {
    return arr[0];
}

pub fn maybe_get(tokens: ArrayList(Token), idx: i64) ?Token {
    if (@as(usize, @intCast(idx)) >= tokens.items.len) {
        return null;
    }
    return tokens.items[@as(usize, @intCast(idx))];
}

pub fn set_via_ptr(ptr: *i64, val: i64) void {
    ptr.* = val;
}

pub fn identity_str(s: []const u8) []const u8 {
    return s;
}

pub fn accept_union(_: union(enum) { v0: Token, v1: Lexer }) bool {
    return true;
}

