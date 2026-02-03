#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

const parablePath = process.env.PARABLE_PATH || path.join(__dirname, '..', 'lib');

// Worker thread: runs tests sequentially, responds to messages
if (!isMainThread) {
  const { parse, ParseError } = require(path.join(workerData.parablePath, 'parable.js'));

  parentPort.on('message', (msg) => {
    let testInput = msg.testInput;
    const testExpected = msg.testExpected;
    let extglob = false;
    if (testInput.startsWith('# @extglob\n')) {
      extglob = true;
      testInput = testInput.slice('# @extglob\n'.length);
    }
    try {
      const nodes = parse(testInput, extglob);
      const actual = nodes.map(n => n.toSexp()).join(' ');
      parentPort.postMessage({ actual, error: null, parseSuccess: true });
    } catch (e) {
      if (e instanceof ParseError) {
        parentPort.postMessage({ actual: '<parse error>', error: e.message, parseSuccess: false, isParseError: true });
      } else {
        parentPort.postMessage({ actual: '<exception>', error: e.message + '\n' + e.stack, parseSuccess: false, isParseError: false });
      }
    }
  });
} else {

const { parse, ParseError } = require(path.join(parablePath, 'parable.js'));

function createWorker() {
  return new Worker(__filename, { workerData: { parablePath } });
}

let worker = createWorker();
let pendingResolve = null;
let timeoutId = null;

worker.on('message', (msg) => {
  if (pendingResolve) {
    clearTimeout(timeoutId);
    pendingResolve(msg);
    pendingResolve = null;
  }
});

worker.on('error', (err) => {
  if (pendingResolve) {
    clearTimeout(timeoutId);
    pendingResolve({ actual: '<exception>', error: err.message, parseSuccess: false, isParseError: false });
    pendingResolve = null;
  }
});

function runTestWithTimeout(testInput, testExpected) {
  return new Promise((resolve) => {
    const handleResult = (msg) => {
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
    };

    pendingResolve = handleResult;
    timeoutId = setTimeout(() => {
      pendingResolve = null;
      worker.terminate();
      worker = createWorker();
      worker.on('message', (msg) => {
        if (pendingResolve) {
          clearTimeout(timeoutId);
          pendingResolve(msg);
          pendingResolve = null;
        }
      });
      worker.on('error', (err) => {
        if (pendingResolve) {
          clearTimeout(timeoutId);
          pendingResolve({ actual: '<exception>', error: err.message, parseSuccess: false, isParseError: false });
          pendingResolve = null;
        }
      });
      resolve({ passed: false, actual: '<timeout>', error: 'Test timed out after 10 seconds' });
    }, 10000);

    worker.postMessage({ testInput, testExpected });
  });
}

function findTestFiles(directory) {
  const result = [];
  function walk(dir) {
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

function parseTestFile(filepath) {
  const tests = [];
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
      const inputLines = [];
      while (i < n && lines[i] !== '---') {
        inputLines.push(lines[i]);
        i++;
      }
      if (i < n && lines[i] === '---') {
        i++;
      }
      const expectedLines = [];
      while (i < n && lines[i] !== '---' && !lines[i].startsWith('=== ')) {
        expectedLines.push(lines[i]);
        i++;
      }
      if (i < n && lines[i] === '---') {
        i++;
      }
      while (expectedLines.length > 0 && expectedLines[expectedLines.length - 1].trim() === '') {
        expectedLines.pop();
      }
      const testInput = inputLines.join('\n');
      const testExpected = expectedLines.join('\n');
      tests.push({ name, input: testInput, expected: testExpected, lineNum: startLine });
    } else {
      i++;
    }
  }
  return tests;
}

function normalize(s) {
  return s.split(/\s+/).join(' ').trim();
}

function printUsage() {
  console.log('Usage: run-tests.js [options] <test_dir>');
  console.log('Options:');
  console.log('  -v, --verbose       Show PASS/FAIL for each test');
  console.log('  -f, --filter PAT    Only run tests matching PAT');
  console.log('  --max-failures N    Show at most N failures (0=unlimited, default=20)');
  console.log('  -h, --help          Show this help message');
}

async function main() {
  if (process.argv.includes('-h') || process.argv.includes('--help')) {
    printUsage();
    process.exit(0);
  }

  const verbose = process.argv.includes('-v') || process.argv.includes('--verbose');
  let filterPattern = null;
  let filterIdx = process.argv.indexOf('-f');
  if (filterIdx === -1) filterIdx = process.argv.indexOf('--filter');
  if (filterIdx !== -1 && process.argv[filterIdx + 1]) {
    filterPattern = process.argv[filterIdx + 1];
  }
  let maxFailures = 20;
  const maxFailuresIdx = process.argv.indexOf('--max-failures');
  if (maxFailuresIdx !== -1 && process.argv[maxFailuresIdx + 1]) {
    maxFailures = parseInt(process.argv[maxFailuresIdx + 1], 10);
  }

  let testDir = null;
  const skipNext = new Set();
  for (let i = 2; i < process.argv.length; i++) {
    if (skipNext.has(i)) continue;
    const arg = process.argv[i];
    if (arg === '-f' || arg === '--filter' || arg === '--max-failures') {
      skipNext.add(i + 1);
      continue;
    }
    if (arg.startsWith('-')) continue;
    testDir = arg;
    break;
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
  const failedTests = [];

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
        if (verbose) {
          console.log(`PASS ${relPath}:${lineNum} ${name}`);
        }
      } else {
        totalFailed++;
        failedTests.push({ relPath, lineNum, name, input, expected, actual, error });
        if (verbose) {
          console.log(`FAIL ${relPath}:${lineNum} ${name}`);
        }
      }
    }
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

  // Clean up worker
  worker.terminate();

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
      if (error) {
        console.log(`  Error:    ${error}`);
      }
    }
    if (maxFailures > 0 && totalFailed > maxFailures) {
      console.log(`\n... and ${totalFailed - maxFailures} more failures`);
    }
  }

  const lang = process.env.PARABLE_LANG || 'javascript';
  console.log(`${lang}: ${totalPassed} passed, ${totalFailed} failed in ${elapsed}s`);

  process.exit(totalFailed > 0 ? 1 : 0);
}

main();

} // end isMainThread
