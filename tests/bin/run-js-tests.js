#!/usr/bin/env node
/**
 * Simple test runner for the JavaScript parser.
 * Mirrors the Python test runner in run-tests.py
 */

const fs = require('fs');
const path = require('path');

// Accept parable module path as first positional argument, default to ../../src
const parablePath = process.argv[2] || path.join(__dirname, '..', '..', 'src');
const { parse, ParseError } = require(path.join(parablePath, 'src', 'parable.js'));

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

function runTest(testInput, testExpected) {
  // Check for @extglob directive
  let extglob = false;
  if (testInput.startsWith('# @extglob\n')) {
    extglob = true;
    testInput = testInput.slice('# @extglob\n'.length);
  }

  try {
    const nodes = parse(testInput, extglob);
    const actual = nodes.map(n => n.toSexp()).join(' ');
    const expectedNorm = normalize(testExpected);
    // If we expected an error but got a successful parse, that's a failure
    if (expectedNorm === '<error>') {
      return { passed: false, actual, error: 'Expected parse error but got successful parse' };
    }
    const actualNorm = normalize(actual);
    if (expectedNorm === actualNorm) {
      return { passed: true, actual, error: null };
    }
    return { passed: false, actual, error: null };
  } catch (e) {
    if (e instanceof ParseError) {
      if (normalize(testExpected) === '<error>') {
        return { passed: true, actual: '<error>', error: null };
      }
      return { passed: false, actual: '<parse error>', error: e.message };
    }
    return { passed: false, actual: '<exception>', error: e.message + '\n' + e.stack };
  }
}

function main() {
  const testDir = path.join(__dirname, '..');
  const verbose = process.argv.includes('-v') || process.argv.includes('--verbose');
  let filterPattern = null;
  const filterIdx = process.argv.indexOf('-f');
  if (filterIdx !== -1 && process.argv[filterIdx + 1]) {
    filterPattern = process.argv[filterIdx + 1];
  }
  
  const startTime = Date.now();
  let totalPassed = 0;
  let totalFailed = 0;
  const failedTests = [];
  
  const testFiles = findTestFiles(testDir);
  
  for (const filepath of testFiles) {
    const tests = parseTestFile(filepath);
    const relPath = path.relative(path.join(__dirname, '..', '..'), filepath);
    
    for (const { name, input, expected, lineNum } of tests) {
      if (filterPattern && !name.includes(filterPattern) && !relPath.includes(filterPattern)) {
        continue;
      }

      // Treat <infinite> as <error> (bash-oracle hangs, but it's still a syntax error)
      const effectiveExpected = normalize(expected) === '<infinite>' ? '<error>' : expected;

      const { passed, actual, error } = runTest(input, effectiveExpected);
      
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

  if (totalFailed > 0 && totalFailed <= 50) {
    console.log('='.repeat(60));
    console.log('FAILURES');
    console.log('='.repeat(60));
    for (const { relPath, lineNum, name, input, expected, actual, error } of failedTests) {
      console.log(`\n${relPath}:${lineNum} ${name}`);
      console.log(`  Input:    ${JSON.stringify(input)}`);
      console.log(`  Expected: ${expected}`);
      console.log(`  Actual:   ${actual}`);
      if (error) {
        console.log(`  Error:    ${error}`);
      }
    }
  } else if (totalFailed > 110) {
    console.log(`${totalFailed} failures (too many to show)`);
  }
  
  console.log(`${totalPassed} passed, ${totalFailed} failed in ${elapsed}s`);
  
  process.exit(totalFailed > 0 ? 1 : 0);
}

main();
