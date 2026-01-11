// Simple test runner for the Go parser.
// Mirrors the Python test runner in bin/run-tests.py
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"parable/src"
)

func findTestFiles(directory string) []string {
	var result []string
	filepath.Walk(directory, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && strings.HasSuffix(path, ".tests") {
			result = append(result, path)
		}
		return nil
	})
	sort.Strings(result)
	return result
}

type testCase struct {
	name     string
	input    string
	expected string
	lineNum  int
}

func parseTestFile(filepath string) []testCase {
	data, err := os.ReadFile(filepath)
	if err != nil {
		return nil
	}
	lines := strings.Split(string(data), "\n")
	var tests []testCase
	i := 0
	n := len(lines)
	for i < n {
		line := lines[i]
		if strings.HasPrefix(line, "#") || strings.TrimSpace(line) == "" {
			i++
			continue
		}
		if strings.HasPrefix(line, "=== ") {
			name := strings.TrimSpace(line[4:])
			startLine := i + 1
			i++
			var inputLines []string
			for i < n && lines[i] != "---" {
				inputLines = append(inputLines, lines[i])
				i++
			}
			if i < n && lines[i] == "---" {
				i++
			}
			var expectedLines []string
			for i < n && lines[i] != "---" && !strings.HasPrefix(lines[i], "=== ") {
				expectedLines = append(expectedLines, lines[i])
				i++
			}
			if i < n && lines[i] == "---" {
				i++
			}
			for len(expectedLines) > 0 && strings.TrimSpace(expectedLines[len(expectedLines)-1]) == "" {
				expectedLines = expectedLines[:len(expectedLines)-1]
			}
			testInput := strings.Join(inputLines, "\n")
			testExpected := strings.Join(expectedLines, "\n")
			tests = append(tests, testCase{name: name, input: testInput, expected: testExpected, lineNum: startLine})
		} else {
			i++
		}
	}
	return tests
}

func normalize(s string) string {
	return strings.Join(strings.Fields(s), " ")
}

type testResult struct {
	passed bool
	actual string
	err    string
}

func runTest(testInput string) testResult {
	defer func() {
		if r := recover(); r != nil {
			// Will be handled below
		}
	}()

	nodes, err := src.Parse(testInput)
	if err != nil {
		if parseErr, ok := err.(*src.ParseError); ok {
			return testResult{passed: false, actual: "<parse error>", err: parseErr.Error()}
		}
		return testResult{passed: false, actual: "<exception>", err: err.Error()}
	}

	var sexps []string
	for _, node := range nodes {
		sexps = append(sexps, node.ToSexp())
	}
	actual := strings.Join(sexps, " ")
	return testResult{passed: true, actual: actual, err: ""}
}

type failedTest struct {
	relPath  string
	lineNum  int
	name     string
	input    string
	expected string
	actual   string
	err      string
}

func main() {
	verbose := false
	filterPattern := ""
	testDir := ""

	// Parse arguments manually to match Python behavior
	args := os.Args[1:]
	for i := 0; i < len(args); i++ {
		arg := args[i]
		if arg == "-v" || arg == "--verbose" {
			verbose = true
		} else if arg == "-f" || arg == "--filter" {
			i++
			if i < len(args) {
				filterPattern = args[i]
			}
		} else if info, err := os.Stat(arg); err == nil {
			_ = info
			testDir = arg
		}
	}

	// Determine repo root and default test directory
	scriptPath, _ := os.Executable()
	repoRoot := filepath.Dir(filepath.Dir(scriptPath))
	if repoRoot == "" || repoRoot == "." {
		repoRoot, _ = os.Getwd()
	}
	if testDir == "" {
		testDir = filepath.Join(repoRoot, "tests")
	}
	// If testDir doesn't exist, try relative to cwd
	if _, err := os.Stat(testDir); os.IsNotExist(err) {
		cwd, _ := os.Getwd()
		testDir = filepath.Join(cwd, "tests")
		repoRoot = cwd
	}

	startTime := time.Now()
	totalPassed := 0
	totalFailed := 0
	var failedTests []failedTest

	var testFiles []string
	if info, err := os.Stat(testDir); err == nil && !info.IsDir() {
		testFiles = []string{testDir}
	} else {
		testFiles = findTestFiles(testDir)
	}

	for _, fpath := range testFiles {
		tests := parseTestFile(fpath)
		relPath, _ := filepath.Rel(repoRoot, fpath)
		if relPath == "" {
			relPath = fpath
		}

		for _, tc := range tests {
			if filterPattern != "" && !strings.Contains(tc.name, filterPattern) && !strings.Contains(relPath, filterPattern) {
				continue
			}

			result := runTest(tc.input)

			expectedNorm := normalize(tc.expected)
			actualNorm := normalize(result.actual)

			if result.err == "" && expectedNorm == actualNorm {
				totalPassed++
				if verbose {
					fmt.Printf("PASS %s:%d %s\n", relPath, tc.lineNum, tc.name)
				}
			} else {
				totalFailed++
				failedTests = append(failedTests, failedTest{
					relPath:  relPath,
					lineNum:  tc.lineNum,
					name:     tc.name,
					input:    tc.input,
					expected: tc.expected,
					actual:   result.actual,
					err:      result.err,
				})
				if verbose {
					fmt.Printf("FAIL %s:%d %s\n", relPath, tc.lineNum, tc.name)
				}
			}
		}
	}

	elapsed := time.Since(startTime).Seconds()

	fmt.Println("")
	if totalFailed > 0 {
		fmt.Println(strings.Repeat("=", 60))
		fmt.Println("FAILURES")
		fmt.Println(strings.Repeat("=", 60))
		for _, ft := range failedTests {
			fmt.Printf("\n%s:%d %s\n", ft.relPath, ft.lineNum, ft.name)
			inputJSON, _ := json.Marshal(ft.input)
			fmt.Printf("  Input:    %s\n", inputJSON)
			fmt.Printf("  Expected: %s\n", ft.expected)
			fmt.Printf("  Actual:   %s\n", ft.actual)
			if ft.err != "" {
				fmt.Printf("  Error:    %s\n", ft.err)
			}
		}
		fmt.Println("")
	}

	fmt.Printf("%d passed, %d failed in %.2fs\n", totalPassed, totalFailed, elapsed)

	if totalFailed > 0 {
		os.Exit(1)
	}
	os.Exit(0)
}
