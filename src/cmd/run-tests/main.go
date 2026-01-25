// Simple test runner for the Go parser.
// Mirrors the JavaScript test runner in tests/bin/run-js-tests.js
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/parable-parser/parable"
)

type testCase struct {
	name     string
	input    string
	expected string
	lineNum  int
}

type testResult struct {
	relPath  string
	lineNum  int
	name     string
	input    string
	expected string
	actual   string
	err      string
}

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

func parseTestFile(filepath string) []testCase {
	content, err := os.ReadFile(filepath)
	if err != nil {
		return nil
	}
	lines := strings.Split(string(content), "\n")
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
			// Trim trailing empty lines from expected
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

var whitespaceRe = regexp.MustCompile(`\s+`)

func normalize(s string) string {
	return strings.TrimSpace(whitespaceRe.ReplaceAllString(s, " "))
}

type testOutput struct {
	passed bool
	actual string
	errMsg string
}

func runTestInner(testInput, testExpected string, extglob bool) (passed bool, actual string, errMsg string) {
	defer func() {
		if r := recover(); r != nil {
			// Check if it's a ParseError
			if pe, ok := r.(*parable.ParseError); ok {
				if normalize(testExpected) == "<error>" {
					passed = true
					actual = "<error>"
					errMsg = ""
					return
				}
				passed = false
				actual = "<parse error>"
				errMsg = pe.Error()
				return
			}
			// Other panic
			passed = false
			actual = "<exception>"
			errMsg = fmt.Sprintf("%v", r)
		}
	}()
	nodes := parable.Parse(testInput, extglob)
	var parts []string
	for _, n := range nodes {
		parts = append(parts, n.ToSexp())
	}
	actual = strings.Join(parts, " ")
	expectedNorm := normalize(testExpected)
	// If we expected an error but got a successful parse, that's a failure
	if expectedNorm == "<error>" {
		return false, actual, "Expected parse error but got successful parse"
	}
	actualNorm := normalize(actual)
	if expectedNorm == actualNorm {
		return true, actual, ""
	}
	return false, actual, ""
}

func runTest(testInput, testExpected string) (passed bool, actual string, errMsg string) {
	// Check for @extglob directive
	extglob := false
	if strings.HasPrefix(testInput, "# @extglob\n") {
		extglob = true
		testInput = testInput[len("# @extglob\n"):]
	}
	resultCh := make(chan testOutput, 1)
	go func() {
		p, a, e := runTestInner(testInput, testExpected, extglob)
		resultCh <- testOutput{p, a, e}
	}()
	select {
	case result := <-resultCh:
		return result.passed, result.actual, result.errMsg
	case <-time.After(5 * time.Second):
		return false, "<timeout>", "Test timed out after 5s"
	}
}

func main() {
	verbose := flag.Bool("v", false, "Verbose output")
	flag.Bool("verbose", false, "Verbose output")
	filterPattern := flag.String("f", "", "Filter pattern for test names")
	flag.Parse()
	// Also check for --verbose
	for _, arg := range os.Args[1:] {
		if arg == "--verbose" {
			*verbose = true
		}
	}
	// Find tests directory - go up from binary location
	testDir := "tests"
	if _, err := os.Stat(testDir); os.IsNotExist(err) {
		// Try from src/ directory
		testDir = "../tests"
		if _, err := os.Stat(testDir); os.IsNotExist(err) {
			fmt.Fprintln(os.Stderr, "Could not find tests directory")
			os.Exit(1)
		}
	}
	startTime := time.Now()
	var totalPassed, totalFailed int
	var failedTests []testResult
	testFiles := findTestFiles(testDir)
	baseDir, _ := filepath.Abs(filepath.Join(testDir, ".."))
	for _, fpath := range testFiles {
		tests := parseTestFile(fpath)
		relPath, _ := filepath.Rel(baseDir, fpath)
		for _, tc := range tests {
			if *filterPattern != "" && !strings.Contains(tc.name, *filterPattern) && !strings.Contains(relPath, *filterPattern) {
				continue
			}
			// Treat <infinite> as <error> (bash-oracle hangs, but it's still a syntax error)
			effectiveExpected := tc.expected
			if normalize(tc.expected) == "<infinite>" {
				effectiveExpected = "<error>"
			}
			passed, actual, errMsg := runTest(tc.input, effectiveExpected)
			if passed {
				totalPassed++
				if *verbose {
					fmt.Printf("PASS %s:%d %s\n", relPath, tc.lineNum, tc.name)
				}
			} else {
				totalFailed++
				failedTests = append(failedTests, testResult{
					relPath:  relPath,
					lineNum:  tc.lineNum,
					name:     tc.name,
					input:    tc.input,
					expected: tc.expected,
					actual:   actual,
					err:      errMsg,
				})
				if *verbose {
					fmt.Printf("FAIL %s:%d %s\n", relPath, tc.lineNum, tc.name)
				}
			}
		}
	}
	elapsed := time.Since(startTime).Seconds()
	if totalFailed > 0 && totalFailed <= 50 {
		fmt.Println(strings.Repeat("=", 60))
		fmt.Println("FAILURES")
		fmt.Println(strings.Repeat("=", 60))
		for _, f := range failedTests {
			fmt.Printf("\n%s:%d %s\n", f.relPath, f.lineNum, f.name)
			fmt.Printf("  Input:    %q\n", f.input)
			fmt.Printf("  Expected: %s\n", f.expected)
			fmt.Printf("  Actual:   %s\n", f.actual)
			if f.err != "" {
				fmt.Printf("  Error:    %s\n", f.err)
			}
		}
	} else if totalFailed > 50 {
		fmt.Printf("%d failures (too many to show)\n", totalFailed)
	}
	fmt.Printf("%d passed, %d failed in %.2fs\n", totalPassed, totalFailed, elapsed)
	if totalFailed > 0 {
		os.Exit(1)
	}
}
