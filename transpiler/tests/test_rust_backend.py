"""Tests for Rust backend."""

from src.backend.rust import RustBackend
from tests.fixture import make_fixture

EXPECTED = """\
use std::collections::{HashMap, HashSet};

const EOF: i64 = -1;

trait Scanner {
    fn peek(&self) -> i64;
    fn advance(&self);
}

struct Token {
    kind: String,
    text: String,
    pos: i64,
}

impl Token {
    fn is_word(&mut self) -> bool {
        return self.kind == "word";
    }
}

struct Lexer {
    source: String,
    pos: i64,
    current: Option<Token>,
}

impl Lexer {
    fn peek(&mut self) -> i64 {
        if self.pos >= self.source.len() {
            return EOF;
        }
        return self.source[self.pos];
    }

    fn advance(&mut self) {
        self.pos += 1;
    }

    fn scan_word(&mut self) -> (Token, bool) {
        let mut start: i64 = self.pos;
        while self.peek() != EOF && !is_space(self.peek()) {
            self.advance();
        }
        if self.pos == start {
            return (Token::default(), false);
        }
        let mut text: String = self.source[start..self.pos].to_string();
        return (Token { kind: "word".to_string(), text: text, pos: start }, true);
    }
}

fn is_space(ch: i64) -> bool {
    return ch == 32 || ch == 10;
}

fn tokenize(source: String) -> Vec<Token> {
    let mut lx: Lexer = Lexer { source: source, pos: 0, current: None };
    let mut tokens: Vec<Token> = vec![];
    while lx.peek() != EOF {
        let mut ch: i64 = lx.peek();
        if is_space(ch) {
            lx.advance();
            continue;
        }
        let mut result: (Token, bool) = lx.scan_word();
        let mut tok: Token = result.0;
        let mut ok: bool = result.1;
        if !ok {
            panic!("{}", "unexpected character".to_string());
        }
        tokens.push(tok);
    }
    return tokens;
}

fn count_words(tokens: Vec<Token>) -> i64 {
    let mut count: i64 = 0;
    for tok in tokens.iter() {
        if tok.kind == "word" {
            count += 1;
        }
    }
    return count;
}

fn format_token(tok: Token) -> String {
    return tok.kind + ":".to_string() + tok.text;
}

fn find_token(tokens: Vec<Token>, kind: String) -> Option<Token> {
    for tok in tokens.iter() {
        if tok.kind == kind {
            return tok;
        }
    }
    return None;
}

fn example_nil_check(tokens: Vec<Token>) -> String {
    let mut tok: Option<Token> = find_token(tokens, "word".to_string());
    if tok.is_none() {
        return "".to_string();
    }
    return tok.text;
}

fn sum_positions(tokens: Vec<Token>) -> i64 {
    let mut sum: i64 = 0;
    let mut i: i64 = 0;
    while i < tokens.len() {
        sum = (sum + tokens[i].pos);
        i = (i + 1);
    }
    return sum;
}

fn first_word_pos(tokens: Vec<Token>) -> i64 {
    let mut pos: i64 = -1;
    for tok in tokens.iter() {
        if tok.kind == "word" {
            pos = tok.pos;
            break;
        }
    }
    return pos;
}

fn max_int(a: i64, b: i64) -> i64 {
    return if a > b { a } else { b };
}

fn default_kinds() -> HashMap<String, i64> {
    return HashMap::from([("word".to_string(), 1), ("num".to_string(), 2), ("op".to_string(), 3)]);
}

fn scoped_work(x: i64) -> i64 {
    let mut result: i64 = 0;
    {
        let mut temp: i64 = (x * 2);
        result = (temp + 1);
    }
    return result;
}

fn kind_priority(kind: String) -> i64 {
    match kind.as_str() {
        "word" => {
            return 1;
        }
        "num" | "float" => {
            return 2;
        }
        "op" => {
            return 3;
        }
        _ => {
            return 0;
        }
    }
}

fn safe_tokenize(source: String) -> Vec<Token> {
    let mut tokens: Vec<Token> = vec![];
    let _result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        tokens = tokenize(source);
    }));
    if let Err(e) = _result {
        tokens = vec![];
    }
    return tokens;
}

fn pi() -> f64 {
    return 3.14159;
}

fn describe_token(tok: Token) -> String {
    return format!("Token({}, {}, {})", tok.kind, tok.text, tok.pos);
}

fn set_first_kind(tokens: Vec<Token>, kind: String) {
    if tokens.len() > 0 {
        tokens[0] = Token { kind: kind, text: "".to_string(), pos: 0 };
    }
}

fn make_int_slice(n: i64) -> Vec<i64> {
    return vec![0; n];
}

fn int_to_float(n: i64) -> f64 {
    return (n as f64);
}

fn known_kinds() -> HashSet<String> {
    return HashSet::from(["word".to_string(), "num".to_string(), "op".to_string()]);
}

fn call_static() -> Token {
    return Token::empty();
}

fn new_kind_map() -> HashMap<String, i64> {
    return HashMap::<String, i64>::new();
}

fn get_array_first(arr: [i64; 10]) -> i64 {
    return arr[0];
}

fn maybe_get(tokens: Vec<Token>, idx: i64) -> Option<Token> {
    if idx >= tokens.len() {
        return None;
    }
    return tokens[idx];
}

fn set_via_ptr(ptr: Box<i64>, val: i64) {
    *ptr = val;
}

fn identity_str(s: &str) -> &str {
    return s;
}

fn accept_union(obj: (Token, Lexer)) -> bool {
    return true;
}"""


def test_fixture_emits_correct_rust() -> None:
    module = make_fixture()
    backend = RustBackend()
    output = backend.emit(module)
    assert output == EXPECTED
