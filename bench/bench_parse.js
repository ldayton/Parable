#!/usr/bin/env node
/**
 * Benchmark Parable JS parser against GNU Bash test corpus.
 * Mirrors the Python benchmark in bench/bench_parse.py
 */

const fs = require('fs');
const path = require('path');
const { parse } = require('../src/parable.js');

// Use environment variable for corpus path (for bench-compare.js), or default to relative path
const CORPUS_PATH = process.env.CORPUS_PATH || path.join(__dirname, '..', 'tests', 'corpus', 'gnu-bash', 'tests.tests');

function loadCorpus() {
  const lines = fs.readFileSync(CORPUS_PATH, 'utf8').split('\n');
  const sources = [];
  let i = 0;
  const n = lines.length;
  while (i < n) {
    const line = lines[i];
    if (line.startsWith('=== ')) {
      i++;
      const inputLines = [];
      while (i < n && lines[i] !== '---') {
        inputLines.push(lines[i]);
        i++;
      }
      if (i < n && lines[i] === '---') {
        i++;
      }
      // Skip expected output
      while (i < n && lines[i] !== '---' && !lines[i].startsWith('=== ')) {
        i++;
      }
      if (i < n && lines[i] === '---') {
        i++;
      }
      sources.push(inputLines.join('\n'));
    } else {
      i++;
    }
  }
  return sources;
}

function parseAll(sources) {
  for (const src of sources) {
    parse(src);
  }
}

function benchmark(sources, iterations = 10, warmup = 3) {
  // Warmup
  for (let i = 0; i < warmup; i++) {
    parseAll(sources);
  }

  // Benchmark
  const times = [];
  for (let i = 0; i < iterations; i++) {
    const start = process.hrtime.bigint();
    parseAll(sources);
    const end = process.hrtime.bigint();
    times.push(Number(end - start) / 1e6); // Convert to ms
  }

  return times;
}

function main() {
  const args = process.argv.slice(2);
  const fast = args.includes('--fast');
  const iterations = fast ? 5 : 20;
  const warmup = fast ? 2 : 5;

  const sources = loadCorpus();
  const totalLines = sources.reduce((sum, src) => sum + src.split('\n').length, 0);
  const totalBytes = sources.reduce((sum, src) => sum + src.length, 0);

  const times = benchmark(sources, iterations, warmup);
  const mean = times.reduce((a, b) => a + b, 0) / times.length;
  const variance = times.reduce((sum, t) => sum + (t - mean) ** 2, 0) / times.length;
  const stddev = Math.sqrt(variance);

  console.log(`Corpus: ${sources.length} scripts, ${totalLines} lines, ${totalBytes} bytes`);
  console.log(`gnu_bash_corpus: Mean +- std dev: ${mean.toFixed(1)} ms +- ${stddev.toFixed(1)} ms`);

  // Output JSON for comparison tool
  if (args.includes('--json')) {
    const result = { mean, stddev, times, corpus: { scripts: sources.length, lines: totalLines, bytes: totalBytes } };
    console.log(JSON.stringify(result));
  }
}

main();
