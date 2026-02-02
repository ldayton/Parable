package parable;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.regex.*;

public class RunTests {
    static class TestCase {
        String name;
        String input;
        String expected;
        int lineNum;
        TestCase(String name, String input, String expected, int lineNum) {
            this.name = name;
            this.input = input;
            this.expected = expected;
            this.lineNum = lineNum;
        }
    }

    static class TestResult {
        String relPath;
        int lineNum;
        String name;
        String input;
        String expected;
        String actual;
        String err;
        TestResult(String relPath, int lineNum, String name, String input, String expected, String actual, String err) {
            this.relPath = relPath;
            this.lineNum = lineNum;
            this.name = name;
            this.input = input;
            this.expected = expected;
            this.actual = actual;
            this.err = err;
        }
    }

    static List<Path> findTestFiles(Path directory) throws IOException {
        List<Path> result = new ArrayList<>();
        Files.walk(directory)
            .filter(p -> !Files.isDirectory(p) && p.toString().endsWith(".tests"))
            .sorted()
            .forEach(result::add);
        return result;
    }

    static List<TestCase> parseTestFile(Path filepath) throws IOException {
        List<String> lines = Files.readAllLines(filepath);
        List<TestCase> tests = new ArrayList<>();
        int i = 0;
        int n = lines.size();
        while (i < n) {
            String line = lines.get(i);
            if (line.startsWith("#") || line.trim().isEmpty()) {
                i++;
                continue;
            }
            if (line.startsWith("=== ")) {
                String name = line.substring(4).trim();
                int startLine = i + 1;
                i++;
                List<String> inputLines = new ArrayList<>();
                while (i < n && !lines.get(i).equals("---")) {
                    inputLines.add(lines.get(i));
                    i++;
                }
                if (i < n && lines.get(i).equals("---")) {
                    i++;
                }
                List<String> expectedLines = new ArrayList<>();
                while (i < n && !lines.get(i).equals("---") && !lines.get(i).startsWith("=== ")) {
                    expectedLines.add(lines.get(i));
                    i++;
                }
                if (i < n && lines.get(i).equals("---")) {
                    i++;
                }
                while (!expectedLines.isEmpty() && expectedLines.get(expectedLines.size() - 1).trim().isEmpty()) {
                    expectedLines.remove(expectedLines.size() - 1);
                }
                String testInput = String.join("\n", inputLines);
                String testExpected = String.join("\n", expectedLines);
                tests.add(new TestCase(name, testInput, testExpected, startLine));
            } else {
                i++;
            }
        }
        return tests;
    }

    static final Pattern WHITESPACE_RE = Pattern.compile("[\\s\\v]+");

    static String normalize(String s) {
        return WHITESPACE_RE.matcher(s).replaceAll(" ").trim();
    }

    static ExecutorService executor = Executors.newSingleThreadExecutor();

    static String[] runTest(String testInput, String testExpected) {
        final boolean extglob;
        final String finalInput;
        if (testInput.startsWith("# @extglob\n")) {
            extglob = true;
            finalInput = testInput.substring("# @extglob\n".length());
        } else {
            extglob = false;
            finalInput = testInput;
        }
        Future<String[]> future = executor.submit(() -> {
            try {
                List<Node> nodes = ParableFunctions.parse(finalInput, extglob);
                List<String> parts = new ArrayList<>();
                for (Node n : nodes) {
                    parts.add(n.toSexp());
                }
                String actual = String.join(" ", parts);
                String expectedNorm = normalize(testExpected);
                if (expectedNorm.equals("<error>")) {
                    return new String[]{"false", actual, "Expected parse error but got successful parse"};
                }
                String actualNorm = normalize(actual);
                if (expectedNorm.equals(actualNorm)) {
                    return new String[]{"true", actual, ""};
                }
                return new String[]{"false", actual, ""};
            } catch (RuntimeException e) {
                if (normalize(testExpected).equals("<error>")) {
                    return new String[]{"true", "<error>", ""};
                }
                StringWriter sw = new StringWriter();
                e.printStackTrace(new PrintWriter(sw));
                return new String[]{"false", "<exception>", e.getMessage() + "\n" + sw.toString()};
            }
        });
        try {
            return future.get(10, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            future.cancel(true);
            return new String[]{"false", "<timeout>", "Test timed out after 10 seconds"};
        } catch (Exception e) {
            return new String[]{"false", "<exception>", e.getMessage()};
        }
    }

    static void printUsage() {
        System.out.println("Usage: RunTests [options] [test_dir]");
        System.out.println("Options:");
        System.out.println("  -v, --verbose       Show PASS/FAIL for each test");
        System.out.println("  -f, --filter PAT    Only run tests matching PAT");
        System.out.println("  --max-failures N    Show at most N failures (0=unlimited, default=20)");
        System.out.println("  -h, --help          Show this help message");
    }

    public static void main(String[] args) throws IOException {
        boolean verbose = false;
        String filterPattern = null;
        String testDir = null;
        int maxFailures = 20;

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("-h") || args[i].equals("--help")) {
                printUsage();
                return;
            } else if (args[i].equals("-v") || args[i].equals("--verbose")) {
                verbose = true;
            } else if ((args[i].equals("-f") || args[i].equals("--filter")) && i + 1 < args.length) {
                filterPattern = args[++i];
            } else if (args[i].equals("--max-failures") && i + 1 < args.length) {
                maxFailures = Integer.parseInt(args[++i]);
            } else if (!args[i].startsWith("-")) {
                testDir = args[i];
            }
        }

        if (testDir == null) {
            testDir = "tests";
            if (!Files.exists(Path.of(testDir))) {
                testDir = "../tests";
            }
        }

        Path testPath = Path.of(testDir);
        if (!Files.exists(testPath)) {
            System.err.println("Could not find tests directory");
            System.exit(1);
        }

        long startTime = System.currentTimeMillis();
        int totalPassed = 0;
        int totalFailed = 0;
        List<TestResult> failedTests = new ArrayList<>();

        List<Path> testFiles = findTestFiles(testPath);
        Path baseDir = testPath.toAbsolutePath().getParent();

        for (Path fpath : testFiles) {
            List<TestCase> tests = parseTestFile(fpath);
            Path absFpath = fpath.toAbsolutePath();
            String relPath = baseDir.relativize(absFpath).toString();

            for (TestCase tc : tests) {
                if (filterPattern != null && !tc.name.contains(filterPattern) && !relPath.contains(filterPattern)) {
                    continue;
                }
                String effectiveExpected = tc.expected;
                if (normalize(tc.expected).equals("<infinite>")) {
                    effectiveExpected = "<error>";
                }
                String[] result = runTest(tc.input, effectiveExpected);
                boolean passed = result[0].equals("true");
                String actual = result[1];
                String errMsg = result[2];

                if (passed) {
                    totalPassed++;
                    if (verbose) {
                        System.out.printf("PASS %s:%d %s%n", relPath, tc.lineNum, tc.name);
                    }
                } else {
                    totalFailed++;
                    failedTests.add(new TestResult(relPath, tc.lineNum, tc.name, tc.input, tc.expected, actual, errMsg));
                    if (verbose) {
                        System.out.printf("FAIL %s:%d %s%n", relPath, tc.lineNum, tc.name);
                    }
                }
            }
        }

        double elapsed = (System.currentTimeMillis() - startTime) / 1000.0;

        if (totalFailed > 0) {
            System.out.println("============================================================");
            System.out.println("FAILURES");
            System.out.println("============================================================");
            int showCount = maxFailures == 0 ? failedTests.size() : Math.min(failedTests.size(), maxFailures);
            for (int i = 0; i < showCount; i++) {
                TestResult f = failedTests.get(i);
                System.out.printf("%n%s:%d %s%n", f.relPath, f.lineNum, f.name);
                System.out.printf("  Input:    %s%n", f.input.replace("\n", "\\n"));
                System.out.printf("  Expected: %s%n", f.expected);
                System.out.printf("  Actual:   %s%n", f.actual);
                if (!f.err.isEmpty()) {
                    System.out.printf("  Error:    %s%n", f.err);
                }
            }
            if (maxFailures > 0 && totalFailed > maxFailures) {
                System.out.printf("%n... and %d more failures%n", totalFailed - maxFailures);
            }
        }

        System.out.printf("java: %d passed, %d failed in %.2fs%n", totalPassed, totalFailed, elapsed);
        executor.shutdownNow();
        if (totalFailed > 0) {
            System.exit(1);
        }
    }
}
