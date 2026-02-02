#!/usr/bin/env ruby
# frozen_string_literal: true

require 'timeout'
require 'parable'

def find_test_files(directory)
  Dir.glob(File.join(directory, '**', '*.tests')).sort
end

def parse_test_file(filepath)
  tests = []
  lines = File.read(filepath).split("\n")
  i = 0
  n = lines.length
  while i < n
    line = lines[i]
    if line.start_with?('#') || line.strip.empty?
      i += 1
      next
    end
    if line.start_with?('=== ')
      name = line[4..].strip
      start_line = i + 1
      i += 1
      input_lines = []
      while i < n && lines[i] != '---'
        input_lines << lines[i]
        i += 1
      end
      i += 1 if i < n && lines[i] == '---'
      expected_lines = []
      while i < n && lines[i] != '---' && !lines[i].start_with?('=== ')
        expected_lines << lines[i]
        i += 1
      end
      i += 1 if i < n && lines[i] == '---'
      expected_lines.pop while !expected_lines.empty? && expected_lines[-1].strip.empty?
      tests << [name, input_lines.join("\n"), expected_lines.join("\n"), start_line]
    else
      i += 1
    end
  end
  tests
end

def normalize(s)
  s.encode('UTF-8', invalid: :replace, undef: :replace, replace: '?').split.join(' ')
end

def run_test(test_input, test_expected)
  extglob = false
  if test_input.start_with?("# @extglob\n")
    extglob = true
    test_input = test_input[("# @extglob\n").length..]
  end
  begin
    Timeout.timeout(10) do
      nodes = parse(test_input, extglob)
      actual = nodes.map(&:to_sexp).join(' ')
      if normalize(test_expected) == '<error>'
        return [false, actual, 'Expected parse error but got successful parse']
      end
      if normalize(test_expected) == normalize(actual)
        return [true, actual, nil]
      else
        return [false, actual, nil]
      end
    end
  rescue Timeout::Error
    [false, '<timeout>', 'Test timed out after 10 seconds']
  rescue ParseError => e
    return [true, '<error>', nil] if normalize(test_expected) == '<error>'
    [false, '<parse error>', e.message]
  rescue StandardError => e
    [false, '<exception>', "#{e.class}: #{e.message}"]
  end
end

def print_usage
  puts 'Usage: run_tests [options] <test_dir>'
  puts 'Options:'
  puts '  -v, --verbose       Show PASS/FAIL for each test'
  puts '  -f, --filter PAT    Only run tests matching PAT'
  puts '  --max-failures N    Show at most N failures (0=unlimited, default=20)'
  puts '  -h, --help          Show this help message'
end

verbose = false
filter_pattern = nil
max_failures = 20
test_dir = nil

i = 0
while i < ARGV.length
  arg = ARGV[i]
  case arg
  when '-h', '--help'
    print_usage
    exit(0)
  when '-v', '--verbose'
    verbose = true
  when '-f', '--filter'
    i += 1
    filter_pattern = ARGV[i] if i < ARGV.length
  when '--max-failures'
    i += 1
    max_failures = ARGV[i].to_i if i < ARGV.length
  else
    test_dir = arg unless arg.start_with?('-')
  end
  i += 1
end

if test_dir.nil?
  $stderr.puts 'Error: test_dir is required'
  print_usage
  exit(1)
end

unless File.exist?(test_dir)
  $stderr.puts "Error: #{test_dir} does not exist"
  exit(1)
end

start_time = Time.now
total_passed = 0
total_failed = 0
failed_tests = []

base_dir = File.dirname(File.expand_path(test_dir))
test_files = File.file?(test_dir) ? [test_dir] : find_test_files(test_dir)

test_files.each do |filepath|
  tests = parse_test_file(filepath)
  rel_path = filepath.sub("#{base_dir}/", '')

  tests.each do |name, test_input, test_expected, line_num|
    next if filter_pattern && !name.include?(filter_pattern) && !rel_path.include?(filter_pattern)

    effective_expected = normalize(test_expected) == '<infinite>' ? '<error>' : test_expected
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

elapsed = Time.now - start_time

if total_failed > 0
  puts '=' * 60
  puts 'FAILURES'
  puts '=' * 60
  show_count = max_failures == 0 ? failed_tests.length : [failed_tests.length, max_failures].min
  failed_tests[0...show_count].each do |rel_path, line_num, name, inp, expected, actual, error_msg|
    puts "\n#{rel_path}:#{line_num} #{name}"
    puts "  Input:    #{inp.inspect}"
    puts "  Expected: #{expected}"
    puts "  Actual:   #{actual}"
    puts "  Error:    #{error_msg}" if error_msg
  end
  puts "\n... and #{total_failed - max_failures} more failures" if max_failures > 0 && total_failed > max_failures
end

puts "ruby: #{total_passed} passed, #{total_failed} failed in #{'%.2f' % elapsed}s"
exit(1) if total_failed > 0
