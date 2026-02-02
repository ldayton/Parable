const std = @import("std");
const parable = @import("parable");
const fs = std.fs;
const mem = std.mem;
const Allocator = std.mem.Allocator;

const TestCase = struct {
    name: []const u8,
    input: []const u8,
    expected: []const u8,
    line_num: usize,
};

const TestResult = struct {
    rel_path: []const u8,
    line_num: usize,
    name: []const u8,
    input: []const u8,
    expected: []const u8,
    actual: []const u8,
    err: []const u8,
};

fn findTestFiles(allocator: Allocator, directory: []const u8) !std.ArrayList([]const u8) {
    var files = std.ArrayList([]const u8).init(allocator);
    var dir = try fs.cwd().openDir(directory, .{ .iterate = true });
    defer dir.close();
    var walker = try dir.walk(allocator);
    defer walker.deinit();
    while (try walker.next()) |entry| {
        if (entry.kind == .file and mem.endsWith(u8, entry.path, ".tests")) {
            const full_path = try std.fmt.allocPrint(allocator, "{s}/{s}", .{ directory, entry.path });
            try files.append(full_path);
        }
    }
    mem.sort([]const u8, files.items, {}, struct {
        fn lessThan(_: void, a: []const u8, b: []const u8) bool {
            return mem.lessThan(u8, a, b);
        }
    }.lessThan);
    return files;
}

fn parseTestFile(allocator: Allocator, filepath: []const u8) !std.ArrayList(TestCase) {
    const content = fs.cwd().readFileAlloc(allocator, filepath, 10 * 1024 * 1024) catch return std.ArrayList(TestCase).init(allocator);
    var tests = std.ArrayList(TestCase).init(allocator);
    var lines = mem.splitScalar(u8, content, '\n');
    var line_num: usize = 0;
    while (lines.next()) |line| {
        line_num += 1;
        if (line.len > 0 and line[0] == '#') continue;
        if (mem.trim(u8, line, " \t\r").len == 0) continue;
        if (mem.startsWith(u8, line, "=== ")) {
            const name = mem.trim(u8, line[4..], " \t\r");
            const start_line = line_num + 1;
            var input_lines = std.ArrayList([]const u8).init(allocator);
            while (lines.next()) |l| {
                line_num += 1;
                if (mem.eql(u8, l, "---")) break;
                try input_lines.append(l);
            }
            var expected_lines = std.ArrayList([]const u8).init(allocator);
            while (lines.next()) |l| {
                line_num += 1;
                if (mem.eql(u8, l, "---") or mem.startsWith(u8, l, "=== ")) {
                    if (mem.startsWith(u8, l, "=== ")) line_num -= 1;
                    break;
                }
                try expected_lines.append(l);
            }
            while (expected_lines.items.len > 0 and mem.trim(u8, expected_lines.items[expected_lines.items.len - 1], " \t\r").len == 0) {
                _ = expected_lines.pop();
            }
            const input = try mem.join(allocator, "\n", input_lines.items);
            const expected = try mem.join(allocator, "\n", expected_lines.items);
            try tests.append(.{ .name = name, .input = input, .expected = expected, .line_num = start_line });
        }
    }
    return tests;
}

fn normalize(allocator: Allocator, s: []const u8) ![]const u8 {
    var result = std.ArrayList(u8).init(allocator);
    var in_space = true;
    for (s) |c| {
        if (std.ascii.isWhitespace(c)) {
            if (!in_space) {
                try result.append(' ');
                in_space = true;
            }
        } else {
            try result.append(c);
            in_space = false;
        }
    }
    const items = result.items;
    var start: usize = 0;
    var end: usize = items.len;
    while (start < end and items[start] == ' ') start += 1;
    while (end > start and items[end - 1] == ' ') end -= 1;
    return items[start..end];
}

const TestOutput = struct { passed: bool, actual: []const u8, err_msg: []const u8 };

fn runTestInner(allocator: Allocator, input: []const u8, extglob: bool, test_expected: []const u8) TestOutput {
    const nodes = parable.parse(allocator, input, extglob) catch |e| {
        const expected_norm = normalize(allocator, test_expected) catch return .{ .passed = false, .actual = "<error>", .err_msg = "normalize failed" };
        if (mem.eql(u8, expected_norm, "<error>")) {
            return .{ .passed = true, .actual = "<error>", .err_msg = "" };
        }
        return .{ .passed = false, .actual = "<parse error>", .err_msg = @errorName(e) };
    };
    var parts = std.ArrayList([]const u8).init(allocator);
    for (nodes) |n| {
        parts.append(n.toSexp(allocator) catch "<sexp failed>") catch {};
    }
    const actual = mem.join(allocator, " ", parts.items) catch return .{ .passed = false, .actual = "<join failed>", .err_msg = "" };
    const expected_norm = normalize(allocator, test_expected) catch return .{ .passed = false, .actual = actual, .err_msg = "normalize failed" };
    if (mem.eql(u8, expected_norm, "<error>")) {
        return .{ .passed = false, .actual = actual, .err_msg = "Expected parse error but got successful parse" };
    }
    const actual_norm = normalize(allocator, actual) catch return .{ .passed = false, .actual = actual, .err_msg = "normalize failed" };
    if (mem.eql(u8, expected_norm, actual_norm)) {
        return .{ .passed = true, .actual = actual, .err_msg = "" };
    }
    return .{ .passed = false, .actual = actual, .err_msg = "" };
}

const ThreadContext = struct {
    allocator: Allocator,
    input: []const u8,
    extglob: bool,
    test_expected: []const u8,
    result: ?TestOutput = null,
    done: std.atomic.Value(bool) = std.atomic.Value(bool).init(false),
};

fn testThread(ctx: *ThreadContext) void {
    ctx.result = runTestInner(ctx.allocator, ctx.input, ctx.extglob, ctx.test_expected);
    ctx.done.store(true, .release);
}

fn runTest(allocator: Allocator, test_input: []const u8, test_expected: []const u8) !TestOutput {
    var extglob = false;
    var input = test_input;
    if (mem.startsWith(u8, input, "# @extglob\n")) {
        extglob = true;
        input = input["# @extglob\n".len..];
    }
    var ctx = ThreadContext{
        .allocator = allocator,
        .input = input,
        .extglob = extglob,
        .test_expected = test_expected,
    };
    const thread = std.Thread.spawn(.{}, testThread, .{&ctx}) catch {
        return runTestInner(allocator, input, extglob, test_expected);
    };
    const deadline = std.time.milliTimestamp() + 10000;
    while (std.time.milliTimestamp() < deadline) {
        if (ctx.done.load(.acquire)) {
            thread.join();
            return ctx.result orelse .{ .passed = false, .actual = "<error>", .err_msg = "No result" };
        }
        std.time.sleep(10 * std.time.ns_per_ms);
    }
    thread.detach();
    return .{ .passed = false, .actual = "<timeout>", .err_msg = "Test timed out after 10 seconds" };
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();
    const args = try std.process.argsAlloc(allocator);
    defer std.process.argsFree(allocator, args);
    var verbose = false;
    var filter_pattern: []const u8 = "";
    var max_failures: usize = 20;
    var test_dir: ?[]const u8 = null;
    var i: usize = 1;
    while (i < args.len) : (i += 1) {
        const arg = args[i];
        if (mem.eql(u8, arg, "-v") or mem.eql(u8, arg, "--verbose")) {
            verbose = true;
        } else if (mem.eql(u8, arg, "-f") or mem.eql(u8, arg, "--filter")) {
            if (i + 1 < args.len) {
                i += 1;
                filter_pattern = args[i];
            }
        } else if (mem.eql(u8, arg, "--max-failures")) {
            if (i + 1 < args.len) {
                i += 1;
                max_failures = try std.fmt.parseInt(usize, args[i], 10);
            }
        } else if (mem.eql(u8, arg, "-h") or mem.eql(u8, arg, "--help")) {
            const stdout = std.io.getStdOut().writer();
            try stdout.print("Usage: run_tests [options] [test_dir]\n", .{});
            try stdout.print("Options:\n", .{});
            try stdout.print("  -v, --verbose       Show PASS/FAIL for each test\n", .{});
            try stdout.print("  -f, --filter PAT    Only run tests matching PAT\n", .{});
            try stdout.print("  --max-failures N    Show at most N failures (0=unlimited)\n", .{});
            try stdout.print("  -h, --help          Show this help message\n", .{});
            return;
        } else if (arg[0] != '-') {
            test_dir = arg;
        }
    }
    const dir = test_dir orelse blk: {
        if (fs.cwd().statFile("tests")) |_| break :blk "tests" else |_| break :blk "../tests";
    };
    fs.cwd().statFile(dir) catch {
        const stderr = std.io.getStdErr().writer();
        try stderr.print("Could not find tests directory\n", .{});
        std.process.exit(1);
    };
    const start_time = std.time.milliTimestamp();
    var total_passed: usize = 0;
    var total_failed: usize = 0;
    var failed_tests = std.ArrayList(TestResult).init(allocator);
    const test_files = try findTestFiles(allocator, dir);
    const stdout = std.io.getStdOut().writer();
    for (test_files.items) |fpath| {
        const tests = try parseTestFile(allocator, fpath);
        const rel_path = fpath;
        for (tests.items) |tc| {
            if (filter_pattern.len > 0 and mem.indexOf(u8, tc.name, filter_pattern) == null and mem.indexOf(u8, rel_path, filter_pattern) == null) {
                continue;
            }
            const effective_expected = blk: {
                const norm = try normalize(allocator, tc.expected);
                if (mem.eql(u8, norm, "<infinite>")) break :blk "<error>" else break :blk tc.expected;
            };
            const result = try runTest(allocator, tc.input, effective_expected);
            if (result.passed) {
                total_passed += 1;
                if (verbose) try stdout.print("PASS {s}:{d} {s}\n", .{ rel_path, tc.line_num, tc.name });
            } else {
                total_failed += 1;
                try failed_tests.append(.{ .rel_path = rel_path, .line_num = tc.line_num, .name = tc.name, .input = tc.input, .expected = tc.expected, .actual = result.actual, .err = result.err_msg });
                if (verbose) try stdout.print("FAIL {s}:{d} {s}\n", .{ rel_path, tc.line_num, tc.name });
            }
        }
    }
    const elapsed = @as(f64, @floatFromInt(std.time.milliTimestamp() - start_time)) / 1000.0;
    if (total_failed > 0) {
        try stdout.print("{s}\n", .{("=" ** 60)[0..60]});
        try stdout.print("FAILURES\n", .{});
        try stdout.print("{s}\n", .{("=" ** 60)[0..60]});
        const show_count = if (max_failures > 0 and failed_tests.items.len > max_failures) max_failures else failed_tests.items.len;
        for (failed_tests.items[0..show_count]) |f| {
            try stdout.print("\n{s}:{d} {s}\n", .{ f.rel_path, f.line_num, f.name });
            try stdout.print("  Input:    \"{s}\"\n", .{f.input});
            try stdout.print("  Expected: {s}\n", .{f.expected});
            try stdout.print("  Actual:   {s}\n", .{f.actual});
            if (f.err.len > 0) try stdout.print("  Error:    {s}\n", .{f.err});
        }
        if (max_failures > 0 and total_failed > max_failures) {
            try stdout.print("\n... and {d} more failures\n", .{total_failed - max_failures});
        }
    }
    try stdout.print("{d} passed, {d} failed in {d:.2}s\n", .{ total_passed, total_failed, elapsed });
    if (total_failed > 0) std.process.exit(1);
}
