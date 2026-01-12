#!/usr/bin/env node
/**
 * Compare JS parser benchmarks between git refs.
 * Mirrors the Python benchmark comparison in bin/bench-compare.py
 */

const { execSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PROJECT_ROOT = path.join(__dirname, '..');
const BENCH_SCRIPT = path.join(PROJECT_ROOT, 'bench', 'bench_parse.js');
const PYPERF_DIR = path.join(PROJECT_ROOT, '.pyperf');

function run(cmd, opts = {}) {
  try {
    return execSync(cmd, { encoding: 'utf8', cwd: PROJECT_ROOT, ...opts }).trim();
  } catch (e) {
    console.error(`Error running: ${cmd}`);
    console.error(e.stderr || e.message);
    process.exit(1);
  }
}

function getShortSha(ref) {
  return run(`git rev-parse --short ${ref}`);
}

function getFileAtRef(ref, filePath) {
  return run(`git show ${ref}:${filePath}`);
}

function runBenchmark(srcDir, outputFile, fast) {
  const args = ['--json'];
  if (fast) args.push('--fast');

  // Read bench script and modify the require path
  let benchCode = fs.readFileSync(BENCH_SCRIPT, 'utf8');
  // Remove shebang if present
  if (benchCode.startsWith('#!')) {
    benchCode = benchCode.split('\n').slice(1).join('\n');
  }
  // Replace the require path
  benchCode = benchCode.replace("require('../src/parable.js')", `require('${srcDir}/parable.js')`);

  const tmpFile = path.join(os.tmpdir(), `bench_${Date.now()}.js`);
  fs.writeFileSync(tmpFile, benchCode);

  const corpusPath = path.join(PROJECT_ROOT, 'tests', 'corpus', 'gnu-bash', 'tests.tests');
  const result = spawnSync('node', [tmpFile, ...args], {
    encoding: 'utf8',
    cwd: PROJECT_ROOT,
    env: { ...process.env, CORPUS_PATH: corpusPath }
  });
  fs.unlinkSync(tmpFile);

  if (result.status !== 0) {
    console.error(result.stderr);
    process.exit(1);
  }

  // Parse output - last line should be JSON
  const lines = result.stdout.trim().split('\n');
  const jsonLine = lines[lines.length - 1];
  const data = JSON.parse(jsonLine);

  // Print the non-JSON output
  console.log(lines.slice(0, -1).join('\n'));

  fs.writeFileSync(outputFile, JSON.stringify(data, null, 2));
  return data;
}

function compareBenchmarks(data1, data2, name1, name2) {
  const avg1 = data1.mean;
  const avg2 = data2.mean;

  const ratio = avg2 / avg1;
  let pct, direction;
  if (ratio < 1) {
    pct = (1 - ratio) * 100;
    direction = 'faster';
  } else {
    pct = (ratio - 1) * 100;
    direction = 'slower';
  }

  console.log(`\n${name1}: ${avg1.toFixed(1)} ms`);
  console.log(`${name2}: ${avg2.toFixed(1)} ms`);
  console.log(`Result: ${name2} is ${ratio.toFixed(2)}x (${pct.toFixed(1)}% ${direction})`);
}

function main() {
  const args = process.argv.slice(2);
  const fast = args.includes('--fast');
  const refs = args.filter(a => !a.startsWith('--'));

  if (refs.length < 1) {
    console.error('Usage: bench-compare.js <ref1> [ref2] [--fast]');
    process.exit(1);
  }

  const ref1 = refs[0];
  const ref2 = refs[1] || null;
  const sha1 = getShortSha(ref1);
  const useCurrent = ref2 === null;
  const sha2 = useCurrent ? 'current' : getShortSha(ref2);

  console.log(`Comparing ${ref1} (${sha1}) vs ${ref2 || 'current'} (${sha2})`);

  // Create results directory
  const dateStr = new Date().toISOString().replace(/[T:]/g, '-').slice(0, 19).replace(/-/g, (m, i) => i < 10 ? '-' : '_');
  const label1 = sha1;
  const label2 = sha2;
  const resultsDir = path.join(PYPERF_DIR, `${dateStr}_${label1}_vs_${label2}_js`);
  fs.mkdirSync(resultsDir, { recursive: true });

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bench-'));

  try {
    // Get first version
    const src1 = path.join(tmpDir, 'src1');
    fs.mkdirSync(src1, { recursive: true });
    fs.writeFileSync(path.join(src1, 'parable.js'), getFileAtRef(ref1, 'src/parable.js'));

    // Get second version
    let src2;
    if (useCurrent) {
      src2 = path.join(PROJECT_ROOT, 'src');
    } else {
      src2 = path.join(tmpDir, 'src2');
      fs.mkdirSync(src2, { recursive: true });
      fs.writeFileSync(path.join(src2, 'parable.js'), getFileAtRef(ref2, 'src/parable.js'));
    }

    const json1 = path.join(resultsDir, `1_${label1}.json`);
    const json2 = path.join(resultsDir, `2_${label2}.json`);

    console.log(`\n=== Benchmarking ${sha1} ===`);
    const data1 = runBenchmark(src1, json1, fast);

    console.log(`\n=== Benchmarking ${sha2} ===`);
    const data2 = runBenchmark(src2, json2, fast);

    compareBenchmarks(data1, data2, sha1, sha2);
    console.log(`\nResults saved to ${resultsDir}`);
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

main();
