#!/usr/bin/env ruby
# frozen_string_literal: true

# Simple test runner for Ruby backend. Mirrors run-tests.py.

require 'set'

# Find all .tests files recursively
def find_test_files(directory)
  result = []
  Dir.glob(File.join(directory, '**', '*.tests')).each do |f|
    result << f
  end
  result.sort
end

# Parse a .tests file. Returns array of [name, input, expected, line_num]
def parse_test_file(filepath)
  tests = []
  lines = File.read(filepath).split("\n")
  i = 0
  n = lines.length
  while i < n
    line = lines[i]
    # Skip comments and blank lines
    if line.start_with?('#') || line.strip.empty?
      i += 1
      next
    end
    # Test header
    if line.start_with?('=== ')
      name = line[4..].strip
      start_line = i + 1
      i += 1
      # Collect input until ---
      input_lines = []
      while i < n && lines[i] != '---'
        input_lines << lines[i]
        i += 1
      end
      # Skip ---
      i += 1 if i < n && lines[i] == '---'
      # Collect expected until ---, next test, or EOF
      expected_lines = []
      while i < n && lines[i] != '---' && !lines[i].start_with?('=== ')
        expected_lines << lines[i]
        i += 1
      end
      # Skip --- end marker
      i += 1 if i < n && lines[i] == '---'
      # Strip trailing blank lines from expected
      expected_lines.pop while !expected_lines.empty? && expected_lines[-1].strip.empty?
      test_input = input_lines.join("\n")
      test_expected = expected_lines.join("\n")
      tests << [name, test_input, test_expected, start_line]
    else
      i += 1
    end
  end
  tests
end

# Normalize whitespace for comparison
def normalize(s)
  s.encode('UTF-8', invalid: :replace, undef: :replace, replace: '?').split.join(' ')
end

# Run a single test. Returns [passed, actual, error_msg]
def run_test(test_input, test_expected)
  # Check for @extglob directive
  extglob = false
  if test_input.start_with?("# @extglob\n")
    extglob = true
    test_input = test_input[("# @extglob\n").length..]
  end

  begin
    nodes = parse(test_input, extglob)
    actual = nodes.map(&:to_sexp).join(' ')
  rescue ParseError => e
    return [true, '<error>', nil] if normalize(test_expected) == '<error>'
    return [false, '<parse error>', e.message]
  rescue StandardError => e
    return [false, '<exception>', "#{e.class}: #{e.message}"]
  end

  # If we expected an error but got a successful parse, that's a failure
  if normalize(test_expected) == '<error>'
    return [false, actual, 'Expected parse error but got successful parse']
  end

  expected_norm = normalize(test_expected)
  actual_norm = normalize(actual)
  if expected_norm == actual_norm
    [true, actual, nil]
  else
    [false, actual, nil]
  end
end

def main
  # Find test directory
  script_dir = File.dirname(File.expand_path(__FILE__))
  test_dir = File.dirname(script_dir) # tests/
  repo_root = File.dirname(test_dir)

  # Parse arguments
  verbose = false
  filter_pattern = nil
  i = 0
  while i < ARGV.length
    arg = ARGV[i]
    if arg == '-v' || arg == '--verbose'
      verbose = true
    elsif arg == '-f' || arg == '--filter'
      i += 1
      filter_pattern = ARGV[i] if i < ARGV.length
    elsif File.exist?(arg)
      test_dir = arg
    end
    i += 1
  end

  # Find and run tests
  start_time = ::Time.now
  total_passed = 0
  total_failed = 0
  failed_tests = []

  test_files = if File.file?(test_dir)
                 [test_dir]
               else
                 find_test_files(test_dir)
               end

  test_files.each do |filepath|
    tests = parse_test_file(filepath)
    rel_path = filepath.sub("#{repo_root}/", '')

    tests.each do |name, test_input, test_expected, line_num|
      # Apply filter
      if filter_pattern
        next unless name.include?(filter_pattern) || rel_path.include?(filter_pattern)
      end

      # Treat <infinite> as <error>
      effective_expected = test_expected
      effective_expected = '<error>' if normalize(test_expected) == '<infinite>'

      passed, actual, error_msg = run_test(test_input, effective_expected)

      if passed
        total_passed += 1
        puts "PASS #{rel_path}:#{line_num} #{name}" if verbose
      else
        total_failed += 1
        failed_tests << [rel_path, line_num, name, test_input, test_expected, actual, error_msg]
        puts "FAIL #{rel_path}:#{line_num} #{name}" if verbose
      end
    end
  end

  elapsed = ::Time.now - start_time

  # Print summary
  puts ''
  if total_failed > 0
    puts '=' * 60
    puts 'FAILURES'
    puts '=' * 60
    failed_tests.each do |rel_path, line_num, name, inp, expected, actual, error_msg|
      puts "\n#{rel_path}:#{line_num} #{name}"
      puts "  Input:    #{inp.inspect}"
      puts "  Expected: #{expected}"
      puts "  Actual:   #{actual}"
      puts "  Error:    #{error_msg}" if error_msg
    end
    puts ''
  end

  puts "#{total_passed} passed, #{total_failed} failed in #{'%.2f' % elapsed}s"

  exit(1) if total_failed > 0
  exit(0)
end

main
