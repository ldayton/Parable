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

#[derive(Clone, Default)]
struct Token {
    kind: String,
    text: String,
    pos: i64,
}

impl Token {
    fn is_word(&self) -> bool {
        self.kind == "word"
    }
}

#[derive(Clone, Default)]
struct Lexer {
    source: String,
    pos: i64,
    current: Option<Token>,
}

impl Lexer {
    fn peek(&mut self) -> i64 {
        if self.pos >= (self.source.len() as i64) {
            return EOF;
        }
        self.source.as_bytes()[self.pos as usize] as i64
    }

    fn advance(&mut self) {
        self.pos += 1;
    }

    fn scan_word(&mut self) -> (Token, bool) {
        let start: i64 = self.pos;
        while self.peek() != EOF && !is_space(self.peek()) {
            self.advance();
        }
        if self.pos == start {
            return (Token::default(), false);
        }
        let text: String = self.source[(start as usize)..(self.pos as usize)].to_string();
        (Token { kind: "word".to_string(), text, pos: start }, true)
    }
}

fn is_space(ch: i64) -> bool {
    ch == 32 || ch == 10
}

fn tokenize(source: String) -> Vec<Token> {
    let mut lx: Lexer = Lexer { source, pos: 0, current: None };
    let mut tokens: Vec<Token> = vec![];
    while lx.peek() != EOF {
        let ch: i64 = lx.peek();
        if is_space(ch) {
            lx.advance();
            continue;
        }
        let (tok, ok) = lx.scan_word();
        if !ok {
            panic!("unexpected character");
        }
        tokens.push(tok);
    }
    tokens
}

fn count_words(tokens: Vec<Token>) -> i64 {
    let mut count: i64 = 0;
    for tok in tokens.iter() {
        if tok.kind == "word" {
            count += 1;
        }
    }
    count
}

fn format_token(tok: Token) -> String {
    tok.kind + ":" + &tok.text
}

fn find_token(tokens: Vec<Token>, kind: String) -> Option<Token> {
    for tok in tokens.iter() {
        if tok.kind == kind {
            return Some(tok.clone());
        }
    }
    None
}

fn example_nil_check(tokens: Vec<Token>) -> String {
    let tok: Option<Token> = find_token(tokens, "word".to_string());
    if tok.is_none() {
        return "".to_string();
    }
    tok.as_ref().unwrap().text.clone()
}

fn sum_positions(tokens: Vec<Token>) -> i64 {
    let mut sum: i64 = 0;
    let mut i: i64 = 0;
    while i < (tokens.len() as i64) {
        sum += tokens[i as usize].pos;
        i += 1;
    }
    sum
}

fn first_word_pos(tokens: Vec<Token>) -> i64 {
    let mut pos: i64 = -1;
    for tok in tokens.iter() {
        if tok.kind == "word" {
            pos = tok.pos;
            break;
        }
    }
    pos
}

fn max_int(a: i64, b: i64) -> i64 {
    if a > b { a } else { b }
}

fn default_kinds() -> HashMap<String, i64> {
    HashMap::from([("word".to_string(), 1), ("num".to_string(), 2), ("op".to_string(), 3)])
}

fn scoped_work(x: i64) -> i64 {
    let mut result: i64 = 0;
    {
        let temp: i64 = x * 2;
        result = temp + 1;
    }
    result
}

fn kind_priority(kind: String) -> i64 {
    match kind.as_str() {
        "word" => 1,
        "num" | "float" => 2,
        "op" => 3,
        _ => 0,
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
    tokens
}

fn pi() -> f64 {
    3.14159
}

fn describe_token(tok: Token) -> String {
    format!("Token({}, {}, {})", tok.kind, tok.text, tok.pos)
}

fn set_first_kind(mut tokens: Vec<Token>, kind: String) {
    if !tokens.is_empty() {
        tokens[0] = Token { kind, text: "".to_string(), pos: 0 };
    }
}

fn make_int_slice(n: i64) -> Vec<i64> {
    vec![0; n as usize]
}

fn int_to_float(n: i64) -> f64 {
    n as f64
}

fn known_kinds() -> HashSet<String> {
    HashSet::from(["word".to_string(), "num".to_string(), "op".to_string()])
}

fn call_static() -> Token {
    Token::default()
}

fn new_kind_map() -> HashMap<String, i64> {
    HashMap::<String, i64>::new()
}

fn get_array_first(arr: [i64; 10]) -> i64 {
    arr[0]
}

fn maybe_get(tokens: Vec<Token>, idx: i64) -> Option<Token> {
    if idx >= (tokens.len() as i64) {
        return None;
    }
    Some(tokens[idx as usize].clone())
}

fn set_via_ptr(mut ptr: Box<i64>, val: i64) {
    *ptr = val;
}

fn identity_str(s: &str) -> &str {
    s
}

fn accept_union(obj: (Token, Lexer)) -> bool {
    true
}"""


def test_fixture_emits_correct_rust() -> None:
    module = make_fixture()
    backend = RustBackend()
    output = backend.emit(module)
    assert output == EXPECTED
