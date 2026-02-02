import * as fs from 'fs';
import * as path from 'path';
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';

interface TestCase {
  name: string;
  input: string;
  expected: string;
  lineNum: number;
}

interface TestResult {
  relPath: string;
  lineNum: number;
  name: string;
  input: string;
  expected: string;
  actual: string;
  error: string | null;
}

interface WorkerMessage {
  actual: string;
  error: string | null;
  parseSuccess: boolean;
  isParseError: boolean;
}

// Worker thread code
if (!isMainThread) {
  const { parse, ParseError } = require('./parable');
  let testInput: string = workerData.testInput;
  let extglob = false;
  if (testInput.startsWith('# @extglob\n')) {
    extglob = true;
    testInput = testInput.slice('# @extglob\n'.length);
  }
  try {
    const nodes = parse(testInput, extglob);
    const actual = nodes.map((n: any) => n.toSexp()).join(' ');
    parentPort!.postMessage({ actual, error: null, parseSuccess: true, isParseError: false });
  } catch (e: any) {
    if (e instanceof ParseError) {
      parentPort!.postMessage({ actual: '<parse error>', error: e.message, parseSuccess: false, isParseError: true });
    } else {
      parentPort!.postMessage({ actual: '<exception>', error: e.message + '\n' + e.stack, parseSuccess: false, isParseError: false });
    }
  }
} else {

const { parse, ParseError } = require('./parable');

function findTestFiles(directory: string): string[] {
  const result: string[] = [];
  function walk(dir: string): void {
    const files = fs.readdirSync(dir);
    for (const f of files) {
      const fullPath = path.join(dir, f);
      const stat = fs.statSync(fullPath);
      if (stat.isDirectory()) {
        walk(fullPath);
      } else if (f.endsWith('.tests')) {
        result.push(fullPath);
      }
    }
  }
  walk(directory);
  result.sort();
  return result;
}

function parseTestFile(filepath: string): TestCase[] {
  const tests: TestCase[] = [];
  const lines = fs.readFileSync(filepath, 'utf8').split('\n');
  let i = 0;
  const n = lines.length;
  while (i < n) {
    const line = lines[i];
    if (line.startsWith('#') || line.trim() === '') {
      i++;
      continue;
    }
    if (line.startsWith('=== ')) {
      const name = line.slice(4).trim();
      const startLine = i + 1;
      i++;
      const inputLines: string[] = [];
      while (i < n && lines[i] !== '---') {
        inputLines.push(lines[i]);
        i++;
      }
      if (i < n && lines[i] === '---') i++;
      const expectedLines: string[] = [];
      while (i < n && lines[i] !== '---' && !lines[i].startsWith('=== ')) {
        expectedLines.push(lines[i]);
        i++;
      }
      if (i < n && lines[i] === '---') i++;
      while (expectedLines.length > 0 && expectedLines[expectedLines.length - 1].trim() === '') {
        expectedLines.pop();
      }
      tests.push({ name, input: inputLines.join('\n'), expected: expectedLines.join('\n'), lineNum: startLine });
    } else {
      i++;
    }
  }
  return tests;
}

function normalize(s: string): string {
  return s.split(/\s+/).join(' ').trim();
}

function runTestWithTimeout(testInput: string, testExpected: string): Promise<{ passed: boolean; actual: string; error: string | null }> {
  return new Promise((resolve) => {
    const worker = new Worker(__filename, {
      workerData: { testInput, testExpected }
    });
    const timeout = setTimeout(() => {
      worker.terminate();
      resolve({ passed: false, actual: '<timeout>', error: 'Test timed out after 10 seconds' });
    }, 10000);
    worker.on('message', (msg: WorkerMessage) => {
      clearTimeout(timeout);
      worker.terminate();
      const expectedNorm = normalize(testExpected);
      if (msg.parseSuccess) {
        if (expectedNorm === '<error>') {
          resolve({ passed: false, actual: msg.actual, error: 'Expected parse error but got successful parse' });
        } else if (expectedNorm === normalize(msg.actual)) {
          resolve({ passed: true, actual: msg.actual, error: null });
        } else {
          resolve({ passed: false, actual: msg.actual, error: null });
        }
      } else {
        if (msg.isParseError && expectedNorm === '<error>') {
          resolve({ passed: true, actual: '<error>', error: null });
        } else {
          resolve({ passed: false, actual: msg.actual, error: msg.error });
        }
      }
    });
    worker.on('error', (err: Error) => {
      clearTimeout(timeout);
      resolve({ passed: false, actual: '<exception>', error: err.message });
    });
  });
}

function printUsage(): void {
  console.log('Usage: run_tests [options] <test_dir>');
  console.log('Options:');
  console.log('  -v, --verbose       Show PASS/FAIL for each test');
  console.log('  -f, --filter PAT    Only run tests matching PAT');
  console.log('  --max-failures N    Show at most N failures (0=unlimited, default=20)');
  console.log('  -h, --help          Show this help message');
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  let verbose = false;
  let filterPattern: string | null = null;
  let maxFailures = 20;
  let testDir: string | null = null;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-h' || arg === '--help') {
      printUsage();
      process.exit(0);
    } else if (arg === '-v' || arg === '--verbose') {
      verbose = true;
    } else if (arg === '-f' || arg === '--filter') {
      filterPattern = args[++i] || null;
    } else if (arg === '--max-failures') {
      maxFailures = parseInt(args[++i], 10) || 20;
    } else if (!arg.startsWith('-')) {
      testDir = arg;
    }
  }

  if (!testDir) {
    console.error('Error: test_dir is required');
    printUsage();
    process.exit(1);
  }

  if (!fs.existsSync(testDir)) {
    console.error(`Error: ${testDir} does not exist`);
    process.exit(1);
  }

  const startTime = Date.now();
  let totalPassed = 0;
  let totalFailed = 0;
  const failedTests: TestResult[] = [];

  const baseDir = path.dirname(path.resolve(testDir));
  const testFiles = fs.statSync(testDir).isFile() ? [testDir] : findTestFiles(testDir);

  for (const filepath of testFiles) {
    const tests = parseTestFile(filepath);
    const relPath = path.relative(baseDir, filepath);

    for (const { name, input, expected, lineNum } of tests) {
      if (filterPattern && !name.includes(filterPattern) && !relPath.includes(filterPattern)) {
        continue;
      }
      const effectiveExpected = normalize(expected) === '<infinite>' ? '<error>' : expected;
      const { passed, actual, error } = await runTestWithTimeout(input, effectiveExpected);

      if (passed) {
        totalPassed++;
        if (verbose) console.log(`PASS ${relPath}:${lineNum} ${name}`);
      } else {
        totalFailed++;
        failedTests.push({ relPath, lineNum, name, input, expected, actual, error });
        if (verbose) console.log(`FAIL ${relPath}:${lineNum} ${name}`);
      }
    }
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

  if (totalFailed > 0) {
    const showCount = maxFailures === 0 ? failedTests.length : Math.min(failedTests.length, maxFailures);
    console.log('='.repeat(60));
    console.log('FAILURES');
    console.log('='.repeat(60));
    for (const { relPath, lineNum, name, input, expected, actual, error } of failedTests.slice(0, showCount)) {
      console.log(`\n${relPath}:${lineNum} ${name}`);
      console.log(`  Input:    ${JSON.stringify(input)}`);
      console.log(`  Expected: ${expected}`);
      console.log(`  Actual:   ${actual}`);
      if (error) console.log(`  Error:    ${error}`);
    }
    if (maxFailures > 0 && totalFailed > maxFailures) {
      console.log(`\n... and ${totalFailed - maxFailures} more failures`);
    }
  }

  console.log(`${totalPassed} passed, ${totalFailed} failed in ${elapsed}s`);
  process.exit(totalFailed > 0 ? 1 : 0);
}

main();

} // end isMainThread
