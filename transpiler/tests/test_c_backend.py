"""Tests for C backend."""

from src.backend.c import CBackend
from tests.fixture import make_fixture

EXPECTED = """\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>

#define PARABLE_PANIC(msg) do { fprintf(stderr, "panic: %s\\n", msg); exit(1); } while(0)

typedef struct { char* data; size_t len; size_t cap; } String;

static String String_new(const char* s) {
    size_t len = s ? strlen(s) : 0;
    String str = {malloc(len + 1), len, len + 1};
    if (s) memcpy(str.data, s, len + 1);
    else str.data[0] = '\\0';
    return str;
}

#define SLICE_DEF(T, NAME) \\
typedef struct { T* data; size_t len; size_t cap; } NAME; \\
static NAME NAME##_new(size_t cap) { \\
    NAME s = {malloc(sizeof(T) * (cap ? cap : 1)), 0, cap ? cap : 1}; return s; } \\
static void NAME##_append(NAME* s, T val) { \\
    if (s->len >= s->cap) { s->cap = s->cap ? s->cap * 2 : 1; \\
    s->data = realloc(s->data, sizeof(T) * s->cap); } s->data[s->len++] = val; }

SLICE_DEF(int, IntSlice)
SLICE_DEF(bool, BoolSlice)
SLICE_DEF(double, FloatSlice)
SLICE_DEF(String, StringSlice)

typedef struct Token Token;
typedef struct Lexer Lexer;

SLICE_DEF(Token*, TokenSlice)
SLICE_DEF(Lexer*, LexerSlice)

static const int EOF = -1;

struct Token {
    String kind;
    String text;
    int pos;
};

struct Lexer {
    String source;
    int pos;
    Token* current;
};

bool is_space(int ch);
TokenSlice tokenize(String source);
int count_words(TokenSlice tokens);
String format_token(Token* tok);
Token* find_token(TokenSlice tokens, String kind);
String example_nil_check(TokenSlice tokens);
int sum_positions(TokenSlice tokens);
int first_word_pos(TokenSlice tokens);
int max_int(int a, int b);
void* default_kinds(void);
int scoped_work(int x);
int kind_priority(String kind);
TokenSlice safe_tokenize(String source);
double pi(void);
String describe_token(Token* tok);
void set_first_kind(TokenSlice tokens, String kind);
IntSlice make_int_slice(int n);
double int_to_float(int n);
void* known_kinds(void);
Token* call_static(void);
void* new_kind_map(void);
int get_array_first(int[10] arr);
Token* maybe_get(TokenSlice tokens, int idx);
void set_via_ptr(int* ptr, int val);
String identity_str(String s);
bool accept_union(void* obj);
bool Token_is_word(Token* self);
int Lexer_peek(Lexer* self);
void Lexer_advance(Lexer* self);
/* tuple */ Lexer_scan_word(Lexer* self);

bool is_space(int ch) {
    return ((ch == 32) || (ch == 10));
}

TokenSlice tokenize(String source) {
    Lexer* lx = (&(Lexer){.source = source, .pos = 0, .current = NULL});
    TokenSlice tokens = TokenSlice_new(0);
    while ((Lexer_peek(lx) != EOF)) {
        int ch = Lexer_peek(lx);
        if (is_space(ch)) {
            Lexer_advance(lx);
            continue;
        }
        /* tuple */ result = Lexer_scan_word(lx);
        Token* tok = result[0];
        bool ok = result[1];
        if (!ok) {
            PARABLE_PANIC("unexpected character");
        }
        TokenSlice_append(&tokens, tok);
    }
    return tokens;
}

int count_words(TokenSlice tokens) {
    int count = 0;
    for (size_t _i = 0; _i < tokens.len; _i++) {
        Token* tok = tokens.data[_i];
        if ((strcmp(tok->kind.data, "word") == 0)) {
            count += 1;
        }
    }
    return count;
}

String format_token(Token* tok) {
    return tok->kind + ":" + tok->text;
}

Token* find_token(TokenSlice tokens, String kind) {
    for (size_t _i = 0; _i < tokens.len; _i++) {
        Token* tok = tokens.data[_i];
        if ((strcmp(tok->kind.data, kind.data) == 0)) {
            return tok;
        }
    }
    return NULL;
}

String example_nil_check(TokenSlice tokens) {
    Token* tok = find_token(tokens, "word");
    if ((tok == NULL)) {
        return "";
    }
    return tok->text;
}

int sum_positions(TokenSlice tokens) {
    int sum = 0;
    for (int i = 0; (i < tokens.len); i = (i + 1)) {
        sum = (sum + tokens.data[i]->pos);
    }
    return sum;
}

int first_word_pos(TokenSlice tokens) {
    int pos = -1;
    for (size_t _i = 0; _i < tokens.len; _i++) {
        Token* tok = tokens.data[_i];
        if ((strcmp(tok->kind.data, "word") == 0)) {
            pos = tok->pos;
            break;
        }
    }
    return pos;
}

int max_int(int a, int b) {
    return ((a > b) ? a : b);
}

void* default_kinds(void) {
    return /* MapLit(3) */;
}

int scoped_work(int x) {
    int result = 0;
    {
        int temp = (x * 2);
        result = (temp + 1);
    }
    return result;
}

int kind_priority(String kind) {
    switch (kind) {
    case "word":
        return 1;
        break;
    case "num":
    case "float":
        return 2;
        break;
    case "op":
        return 3;
        break;
    default:
        return 0;
        break;
    }
}

TokenSlice safe_tokenize(String source) {
    TokenSlice tokens = TokenSlice_new(0);
    /* try */
    tokens = tokenize(source);
    /* catch (not supported) */
    return tokens;
}

double pi(void) {
    return 3.14159;
}

String describe_token(Token* tok) {
    return /* format("Token({0}, {1}, {2})") */;
}

void set_first_kind(TokenSlice tokens, String kind) {
    if ((tokens.len > 0)) {
        tokens.data[0] = (&(Token){.kind = kind, .text = "", .pos = 0});
    }
}

IntSlice make_int_slice(int n) {
    return IntSlice_new(n);
}

double int_to_float(int n) {
    return ((double)n);
}

void* known_kinds(void) {
    return /* SetLit(3) */;
}

Token* call_static(void) {
    return Token_empty();
}

void* new_kind_map(void) {
    return /* MakeMap */;
}

int get_array_first(int[10] arr) {
    return arr[0];
}

Token* maybe_get(TokenSlice tokens, int idx) {
    if ((idx >= tokens.len)) {
        return NULL;
    }
    return tokens.data[idx];
}

void set_via_ptr(int* ptr, int val) {
    *ptr = val;
}

String identity_str(String s) {
    return s;
}

bool accept_union(void* obj) {
    return true;
}

bool Token_is_word(Token* self) {
    return (strcmp(t->kind.data, "word") == 0);
}

int Lexer_peek(Lexer* self) {
    if ((lx->pos >= lx->source.len)) {
        return EOF;
    }
    return lx->source.data[lx->pos];
}

void Lexer_advance(Lexer* self) {
    lx->pos += 1;
}

/* tuple */ Lexer_scan_word(Lexer* self) {
    int start = lx->pos;
    while (((Lexer_peek(lx) != EOF) && !is_space(Lexer_peek(lx)))) {
        Lexer_advance(lx);
    }
    if ((lx->pos == start)) {
        return /* TupleLit */;
    }
    String text = /* slice */;
    return /* TupleLit */;
}
"""


def test_fixture_emits_correct_c() -> None:
    module = make_fixture()
    backend = CBackend()
    output = backend.emit(module)
    assert output == EXPECTED
