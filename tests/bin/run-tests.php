#!/usr/bin/env php
<?php
/**
 * Simple test runner for PHP backend. Mirrors run-tests.py.
 */

declare(strict_types=1);

require_once __DIR__ . '/../../dist/php/parable.php';

function findTestFiles(string $directory): array {
    $result = [];
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($directory)
    );
    foreach ($iterator as $file) {
        if ($file->isFile() && str_ends_with($file->getFilename(), '.tests')) {
            $result[] = $file->getPathname();
        }
    }
    sort($result);
    return $result;
}

function parseTestFile(string $filepath): array {
    $tests = [];
    $lines = explode("\n", file_get_contents($filepath));
    $i = 0;
    $n = count($lines);
    while ($i < $n) {
        $line = $lines[$i];
        if (str_starts_with($line, '#') || trim($line) === '') {
            $i++;
            continue;
        }
        if (str_starts_with($line, '=== ')) {
            $name = trim(substr($line, 4));
            $startLine = $i + 1;
            $i++;
            $inputLines = [];
            while ($i < $n && $lines[$i] !== '---') {
                $inputLines[] = $lines[$i];
                $i++;
            }
            if ($i < $n && $lines[$i] === '---') {
                $i++;
            }
            $expectedLines = [];
            while ($i < $n && $lines[$i] !== '---' && !str_starts_with($lines[$i], '=== ')) {
                $expectedLines[] = $lines[$i];
                $i++;
            }
            if ($i < $n && $lines[$i] === '---') {
                $i++;
            }
            while (count($expectedLines) > 0 && trim($expectedLines[count($expectedLines) - 1]) === '') {
                array_pop($expectedLines);
            }
            $testInput = implode("\n", $inputLines);
            $testExpected = implode("\n", $expectedLines);
            $tests[] = [$name, $testInput, $testExpected, $startLine];
        } else {
            $i++;
        }
    }
    return $tests;
}

function normalize(string $s): string {
    return implode(' ', preg_split('/\s+/', trim($s)));
}

function runTest(string $testInput, string $testExpected): array {
    $extglob = false;
    if (str_starts_with($testInput, "# @extglob\n")) {
        $extglob = true;
        $testInput = substr($testInput, strlen("# @extglob\n"));
    }
    try {
        $nodes = parse($testInput, $extglob);
        $parts = [];
        foreach ($nodes as $node) {
            $parts[] = $node->toSexp();
        }
        $actual = implode(' ', $parts);
    } catch (Parseerror_ $e) {
        if (normalize($testExpected) === '<error>') {
            return [true, '<error>', null];
        }
        return [false, '<parse error>', $e->getMessage()];
    } catch (Exception $e) {
        return [false, '<exception>', $e->getMessage()];
    }
    if (normalize($testExpected) === '<error>') {
        return [false, $actual, 'Expected parse error but got successful parse'];
    }
    $expectedNorm = normalize($testExpected);
    $actualNorm = normalize($actual);
    if ($expectedNorm === $actualNorm) {
        return [true, $actual, null];
    }
    return [false, $actual, null];
}

function main(): int {
    global $argv;
    $scriptDir = dirname(__FILE__);
    $testDir = dirname($scriptDir);
    $repoRoot = dirname($testDir);
    $verbose = false;
    $filterPattern = null;
    $i = 1;
    while ($i < count($argv)) {
        $arg = $argv[$i];
        if ($arg === '-v' || $arg === '--verbose') {
            $verbose = true;
        } elseif ($arg === '-f' || $arg === '--filter') {
            $i++;
            if ($i < count($argv)) {
                $filterPattern = $argv[$i];
            }
        } elseif (file_exists($arg)) {
            $testDir = $arg;
        }
        $i++;
    }
    $startTime = microtime(true);
    $totalPassed = 0;
    $totalFailed = 0;
    $failedTests = [];
    if (is_file($testDir)) {
        $testFiles = [$testDir];
    } else {
        $testFiles = findTestFiles($testDir);
    }
    foreach ($testFiles as $filepath) {
        $tests = parseTestFile($filepath);
        $relPath = str_replace($repoRoot . '/', '', $filepath);
        foreach ($tests as [$name, $testInput, $testExpected, $lineNum]) {
            if ($filterPattern !== null) {
                if (strpos($name, $filterPattern) === false && strpos($relPath, $filterPattern) === false) {
                    continue;
                }
            }
            $effectiveExpected = $testExpected;
            if (normalize($testExpected) === '<infinite>') {
                $effectiveExpected = '<error>';
            }
            [$passed, $actual, $errorMsg] = runTest($testInput, $effectiveExpected);
            if ($passed) {
                $totalPassed++;
                if ($verbose) {
                    echo "PASS {$relPath}:{$lineNum} {$name}\n";
                }
            } else {
                $totalFailed++;
                $failedTests[] = [$relPath, $lineNum, $name, $testInput, $testExpected, $actual, $errorMsg];
                if ($verbose) {
                    echo "FAIL {$relPath}:{$lineNum} {$name}\n";
                }
            }
        }
    }
    $elapsed = microtime(true) - $startTime;
    echo "\n";
    if ($totalFailed > 0) {
        echo str_repeat('=', 60) . "\n";
        echo "FAILURES\n";
        echo str_repeat('=', 60) . "\n";
        foreach ($failedTests as [$relPath, $lineNum, $name, $inp, $expected, $actual, $errorMsg]) {
            echo "\n{$relPath}:{$lineNum} {$name}\n";
            echo "  Input:    " . var_export($inp, true) . "\n";
            echo "  Expected: {$expected}\n";
            echo "  Actual:   {$actual}\n";
            if ($errorMsg !== null) {
                echo "  Error:    {$errorMsg}\n";
            }
        }
        echo "\n";
    }
    printf("%d passed, %d failed in %.2fs\n", $totalPassed, $totalFailed, $elapsed);
    return $totalFailed > 0 ? 1 : 0;
}

exit(main());
