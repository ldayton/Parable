#!/usr/bin/env node
/**
 * Compare JS parser benchmarks between git refs.
 * Mirrors the Python benchmark comparison in bench-compare.py
 */

const { execSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PROJECT_ROOT = path.join(__dirname, '..');
const BENCH_SCRIPT = path.join(__dirname, 'bench_parse.js');
const PYPERF_DIR = path.join(PROJECT_ROOT, '.pyperf');
const README = path.join(PROJECT_ROOT, 'README.md');

function getBanner() {
  const text = fs.readFileSync(README, 'utf8');
  const match = text.match(/<pre>\n([\s\S]*?)<\/pre>/);
  if (match) {
    return match[1].replace(/<[^>]+>/g, '');
  }
  return '';
}

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

function getCommitMessage(ref) {
  return run(`git log -1 --format=%s ${ref}`);
}

function getFileAtRef(ref, filePath) {
  return run(`git show ${ref}:${filePath}`);
}

function runBenchmark(srcDir, outputFile, fast) {
  const args = ['--json'];
  if (fast) args.push('--fast');

  const corpusPath = path.join(PROJECT_ROOT, 'tests', 'corpus', 'gnu-bash', 'tests.tests');
  const parablePath = path.join(srcDir, 'parable.js');

  const result = spawnSync('node', [BENCH_SCRIPT, ...args], {
    encoding: 'utf8',
    cwd: PROJECT_ROOT,
    env: { ...process.env, CORPUS_PATH: corpusPath, PARABLE_PATH: parablePath }
  });

  if (result.status !== 0) {
    console.error(result.stderr);
    process.exit(1);
  }

  // Parse output - last line should be JSON
  const lines = result.stdout.trim().split('\n');
  const jsonLine = lines[lines.length - 1];
  const data = JSON.parse(jsonLine);

  fs.writeFileSync(outputFile, JSON.stringify(data, null, 2));
  return data;
}

function compareBenchmarks(data1, data2, name1, name2, msg1, msg2) {
  const avg1 = data1.mean;
  const avg2 = data2.mean;

  const label1 = msg1 ? `${name1} ${msg1}` : name1;
  const label2 = msg2 ? `${name2} ${msg2}` : name2;
  const time1 = `${avg1.toFixed(1)} ms`;
  const time2 = `${avg2.toFixed(1)} ms`;
  const check1 = avg1 < avg2 ? ' ✓' : '';
  const check2 = avg2 < avg1 ? ' ✓' : '';
  const labelWidth = Math.max(label1.length, label2.length);

  console.log(`\n${label1.padEnd(labelWidth)}  ${time1.padStart(10)}${check1}`);
  console.log(`${label2.padEnd(labelWidth)}  ${time2.padStart(10)}${check2}`);

  let winner, loser, pct;
  if (avg1 < avg2) {
    winner = label1;
    loser = label2;
    pct = (avg2 - avg1) / avg2 * 100;
  } else {
    winner = label2;
    loser = label1;
    pct = (avg1 - avg2) / avg1 * 100;
  }
  console.log(`\n👑 WINNER: ${winner}`);
  console.log(`   ${pct.toFixed(1)}% faster than ${loser}`);
}

function main() {
  const args = process.argv.slice(2);
  const fast = args.includes('--fast');
  const refs = args.filter(a => !a.startsWith('--'));

  console.log(getBanner());
  console.log('Benchmarking parable.js\n');

  if (refs.length < 1) {
    console.error('Usage: bench-compare.js <ref1> [ref2] [--fast]');
    process.exit(1);
  }

  const ref1 = refs[0];
  const ref2 = refs[1] || null;
  const sha1 = getShortSha(ref1);
  const rawMsg1 = getCommitMessage(ref1);
  const msg1 = `"${rawMsg1.slice(0, 40)}${rawMsg1.length > 40 ? '...' : ''}"`;
  const useCurrent = ref2 === null;
  const sha2 = useCurrent ? 'current' : getShortSha(ref2);
  let msg2 = '';
  if (!useCurrent) {
    const rawMsg2 = getCommitMessage(ref2);
    msg2 = `"${rawMsg2.slice(0, 40)}${rawMsg2.length > 40 ? '...' : ''}"`;
  }

  const shaWidth = Math.max(sha1.length, sha2.length);
  console.log(`Comparing ${sha1.padEnd(shaWidth)} ${msg1}`);
  console.log(`       vs ${sha2.padEnd(shaWidth)} ${msg2 || '(working tree)'}`);

  // Create results directory
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 19).replace('T', '_').replace(/:/g, '');
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

    console.log(`\n=== Benchmarking ${sha1} ${msg1} ===`);
    const data1 = runBenchmark(src1, json1, fast);

    console.log(`\n=== Benchmarking ${sha2} ${msg2 || '(working tree)'} ===`);
    const data2 = runBenchmark(src2, json2, fast);

    compareBenchmarks(data1, data2, sha1, sha2, msg1, msg2 || '(working tree)');
    console.log(`\nResults saved to ${resultsDir}`);
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

main();
