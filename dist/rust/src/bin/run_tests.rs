use parable::{parse, ParseError};
use std::env;
use std::fs;
use std::path::Path;
use std::process;
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

struct TestCase {
    name: String,
    input: String,
    expected: String,
    line_num: usize,
}

struct TestResult {
    rel_path: String,
    line_num: usize,
    name: String,
    input: String,
    expected: String,
    actual: String,
    err: String,
}

fn find_test_files(directory: &str) -> Vec<String> {
    let mut files = Vec::new();
    fn walk(dir: &Path, files: &mut Vec<String>) {
        if let Ok(entries) = fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    walk(&path, files);
                } else if path.extension().map_or(false, |e| e == "tests") {
                    files.push(path.to_string_lossy().to_string());
                }
            }
        }
    }
    walk(Path::new(directory), &mut files);
    files.sort();
    files
}

fn parse_test_file(filepath: &str) -> Vec<TestCase> {
    let content = fs::read_to_string(filepath).unwrap_or_default();
    let lines: Vec<&str> = content.split('\n').collect();
    let mut tests = Vec::new();
    let mut i = 0;
    let n = lines.len();
    while i < n {
        let line = lines[i];
        if line.starts_with('#') || line.trim().is_empty() {
            i += 1;
            continue;
        }
        if line.starts_with("=== ") {
            let name = line[4..].trim().to_string();
            let start_line = i + 1;
            i += 1;
            let mut input_lines = Vec::new();
            while i < n && lines[i] != "---" {
                input_lines.push(lines[i]);
                i += 1;
            }
            if i < n && lines[i] == "---" {
                i += 1;
            }
            let mut expected_lines = Vec::new();
            while i < n && lines[i] != "---" && !lines[i].starts_with("=== ") {
                expected_lines.push(lines[i]);
                i += 1;
            }
            if i < n && lines[i] == "---" {
                i += 1;
            }
            while !expected_lines.is_empty() && expected_lines.last().unwrap().trim().is_empty() {
                expected_lines.pop();
            }
            tests.push(TestCase {
                name,
                input: input_lines.join("\n"),
                expected: expected_lines.join("\n"),
                line_num: start_line,
            });
        } else {
            i += 1;
        }
    }
    tests
}

fn normalize(s: &str) -> String {
    let re = regex::Regex::new(r"[\s\v]+").unwrap();
    re.replace_all(s, " ").trim().to_string()
}

fn run_test_inner(input: &str, extglob: bool, test_expected: &str) -> (bool, String, String) {
    match std::panic::catch_unwind(|| parse(input, extglob)) {
        Ok(Ok(nodes)) => {
            let actual: String = nodes.iter().map(|n| n.to_sexp()).collect::<Vec<_>>().join(" ");
            let expected_norm = normalize(test_expected);
            if expected_norm == "<error>" {
                return (false, actual, "Expected parse error but got successful parse".to_string());
            }
            let actual_norm = normalize(&actual);
            if expected_norm == actual_norm {
                (true, actual, String::new())
            } else {
                (false, actual, String::new())
            }
        }
        Ok(Err(e)) => {
            if normalize(test_expected) == "<error>" {
                (true, "<error>".to_string(), String::new())
            } else {
                (false, "<parse error>".to_string(), e.to_string())
            }
        }
        Err(e) => {
            if normalize(test_expected) == "<error>" {
                (true, "<error>".to_string(), String::new())
            } else {
                let msg = if let Some(s) = e.downcast_ref::<&str>() {
                    s.to_string()
                } else if let Some(s) = e.downcast_ref::<String>() {
                    s.clone()
                } else {
                    "Unknown panic".to_string()
                };
                (false, "<exception>".to_string(), msg)
            }
        }
    }
}

fn run_test(test_input: &str, test_expected: &str) -> (bool, String, String) {
    let mut extglob = false;
    let mut input = test_input;
    if input.starts_with("# @extglob\n") {
        extglob = true;
        input = &input["# @extglob\n".len()..];
    }
    let input = input.to_string();
    let expected = test_expected.to_string();
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let result = run_test_inner(&input, extglob, &expected);
        let _ = tx.send(result);
    });
    match rx.recv_timeout(Duration::from_secs(10)) {
        Ok(result) => result,
        Err(_) => (false, "<timeout>".to_string(), "Test timed out after 10 seconds".to_string()),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut verbose = false;
    let mut filter_pattern = String::new();
    let mut max_failures = 20;
    let mut test_dir = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "-v" | "--verbose" => verbose = true,
            "-f" | "--filter" => {
                if i + 1 < args.len() {
                    i += 1;
                    filter_pattern = args[i].clone();
                }
            }
            "--max-failures" => {
                if i + 1 < args.len() {
                    i += 1;
                    max_failures = args[i].parse().unwrap_or(20);
                }
            }
            "-h" | "--help" => {
                println!("Usage: run_tests [options] [test_dir]");
                println!("Options:");
                println!("  -v, --verbose       Show PASS/FAIL for each test");
                println!("  -f, --filter PAT    Only run tests matching PAT");
                println!("  --max-failures N    Show at most N failures (0=unlimited)");
                println!("  -h, --help          Show this help message");
                return;
            }
            s if !s.starts_with('-') => test_dir = Some(s.to_string()),
            _ => {}
        }
        i += 1;
    }
    let test_dir = test_dir.unwrap_or_else(|| {
        if Path::new("tests").exists() {
            "tests".to_string()
        } else {
            "../tests".to_string()
        }
    });
    if !Path::new(&test_dir).exists() {
        eprintln!("Could not find tests directory");
        process::exit(1);
    }
    let start_time = Instant::now();
    let mut total_passed = 0;
    let mut total_failed = 0;
    let mut failed_tests = Vec::new();
    let test_files = find_test_files(&test_dir);
    let base_dir = fs::canonicalize(format!("{}/..", test_dir)).unwrap();
    for fpath in test_files {
        let tests = parse_test_file(&fpath);
        let abs_path = fs::canonicalize(&fpath).unwrap();
        let rel_path = abs_path.strip_prefix(&base_dir).unwrap().to_string_lossy().to_string();
        for tc in tests {
            if !filter_pattern.is_empty() && !tc.name.contains(&filter_pattern) && !rel_path.contains(&filter_pattern) {
                continue;
            }
            let effective_expected = if normalize(&tc.expected) == "<infinite>" {
                "<error>".to_string()
            } else {
                tc.expected.clone()
            };
            let (passed, actual, err_msg) = run_test(&tc.input, &effective_expected);
            if passed {
                total_passed += 1;
                if verbose {
                    println!("PASS {}:{} {}", rel_path, tc.line_num, tc.name);
                }
            } else {
                total_failed += 1;
                failed_tests.push(TestResult {
                    rel_path: rel_path.clone(),
                    line_num: tc.line_num,
                    name: tc.name.clone(),
                    input: tc.input.clone(),
                    expected: tc.expected.clone(),
                    actual,
                    err: err_msg,
                });
                if verbose {
                    println!("FAIL {}:{} {}", rel_path, tc.line_num, tc.name);
                }
            }
        }
    }
    let elapsed = start_time.elapsed().as_secs_f64();
    if total_failed > 0 {
        println!("{}", "=".repeat(60));
        println!("FAILURES");
        println!("{}", "=".repeat(60));
        let show_count = if max_failures > 0 && failed_tests.len() > max_failures {
            max_failures
        } else {
            failed_tests.len()
        };
        for f in failed_tests.iter().take(show_count) {
            println!("\n{}:{} {}", f.rel_path, f.line_num, f.name);
            println!("  Input:    {:?}", f.input);
            println!("  Expected: {}", f.expected);
            println!("  Actual:   {}", f.actual);
            if !f.err.is_empty() {
                println!("  Error:    {}", f.err);
            }
        }
        if max_failures > 0 && total_failed > max_failures {
            println!("\n... and {} more failures", total_failed - max_failures);
        }
    }
    println!("rust: {} passed, {} failed in {:.2}s", total_passed, total_failed, elapsed);
    if total_failed > 0 {
        process::exit(1);
    }
}
