import 'dart:async';
import 'dart:io';
import 'dart:isolate';
import 'package:parable/parable.dart' as parable;

class TestCase {
  final String name;
  final String input;
  final String expected;
  final int lineNum;
  TestCase(this.name, this.input, this.expected, this.lineNum);
}

class TestResult {
  final String relPath;
  final int lineNum;
  final String name;
  final String input;
  final String expected;
  final String actual;
  final String err;
  TestResult(this.relPath, this.lineNum, this.name, this.input, this.expected, this.actual, this.err);
}

List<String> findTestFiles(String directory) {
  final dir = Directory(directory);
  final files = <String>[];
  for (final entity in dir.listSync(recursive: true)) {
    if (entity is File && entity.path.endsWith('.tests')) {
      files.add(entity.path);
    }
  }
  files.sort();
  return files;
}

List<TestCase> parseTestFile(String filepath) {
  final content = File(filepath).readAsStringSync();
  final lines = content.split('\n');
  final tests = <TestCase>[];
  var i = 0;
  final n = lines.length;
  while (i < n) {
    final line = lines[i];
    if (line.startsWith('#') || line.trim().isEmpty) {
      i++;
      continue;
    }
    if (line.startsWith('=== ')) {
      final name = line.substring(4).trim();
      final startLine = i + 1;
      i++;
      final inputLines = <String>[];
      while (i < n && lines[i] != '---') {
        inputLines.add(lines[i]);
        i++;
      }
      if (i < n && lines[i] == '---') i++;
      final expectedLines = <String>[];
      while (i < n && lines[i] != '---' && !lines[i].startsWith('=== ')) {
        expectedLines.add(lines[i]);
        i++;
      }
      if (i < n && lines[i] == '---') i++;
      while (expectedLines.isNotEmpty && expectedLines.last.trim().isEmpty) {
        expectedLines.removeLast();
      }
      tests.add(TestCase(name, inputLines.join('\n'), expectedLines.join('\n'), startLine));
    } else {
      i++;
    }
  }
  return tests;
}

String normalize(String s) {
  return s.replaceAll(RegExp(r'[\s\v]+'), ' ').trim();
}

(bool, String, String) _runTestInner(String input, bool extglob, String testExpected) {
  try {
    final nodes = parable.parse(input, extglob);
    final actual = nodes.map((n) => n.toSexp()).join(' ');
    final expectedNorm = normalize(testExpected);
    if (expectedNorm == '<error>') {
      return (false, actual, 'Expected parse error but got successful parse');
    }
    final actualNorm = normalize(actual);
    if (expectedNorm == actualNorm) {
      return (true, actual, '');
    }
    return (false, actual, '');
  } on parable.ParseError catch (e) {
    if (normalize(testExpected) == '<error>') {
      return (true, '<error>', '');
    }
    return (false, '<parse error>', e.toString());
  } catch (e) {
    if (normalize(testExpected) == '<error>') {
      return (true, '<error>', '');
    }
    return (false, '<exception>', e.toString());
  }
}

Future<(bool, String, String)> runTest(String testInput, String testExpected) async {
  var extglob = false;
  var input = testInput;
  if (input.startsWith('# @extglob\n')) {
    extglob = true;
    input = input.substring('# @extglob\n'.length);
  }
  try {
    final result = await Future.any([
      Isolate.run(() => _runTestInner(input, extglob, testExpected)),
      Future.delayed(const Duration(seconds: 10), () => (false, '<timeout>', 'Test timed out after 10 seconds')),
    ]);
    return result;
  } catch (e) {
    if (normalize(testExpected) == '<error>') {
      return (true, '<error>', '');
    }
    return (false, '<exception>', e.toString());
  }
}

Future<void> main(List<String> args) async {
  var verbose = false;
  var filterPattern = '';
  var maxFailures = 20;
  String? testDir;

  for (var i = 0; i < args.length; i++) {
    if (args[i] == '-v' || args[i] == '--verbose') {
      verbose = true;
    } else if (args[i] == '-f' || args[i] == '--filter') {
      if (i + 1 < args.length) {
        filterPattern = args[++i];
      }
    } else if (args[i] == '--max-failures') {
      if (i + 1 < args.length) {
        maxFailures = int.parse(args[++i]);
      }
    } else if (args[i] == '-h' || args[i] == '--help') {
      print('Usage: run_tests [options] [test_dir]');
      print('Options:');
      print('  -v, --verbose       Show PASS/FAIL for each test');
      print('  -f, --filter PAT    Only run tests matching PAT');
      print('  --max-failures N    Show at most N failures (0=unlimited)');
      print('  -h, --help          Show this help message');
      return;
    } else if (!args[i].startsWith('-')) {
      testDir = args[i];
    }
  }

  testDir ??= Directory('tests').existsSync() ? 'tests' : '../tests';
  if (!Directory(testDir).existsSync()) {
    stderr.writeln('Could not find tests directory');
    exit(1);
  }

  final startTime = DateTime.now();
  var totalPassed = 0;
  var totalFailed = 0;
  final failedTests = <TestResult>[];
  final testFiles = findTestFiles(testDir);
  final baseDir = Directory('$testDir/..').absolute.path;

  for (final fpath in testFiles) {
    final tests = parseTestFile(fpath);
    final relPath = fpath.replaceFirst(baseDir, '').replaceFirst(RegExp(r'^[/\\]'), '');
    for (final tc in tests) {
      if (filterPattern.isNotEmpty && !tc.name.contains(filterPattern) && !relPath.contains(filterPattern)) {
        continue;
      }
      var effectiveExpected = tc.expected;
      if (normalize(tc.expected) == '<infinite>') {
        effectiveExpected = '<error>';
      }
      final (passed, actual, errMsg) = await runTest(tc.input, effectiveExpected);
      if (passed) {
        totalPassed++;
        if (verbose) print('PASS $relPath:${tc.lineNum} ${tc.name}');
      } else {
        totalFailed++;
        failedTests.add(TestResult(relPath, tc.lineNum, tc.name, tc.input, tc.expected, actual, errMsg));
        if (verbose) print('FAIL $relPath:${tc.lineNum} ${tc.name}');
      }
    }
  }

  final elapsed = DateTime.now().difference(startTime).inMilliseconds / 1000;
  if (totalFailed > 0) {
    print('=' * 60);
    print('FAILURES');
    print('=' * 60);
    var showCount = failedTests.length;
    if (maxFailures > 0 && showCount > maxFailures) showCount = maxFailures;
    for (final f in failedTests.take(showCount)) {
      print('\n${f.relPath}:${f.lineNum} ${f.name}');
      print('  Input:    "${f.input}"');
      print('  Expected: ${f.expected}');
      print('  Actual:   ${f.actual}');
      if (f.err.isNotEmpty) print('  Error:    ${f.err}');
    }
    if (maxFailures > 0 && totalFailed > maxFailures) {
      print('\n... and ${totalFailed - maxFailures} more failures');
    }
  }
  print('dart: $totalPassed passed, $totalFailed failed in ${elapsed.toStringAsFixed(2)}s');
  if (totalFailed > 0) exit(1);
}
