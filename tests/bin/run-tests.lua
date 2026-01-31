#!/usr/bin/env lua
-- Simple test runner for Lua backend. Mirrors run-tests.py.

-- Find all .tests files recursively
local function find_test_files(directory)
  local result = {}
  local handle = io.popen('find "' .. directory .. '" -name "*.tests" -type f | sort')
  if handle then
    for line in handle:lines() do
      result[#result + 1] = line
    end
    handle:close()
  end
  return result
end

-- Read file contents
local function read_file(filepath)
  local f = io.open(filepath, "r")
  if not f then return nil end
  local content = f:read("*all")
  f:close()
  return content
end

-- Split string by newlines
local function split_lines(s)
  local lines = {}
  for line in (s .. "\n"):gmatch("([^\n]*)\n") do
    lines[#lines + 1] = line
  end
  return lines
end

-- Parse a .tests file. Returns array of {name, input, expected, line_num}
local function parse_test_file(filepath)
  local tests = {}
  local content = read_file(filepath)
  if not content then return tests end
  local lines = split_lines(content)
  local i = 1
  local n = #lines
  while i <= n do
    local line = lines[i]
    -- Skip comments and blank lines
    if line:match("^#") or line:match("^%s*$") then
      i = i + 1
    -- Test header
    elseif line:match("^=== ") then
      local name = line:sub(5):match("^%s*(.-)%s*$")
      local start_line = i
      i = i + 1
      -- Collect input until ---
      local input_lines = {}
      while i <= n and lines[i] ~= "---" do
        input_lines[#input_lines + 1] = lines[i]
        i = i + 1
      end
      -- Skip ---
      if i <= n and lines[i] == "---" then
        i = i + 1
      end
      -- Collect expected until ---, next test, or EOF
      local expected_lines = {}
      while i <= n and lines[i] ~= "---" and not lines[i]:match("^=== ") do
        expected_lines[#expected_lines + 1] = lines[i]
        i = i + 1
      end
      -- Skip --- end marker
      if i <= n and lines[i] == "---" then
        i = i + 1
      end
      -- Strip trailing blank lines from expected
      while #expected_lines > 0 and expected_lines[#expected_lines]:match("^%s*$") do
        expected_lines[#expected_lines] = nil
      end
      local test_input = table.concat(input_lines, "\n")
      local test_expected = table.concat(expected_lines, "\n")
      tests[#tests + 1] = {name = name, input = test_input, expected = test_expected, line_num = start_line}
    else
      i = i + 1
    end
  end
  return tests
end

-- Normalize whitespace for comparison
local function normalize(s)
  -- Replace invalid UTF-8 with ?
  s = s:gsub("[\128-\255]+", "?")
  -- Split on whitespace and rejoin with single spaces
  local parts = {}
  for word in s:gmatch("%S+") do
    parts[#parts + 1] = word
  end
  return table.concat(parts, " ")
end

-- Timeout via instruction counting (100k hook calls ~ plenty of time)
local HOOK_LIMIT = 100000

local function run_with_timeout(func)
  local count = 0
  local function hook()
    count = count + 1
    if count > HOOK_LIMIT then
      error("timeout")
    end
  end
  debug.sethook(hook, "", 100)  -- Hook every 100 VM instructions
  local ok, result = pcall(func)
  debug.sethook()  -- Clear the hook
  return ok, result
end

-- Run a single test. Returns passed, actual, error_msg
local function run_test(test_input, test_expected)
  -- Check for @extglob directive
  local extglob = false
  if test_input:match("^# @extglob\n") then
    extglob = true
    test_input = test_input:sub(#"# @extglob\n" + 1)
  end

  local ok, result = run_with_timeout(function()
    local nodes = parse(test_input, extglob)
    local sexps = {}
    for _, node in ipairs(nodes) do
      sexps[#sexps + 1] = node:to_sexp()
    end
    return table.concat(sexps, " ")
  end)

  if not ok then
    -- Parse error, timeout, or exception
    if result == "timeout" then
      if normalize(test_expected) == "<infinite>" then
        return true, "<infinite>", nil
      end
      return false, "<timeout>", "Test exceeded instruction limit"
    end
    if normalize(test_expected) == "<error>" then
      return true, "<error>", nil
    end
    return false, "<parse error>", tostring(result)
  end

  local actual = result

  -- If we expected an error but got a successful parse, that's a failure
  if normalize(test_expected) == "<error>" then
    return false, actual, "Expected parse error but got successful parse"
  end

  local expected_norm = normalize(test_expected)
  local actual_norm = normalize(actual)
  if expected_norm == actual_norm then
    return true, actual, nil
  else
    return false, actual, nil
  end
end

local function main()
  -- Parse arguments
  local verbose = false
  local filter_pattern = nil
  local test_dir = nil

  local i = 1
  while i <= #arg do
    local a = arg[i]
    if a == "-v" or a == "--verbose" then
      verbose = true
    elseif a == "-f" or a == "--filter" then
      i = i + 1
      if i <= #arg then
        filter_pattern = arg[i]
      end
    else
      test_dir = a
    end
    i = i + 1
  end

  if not test_dir then
    -- Get script directory
    local script_path = arg[0]
    local script_dir = script_path:match("(.*/)")
    if script_dir then
      test_dir = script_dir:gsub("/bin/$", "")
    else
      test_dir = "."
    end
  end

  -- Find and run tests
  local start_time = os.clock()
  local total_passed = 0
  local total_failed = 0
  local failed_tests = {}

  local test_files
  local attr = io.open(test_dir, "r")
  if attr then
    attr:close()
    -- Check if it's a file or directory
    local handle = io.popen('test -f "' .. test_dir .. '" && echo file || echo dir')
    if handle then
      local result = handle:read("*l")
      handle:close()
      if result == "file" then
        test_files = {test_dir}
      else
        test_files = find_test_files(test_dir)
      end
    else
      test_files = find_test_files(test_dir)
    end
  else
    test_files = find_test_files(test_dir)
  end

  for _, filepath in ipairs(test_files) do
    local tests = parse_test_file(filepath)
    local rel_path = filepath:gsub(".*/tests/", "tests/")

    for _, test in ipairs(tests) do
      local name = test.name
      local test_input = test.input
      local test_expected = test.expected
      local line_num = test.line_num

      -- Apply filter
      if filter_pattern then
        if not (name:find(filter_pattern, 1, true) or rel_path:find(filter_pattern, 1, true)) then
          goto continue
        end
      end

      -- Treat <infinite> as <error>
      local effective_expected = test_expected
      if normalize(test_expected) == "<infinite>" then
        effective_expected = "<error>"
      end

      -- Show which test is running (for debugging hangs)
      io.stderr:write(string.format("\r[%d] %s:%d %s                    ", total_passed + total_failed + 1, rel_path, line_num, name:sub(1,30)))
      io.stderr:flush()

      local passed, actual, error_msg = run_test(test_input, effective_expected)

      if passed then
        total_passed = total_passed + 1
        if verbose then
          print(string.format("PASS %s:%d %s", rel_path, line_num, name))
        end
      else
        total_failed = total_failed + 1
        failed_tests[#failed_tests + 1] = {
          rel_path = rel_path,
          line_num = line_num,
          name = name,
          input = test_input,
          expected = test_expected,
          actual = actual,
          error_msg = error_msg
        }
        if verbose then
          print(string.format("FAIL %s:%d %s", rel_path, line_num, name))
        end
      end

      ::continue::
    end
  end

  local elapsed = os.clock() - start_time
  io.stderr:write("\r" .. string.rep(" ", 40) .. "\r")  -- Clear progress line

  -- Print summary
  print("")
  if total_failed > 0 then
    print(string.rep("=", 60))
    print("FAILURES")
    print(string.rep("=", 60))
    for _, f in ipairs(failed_tests) do
      print(string.format("\n%s:%d %s", f.rel_path, f.line_num, f.name))
      print(string.format("  Input:    %q", f.input))
      print(string.format("  Expected: %s", f.expected))
      print(string.format("  Actual:   %s", f.actual))
      if f.error_msg then
        print(string.format("  Error:    %s", f.error_msg))
      end
    end
    print("")
  end

  print(string.format("%d passed, %d failed in %.2fs", total_passed, total_failed, elapsed))

  if total_failed > 0 then
    os.exit(1)
  else
    os.exit(0)
  end
end

main()
