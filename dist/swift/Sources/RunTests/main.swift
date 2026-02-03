import Foundation
import Parable

struct TestCase {
    let name: String
    let input: String
    let expected: String
    let lineNum: Int
}

struct TestResult {
    let relPath: String
    let lineNum: Int
    let name: String
    let input: String
    let expected: String
    let actual: String
    let err: String
}

func findTestFiles(directory: String) -> [String] {
    let fm = FileManager.default
    var files: [String] = []
    if let enumerator = fm.enumerator(atPath: directory) {
        while let element = enumerator.nextObject() as? String {
            if element.hasSuffix(".tests") {
                files.append("\(directory)/\(element)")
            }
        }
    }
    return files.sorted()
}

func parseTestFile(filepath: String) -> [TestCase] {
    guard let content = try? String(contentsOfFile: filepath, encoding: .utf8) else {
        return []
    }
    let lines = content.components(separatedBy: "\n")
    var tests: [TestCase] = []
    var i = 0
    let n = lines.count
    while i < n {
        let line = lines[i]
        if line.hasPrefix("#") || line.trimmingCharacters(in: .whitespaces).isEmpty {
            i += 1
            continue
        }
        if line.hasPrefix("=== ") {
            let name = String(line.dropFirst(4)).trimmingCharacters(in: .whitespaces)
            let startLine = i + 1
            i += 1
            var inputLines: [String] = []
            while i < n && lines[i] != "---" {
                inputLines.append(lines[i])
                i += 1
            }
            if i < n && lines[i] == "---" { i += 1 }
            var expectedLines: [String] = []
            while i < n && lines[i] != "---" && !lines[i].hasPrefix("=== ") {
                expectedLines.append(lines[i])
                i += 1
            }
            if i < n && lines[i] == "---" { i += 1 }
            while !expectedLines.isEmpty && expectedLines.last!.trimmingCharacters(in: .whitespaces).isEmpty {
                expectedLines.removeLast()
            }
            tests.append(TestCase(name: name, input: inputLines.joined(separator: "\n"), expected: expectedLines.joined(separator: "\n"), lineNum: startLine))
        } else {
            i += 1
        }
    }
    return tests
}

func normalize(_ s: String) -> String {
    let pattern = try! NSRegularExpression(pattern: "[\\s\\v]+", options: [])
    let range = NSRange(s.startIndex..., in: s)
    return pattern.stringByReplacingMatches(in: s, options: [], range: range, withTemplate: " ").trimmingCharacters(in: .whitespaces)
}

func runTestInner(input: String, extglob: Bool, testExpected: String) -> (passed: Bool, actual: String, errMsg: String) {
    do {
        let nodes = try parse(input, extglob: extglob)
        let actual = nodes.map { $0.toSexp() }.joined(separator: " ")
        let expectedNorm = normalize(testExpected)
        if expectedNorm == "<error>" {
            return (false, actual, "Expected parse error but got successful parse")
        }
        let actualNorm = normalize(actual)
        if expectedNorm == actualNorm {
            return (true, actual, "")
        }
        return (false, actual, "")
    } catch let e as ParseError {
        if normalize(testExpected) == "<error>" {
            return (true, "<error>", "")
        }
        return (false, "<parse error>", e.localizedDescription)
    } catch {
        if normalize(testExpected) == "<error>" {
            return (true, "<error>", "")
        }
        return (false, "<exception>", error.localizedDescription)
    }
}

func runTest(testInput: String, testExpected: String) -> (passed: Bool, actual: String, errMsg: String) {
    var extglob = false
    var input = testInput
    if input.hasPrefix("# @extglob\n") {
        extglob = true
        input = String(input.dropFirst("# @extglob\n".count))
    }
    var result: (passed: Bool, actual: String, errMsg: String)? = nil
    let semaphore = DispatchSemaphore(value: 0)
    let queue = DispatchQueue.global(qos: .userInitiated)
    queue.async {
        result = runTestInner(input: input, extglob: extglob, testExpected: testExpected)
        semaphore.signal()
    }
    let timeout = semaphore.wait(timeout: .now() + 10)
    if timeout == .timedOut {
        return (false, "<timeout>", "Test timed out after 10 seconds")
    }
    return result ?? (false, "<exception>", "Unknown error")
}

func main() {
    let args = CommandLine.arguments
    var verbose = false
    var filterPattern = ""
    var maxFailures = 20
    var testDir: String? = nil
    var i = 1
    while i < args.count {
        switch args[i] {
        case "-v", "--verbose":
            verbose = true
        case "-f", "--filter":
            if i + 1 < args.count {
                i += 1
                filterPattern = args[i]
            }
        case "--max-failures":
            if i + 1 < args.count {
                i += 1
                maxFailures = Int(args[i]) ?? 20
            }
        case "-h", "--help":
            print("Usage: RunTests [options] [test_dir]")
            print("Options:")
            print("  -v, --verbose       Show PASS/FAIL for each test")
            print("  -f, --filter PAT    Only run tests matching PAT")
            print("  --max-failures N    Show at most N failures (0=unlimited)")
            print("  -h, --help          Show this help message")
            return
        default:
            if !args[i].hasPrefix("-") {
                testDir = args[i]
            }
        }
        i += 1
    }
    let fm = FileManager.default
    let dir = testDir ?? (fm.fileExists(atPath: "tests") ? "tests" : "../tests")
    guard fm.fileExists(atPath: dir) else {
        fputs("Could not find tests directory\n", stderr)
        exit(1)
    }
    let startTime = Date()
    var totalPassed = 0
    var totalFailed = 0
    var failedTests: [TestResult] = []
    let testFiles = findTestFiles(directory: dir)
    let baseDir = URL(fileURLWithPath: dir).deletingLastPathComponent().standardizedFileURL.path
    for fpath in testFiles {
        let tests = parseTestFile(filepath: fpath)
        let absPath = URL(fileURLWithPath: fpath).standardizedFileURL.path
        let relPath = absPath.hasPrefix(baseDir) ? String(absPath.dropFirst(baseDir.count + 1)) : absPath
        for tc in tests {
            if !filterPattern.isEmpty && !tc.name.contains(filterPattern) && !relPath.contains(filterPattern) {
                continue
            }
            let effectiveExpected = normalize(tc.expected) == "<infinite>" ? "<error>" : tc.expected
            let (passed, actual, errMsg) = runTest(testInput: tc.input, testExpected: effectiveExpected)
            if passed {
                totalPassed += 1
                if verbose { print("PASS \(relPath):\(tc.lineNum) \(tc.name)") }
            } else {
                totalFailed += 1
                failedTests.append(TestResult(relPath: relPath, lineNum: tc.lineNum, name: tc.name, input: tc.input, expected: tc.expected, actual: actual, err: errMsg))
                if verbose { print("FAIL \(relPath):\(tc.lineNum) \(tc.name)") }
            }
        }
    }
    let elapsed = Date().timeIntervalSince(startTime)
    if totalFailed > 0 {
        print(String(repeating: "=", count: 60))
        print("FAILURES")
        print(String(repeating: "=", count: 60))
        let showCount = maxFailures > 0 && failedTests.count > maxFailures ? maxFailures : failedTests.count
        for f in failedTests.prefix(showCount) {
            print("\n\(f.relPath):\(f.lineNum) \(f.name)")
            print("  Input:    \"\(f.input)\"")
            print("  Expected: \(f.expected)")
            print("  Actual:   \(f.actual)")
            if !f.err.isEmpty { print("  Error:    \(f.err)") }
        }
        if maxFailures > 0 && totalFailed > maxFailures {
            print("\n... and \(totalFailed - maxFailures) more failures")
        }
    }
    print("swift: \(totalPassed) passed, \(totalFailed) failed in \(String(format: "%.2f", elapsed))s")
    if totalFailed > 0 { exit(1) }
}

main()
