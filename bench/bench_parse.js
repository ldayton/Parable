#!/usr/bin/env node
/**
 * Benchmark Parable JS parser against GNU Bash test corpus.
 * Uses tinybench for statistical rigor matching Python's pyperf.
 *
 * Setup: npm install (from bench/)
 */

const fs = require('fs');
const path = require('path');

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

async function main() {
  const args = process.argv.slice(2);
  const fast = args.includes('--fast');
  const jsonOutput = args.includes('--json');

  const { Bench } = await import('tinybench');

  const parablePath = process.env.PARABLE_PATH || path.join(__dirname, '..', 'src', 'parable.js');
  const { parse } = require(parablePath);

  const sources = loadCorpus();
  const totalLines = sources.reduce((sum, src) => sum + src.split('\n').length, 0);
  const totalBytes = sources.reduce((sum, src) => sum + src.length, 0);

  function parseAll() {
    for (const src of sources) {
      parse(src);
    }
  }

  const bench = new Bench({
    warmup: fast ? 3 : 5,
    iterations: fast ? 10 : 20,
  });

  bench.add('gnu_bash_corpus', parseAll);
  await bench.run();

  const task = bench.tasks[0];
  const latency = task.result.latency;

  // tinybench latency is in milliseconds
  const mean = latency.mean;
  const stddev = latency.sd;

  if (!jsonOutput) {
    console.log(`Corpus: ${sources.length} scripts, ${totalLines} lines, ${totalBytes} bytes`);
    console.log(`gnu_bash_corpus: Mean +- std dev: ${mean.toFixed(1)} ms +- ${stddev.toFixed(1)} ms`);
  }

  if (jsonOutput) {
    const output = { mean, stddev, corpus: { scripts: sources.length, lines: totalLines, bytes: totalBytes } };
    console.log(JSON.stringify(output));
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
