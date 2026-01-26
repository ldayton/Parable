"""Tests for C backend."""

from src.backend.c import CBackend
from tests.fixture import make_fixture

EXPECTED = """#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdarg.h>

#define PARABLE_PANIC(msg) do { fprintf(stderr, "panic: %s\\n", msg); exit(1); } while(0)

typedef struct { char* data; size_t len; size_t cap; } String;

static String String_new(const char* s) {
    size_t len = s ? strlen(s) : 0;
    String str = {malloc(len + 1), len, len + 1};
    if (s) memcpy(str.data, s, len + 1);
    else str.data[0] = '\\0';
    return str;
}

static String parable_strcat(String a, String b) {
    size_t len = a.len + b.len;
    String str = {malloc(len + 1), len, len + 1};
    memcpy(str.data, a.data, a.len);
    memcpy(str.data + a.len, b.data, b.len + 1);
    return str;
}

static String parable_slice(String s, size_t start, size_t end) {
    if (start > s.len) start = s.len;
    if (end > s.len) end = s.len;
    if (start > end) start = end;
    size_t len = end - start;
    String str = {malloc(len + 1), len, len + 1};
    memcpy(str.data, s.data + start, len);
    str.data[len] = '\\0';
    return str;
}

static String parable_sprintf(const char* fmt, ...) {
    va_list args, args2;
    va_start(args, fmt);
    va_copy(args2, args);
    int len = vsnprintf(NULL, 0, fmt, args);
    va_end(args);
    String str = {malloc(len + 1), len, len + 1};
    vsnprintf(str.data, len + 1, fmt, args2);
    va_end(args2);
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

typedef struct { Token* f0; bool f1; } Tuple1;

typedef struct { String key; int val; bool used; } Map_String_int_Entry;
typedef struct { Map_String_int_Entry* data; size_t cap; size_t len; } Map_String_int;
static Map_String_int Map_String_int_new(void) { Map_String_int m = {calloc(16, sizeof(Map_String_int_Entry)), 16, 0}; return m; }
static size_t Map_String_int_hash(String k) { size_t h = 5381; for (size_t i = 0; i < k.len; i++) h = ((h << 5) + h) + k.data[i]; return h; }
static bool Map_String_int_eq(String a, String b) { return a.len == b.len && memcmp(a.data, b.data, a.len) == 0; }
static void Map_String_int_set(Map_String_int* m, String k, int v) {
    if (m->len * 2 >= m->cap) { size_t nc = m->cap * 2; Map_String_int_Entry* nd = calloc(nc, sizeof(Map_String_int_Entry));
    for (size_t i = 0; i < m->cap; i++) if (m->data[i].used) { size_t j = Map_String_int_hash(m->data[i].key) % nc; while (nd[j].used) j = (j+1) % nc; nd[j] = m->data[i]; }
    free(m->data); m->data = nd; m->cap = nc; }
    size_t i = Map_String_int_hash(k) % m->cap; while (m->data[i].used && !Map_String_int_eq(m->data[i].key, k)) i = (i+1) % m->cap;
    if (!m->data[i].used) m->len++;
    m->data[i] = (Map_String_int_Entry){k, v, true};
}
static int Map_String_int_get(Map_String_int* m, String k) {
    size_t i = Map_String_int_hash(k) % m->cap;
    while (m->data[i].used) { if (Map_String_int_eq(m->data[i].key, k)) return m->data[i].val; i = (i+1) % m->cap; }
    return 0;
}
typedef struct { String val; bool used; } Set_String_Entry;
typedef struct { Set_String_Entry* data; size_t cap; size_t len; } Set_String;
static Set_String Set_String_new(void) { Set_String s = {calloc(16, sizeof(Set_String_Entry)), 16, 0}; return s; }
static size_t Set_String_hash(String k) { size_t h = 5381; for (size_t i = 0; i < k.len; i++) h = ((h << 5) + h) + k.data[i]; return h; }
static bool Set_String_eq(String a, String b) { return a.len == b.len && memcmp(a.data, b.data, a.len) == 0; }
static void Set_String_add(Set_String* s, String v) {
    if (s->len * 2 >= s->cap) { size_t nc = s->cap * 2; Set_String_Entry* nd = calloc(nc, sizeof(Set_String_Entry));
    for (size_t i = 0; i < s->cap; i++) if (s->data[i].used) { size_t j = Set_String_hash(s->data[i].val) % nc; while (nd[j].used) j = (j+1) % nc; nd[j] = s->data[i]; }
    free(s->data); s->data = nd; s->cap = nc; }
    size_t i = Set_String_hash(v) % s->cap; while (s->data[i].used && !Set_String_eq(s->data[i].val, v)) i = (i+1) % s->cap;
    if (!s->data[i].used) s->len++;
    s->data[i] = (Set_String_Entry){v, true};
}
static bool Set_String_contains(Set_String* s, String v) {
    size_t i = Set_String_hash(v) % s->cap;
    while (s->data[i].used) { if (Set_String_eq(s->data[i].val, v)) return true; i = (i+1) % s->cap; }
    return false;
}

SLICE_DEF(Token*, TokenSlice)
SLICE_DEF(Lexer*, LexerSlice)

static const int PARABLE_EOF = -1;

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
Map_String_int default_kinds(void);
int scoped_work(int x);
int kind_priority(String kind);
TokenSlice safe_tokenize(String source);
double pi(void);
String describe_token(Token* tok);
void set_first_kind(TokenSlice tokens, String kind);
IntSlice make_int_slice(int n);
double int_to_float(int n);
Set_String known_kinds(void);
Token* call_static(void);
Map_String_int new_kind_map(void);
int get_array_first(int arr[10]);
Token* maybe_get(TokenSlice tokens, int idx);
void set_via_ptr(int* ptr, int val);
String identity_str(String s);
bool accept_union(void* obj);
bool Token_is_word(Token* self);
int Lexer_peek(Lexer* self);
void Lexer_advance(Lexer* self);
Tuple1 Lexer_scan_word(Lexer* self);

bool is_space(int ch) {
    return ch == 32 || ch == 10;
}

TokenSlice tokenize(String source) {
    Lexer* lx = (&(Lexer){.source = source, .pos = 0, .current = NULL});
    TokenSlice tokens = TokenSlice_new(0);
    while (Lexer_peek(lx) != PARABLE_EOF) {
        int ch = Lexer_peek(lx);
        if (is_space(ch)) {
            Lexer_advance(lx);
            continue;
        }
        Tuple1 result = Lexer_scan_word(lx);
        Token* tok = result.f0;
        bool ok = result.f1;
        if (!ok) {
            PARABLE_PANIC(String_new("unexpected character"));
        }
        TokenSlice_append(&tokens, tok);
    }
    return tokens;
}

int count_words(TokenSlice tokens) {
    int count = 0;
    for (size_t _i = 0; _i < tokens.len; _i++) {
        Token* tok = tokens.data[_i];
        if (strcmp(tok->kind.data, "word") == 0) {
            count++;
        }
    }
    return count;
}

String format_token(Token* tok) {
    return parable_strcat(parable_strcat(tok->kind, String_new(":")), tok->text);
}

Token* find_token(TokenSlice tokens, String kind) {
    for (size_t _i = 0; _i < tokens.len; _i++) {
        Token* tok = tokens.data[_i];
        if (strcmp(tok->kind.data, kind.data) == 0) {
            return tok;
        }
    }
    return NULL;
}

String example_nil_check(TokenSlice tokens) {
    Token* tok = find_token(tokens, String_new("word"));
    if (tok == NULL) {
        return String_new("");
    }
    return tok->text;
}

int sum_positions(TokenSlice tokens) {
    int sum = 0;
    for (int i = 0; i < tokens.len; i++) {
        sum += tokens.data[i]->pos;
    }
    return sum;
}

int first_word_pos(TokenSlice tokens) {
    int pos = -1;
    for (size_t _i = 0; _i < tokens.len; _i++) {
        Token* tok = tokens.data[_i];
        if (strcmp(tok->kind.data, "word") == 0) {
            pos = tok->pos;
            break;
        }
    }
    return pos;
}

int max_int(int a, int b) {
    return a > b ? a : b;
}

Map_String_int default_kinds(void) {
    return ({ Map_String_int _m = Map_String_int_new(); Map_String_int_set(&_m, String_new("word"), 1); Map_String_int_set(&_m, String_new("num"), 2); Map_String_int_set(&_m, String_new("op"), 3); _m; });
}

int scoped_work(int x) {
    int result = 0;
    {
        int temp = x * 2;
        result = temp + 1;
    }
    return result;
}

int kind_priority(String kind) {
    if (strcmp(kind.data, "word") == 0) {
        return 1;
    } else if (strcmp(kind.data, "num") == 0 || strcmp(kind.data, "float") == 0) {
        return 2;
    } else if (strcmp(kind.data, "op") == 0) {
        return 3;
    } else {
        return 0;
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
    return parable_sprintf("Token(%s, %s, %d)", tok->kind.data, tok->text.data, tok->pos);
}

void set_first_kind(TokenSlice tokens, String kind) {
    if (tokens.len > 0) {
        tokens.data[0] = (&(Token){.kind = kind, .text = String_new(""), .pos = 0});
    }
}

IntSlice make_int_slice(int n) {
    return IntSlice_new(n);
}

double int_to_float(int n) {
    return (double)n;
}

Set_String known_kinds(void) {
    return ({ Set_String _s = Set_String_new(); Set_String_add(&_s, String_new("word")); Set_String_add(&_s, String_new("num")); Set_String_add(&_s, String_new("op")); _s; });
}

Token* call_static(void) {
    return Token_empty();
}

Map_String_int new_kind_map(void) {
    return Map_String_int_new();
}

int get_array_first(int arr[10]) {
    return arr[0];
}

Token* maybe_get(TokenSlice tokens, int idx) {
    if (idx >= tokens.len) {
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
    return strcmp(self->kind.data, "word") == 0;
}

int Lexer_peek(Lexer* self) {
    if (self->pos >= self->source.len) {
        return PARABLE_EOF;
    }
    return self->source.data[self->pos];
}

void Lexer_advance(Lexer* self) {
    self->pos++;
}

Tuple1 Lexer_scan_word(Lexer* self) {
    int start = self->pos;
    while (Lexer_peek(self) != PARABLE_EOF && !is_space(Lexer_peek(self))) {
        Lexer_advance(self);
    }
    if (self->pos == start) {
        return (Tuple1){.f0 = (&(Token){}), .f1 = false};
    }
    String text = parable_slice(self->source, start, self->pos);
    return (Tuple1){.f0 = (&(Token){.kind = String_new("word"), .text = text, .pos = start}), .f1 = true};
}
"""


def test_fixture_emits_correct_c() -> None:
    module = make_fixture()
    backend = CBackend()
    output = backend.emit(module)
    assert output == EXPECTED
