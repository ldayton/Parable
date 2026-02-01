// Test runner for the C# parser.
// Mirrors the Java test runner in dist/java/RunTests.java
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

class TestCase
{
    public string Name { get; set; }
    public string Input { get; set; }
    public string Expected { get; set; }
    public int LineNum { get; set; }

    public TestCase(string name, string input, string expected, int lineNum)
    {
        Name = name;
        Input = input;
        Expected = expected;
        LineNum = lineNum;
    }
}

class TestResult
{
    public string RelPath { get; set; }
    public int LineNum { get; set; }
    public string Name { get; set; }
    public string Input { get; set; }
    public string Expected { get; set; }
    public string Actual { get; set; }
    public string Err { get; set; }

    public TestResult(string relPath, int lineNum, string name, string input, string expected, string actual, string err)
    {
        RelPath = relPath;
        LineNum = lineNum;
        Name = name;
        Input = input;
        Expected = expected;
        Actual = actual;
        Err = err;
    }
}

class RunTests
{
    static List<string> FindTestFiles(string directory)
    {
        return Directory.GetFiles(directory, "*.tests", SearchOption.AllDirectories)
            .OrderBy(f => f)
            .ToList();
    }

    static List<TestCase> ParseTestFile(string filepath)
    {
        var lines = File.ReadAllLines(filepath).ToList();
        var tests = new List<TestCase>();
        int i = 0;
        int n = lines.Count;

        while (i < n)
        {
            string line = lines[i];
            if (line.StartsWith("#") || string.IsNullOrWhiteSpace(line))
            {
                i++;
                continue;
            }
            if (line.StartsWith("=== "))
            {
                string name = line.Substring(4).Trim();
                int startLine = i + 1;
                i++;
                var inputLines = new List<string>();
                while (i < n && lines[i] != "---")
                {
                    inputLines.Add(lines[i]);
                    i++;
                }
                if (i < n && lines[i] == "---")
                {
                    i++;
                }
                var expectedLines = new List<string>();
                while (i < n && lines[i] != "---" && !lines[i].StartsWith("=== "))
                {
                    expectedLines.Add(lines[i]);
                    i++;
                }
                if (i < n && lines[i] == "---")
                {
                    i++;
                }
                // Trim trailing empty lines from expected
                while (expectedLines.Count > 0 && string.IsNullOrWhiteSpace(expectedLines[expectedLines.Count - 1]))
                {
                    expectedLines.RemoveAt(expectedLines.Count - 1);
                }
                string testInput = string.Join("\n", inputLines);
                string testExpected = string.Join("\n", expectedLines);
                tests.Add(new TestCase(name, testInput, testExpected, startLine));
            }
            else
            {
                i++;
            }
        }
        return tests;
    }

    static readonly Regex WhitespaceRe = new Regex(@"[\s\v]+");

    static string Normalize(string s)
    {
        return WhitespaceRe.Replace(s, " ").Trim();
    }

    static (bool passed, string actual, string errMsg) RunTest(string testInput, string testExpected)
    {
        bool extglob = false;
        if (testInput.StartsWith("# @extglob\n"))
        {
            extglob = true;
            testInput = testInput.Substring("# @extglob\n".Length);
        }
        var task = System.Threading.Tasks.Task.Run(() => RunTestInner(testInput, testExpected, extglob));
        if (task.Wait(TimeSpan.FromSeconds(5)))
        {
            return task.Result;
        }
        return (false, "<timeout>", "Test timed out after 5 seconds");
    }

    static (bool passed, string actual, string errMsg) RunTestInner(string testInput, string testExpected, bool extglob)
    {
        try
        {
            var nodes = ParableFunctions.Parse(testInput, extglob);
            var parts = new List<string>();
            foreach (var n in nodes)
            {
                parts.Add(n.ToSexp());
            }
            string actual = string.Join(" ", parts);
            string expectedNorm = Normalize(testExpected);
            // If we expected an error but got a successful parse, that's a failure
            if (expectedNorm == "<error>")
            {
                return (false, actual, "Expected parse error but got successful parse");
            }
            string actualNorm = Normalize(actual);
            if (expectedNorm == actualNorm)
            {
                return (true, actual, "");
            }
            return (false, actual, "");
        }
        catch (Exception e)
        {
            // Parse errors are signaled via exceptions
            if (Normalize(testExpected) == "<error>")
            {
                return (true, "<error>", "");
            }
            return (false, "<exception>", e.Message + "\n" + e.StackTrace);
        }
    }

    static void Main(string[] args)
    {
        bool verbose = false;
        string filterPattern = null;
        string testDir = null;

        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "-v" || args[i] == "--verbose")
            {
                verbose = true;
            }
            else if (args[i] == "-f" && i + 1 < args.Length)
            {
                filterPattern = args[++i];
            }
            else if (!args[i].StartsWith("-"))
            {
                testDir = args[i];
            }
        }

        if (testDir == null)
        {
            testDir = "tests";
            if (!Directory.Exists(testDir))
            {
                testDir = "../tests";
            }
        }

        if (!Directory.Exists(testDir))
        {
            Console.Error.WriteLine("Could not find tests directory");
            Environment.Exit(1);
        }

        var startTime = DateTime.Now;
        int totalPassed = 0;
        int totalFailed = 0;
        var failedTests = new List<TestResult>();

        var testFiles = FindTestFiles(testDir);
        string baseDir = Path.GetDirectoryName(Path.GetFullPath(testDir));

        foreach (var fpath in testFiles)
        {
            var tests = ParseTestFile(fpath);
            string absFpath = Path.GetFullPath(fpath);
            string relPath = Path.GetRelativePath(baseDir, absFpath);

            foreach (var tc in tests)
            {
                if (filterPattern != null && !tc.Name.Contains(filterPattern) && !relPath.Contains(filterPattern))
                {
                    continue;
                }
                // Treat <infinite> as <error> (bash-oracle hangs, but it's still a syntax error)
                string effectiveExpected = tc.Expected;
                if (Normalize(tc.Expected) == "<infinite>")
                {
                    effectiveExpected = "<error>";
                }
                Console.Write($"{relPath}:{tc.LineNum} {tc.Name} ... ");
                Console.Out.Flush();
                var (passed, actual, errMsg) = RunTest(tc.Input, effectiveExpected);

                if (passed)
                {
                    totalPassed++;
                    Console.WriteLine("ok");
                }
                else
                {
                    totalFailed++;
                    failedTests.Add(new TestResult(relPath, tc.LineNum, tc.Name, tc.Input, tc.Expected, actual, errMsg));
                    Console.WriteLine("FAIL");
                }
            }
        }

        double elapsed = (DateTime.Now - startTime).TotalSeconds;

        if (totalFailed > 0)
        {
            Console.WriteLine("============================================================");
            Console.WriteLine("FAILURES");
            Console.WriteLine("============================================================");
            int showCount = Math.Min(failedTests.Count, 20);
            for (int i = 0; i < showCount; i++)
            {
                var f = failedTests[i];
                Console.WriteLine();
                Console.WriteLine($"{f.RelPath}:{f.LineNum} {f.Name}");
                Console.WriteLine($"  Input:    {f.Input.Replace("\n", "\\n")}");
                Console.WriteLine($"  Expected: {f.Expected}");
                Console.WriteLine($"  Actual:   {f.Actual}");
                if (!string.IsNullOrEmpty(f.Err))
                {
                    Console.WriteLine($"  Error:    {f.Err}");
                }
            }
            if (totalFailed > 20)
            {
                Console.WriteLine($"\n... and {totalFailed - 20} more failures");
            }
        }

        Console.WriteLine($"{totalPassed} passed, {totalFailed} failed in {elapsed:F2}s");
        if (totalFailed > 0)
        {
            Environment.Exit(1);
        }
    }
}
