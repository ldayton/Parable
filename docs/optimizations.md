# Optimization Opportunities

## 1. Inline Hot Path Methods

### Current
```python
def peek(self) -> str | None:
    if self.at_end():
        return None
    return self.source[self.pos]

def at_end(self) -> bool:
    return self.pos >= self.length

def skip_whitespace(self) -> None:
    while not self.at_end() and self.peek() in " \t":
        self.advance()
```

### Optimized
```python
def peek(self) -> str | None:
    return self.source[self.pos] if self.pos < self.length else None

def skip_whitespace(self) -> None:
    source, length = self.source, self.length
    pos = self.pos
    while pos < length and source[pos] in _WHITESPACE:
        pos += 1
    self.pos = pos
```

**Estimated impact:** 5-10% overall speedup

**LLM considerations:**
- Inlined logic is harder for LLMs to reason about because the semantic abstraction (`at_end()`) is lost
- Local variable aliasing (`source = self.source`) obscures the relationship to instance state
- LLMs may struggle to understand that `pos` is a snapshot that must be written back

**Other considerations:**
- Must ensure `self.length` is always set correctly in `__init__`
- Risk of divergence if `peek()` semantics change but inlined copies don't


## 2. Cached Character Sets

### Current
```python
# Inline string literals checked repeatedly
if ch in " \t\n":
    ...
if ch in " \t":
    ...
```

### Optimized
```python
_WHITESPACE = frozenset(' \t')
_WHITESPACE_NEWLINE = frozenset(' \t\n')
_METACHAR = frozenset(' \t\n|&;()<>')

# In hot loops
if ch in _WHITESPACE_NEWLINE:
    ...
```

**Estimated impact:** 3-5% speedup

**LLM considerations:**
- Module-level constants are semantically clear
- LLMs handle this well; the pattern is common in Python
- The underscore prefix convention may confuse some models about visibility

**Other considerations:**
- `frozenset` vs `set`: frozenset is hashable and immutable, marginally faster for membership tests
- Must keep constants in sync with usage sites


## 3. ASCII Range Checks

### Current
```python
if ch.isalpha() or ch == "_":
    ...
if ch.isdigit():
    ...
```

### Optimized
```python
def _is_name_start(ch: str) -> bool:
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ch == '_'

def _is_name_char(ch: str) -> bool:
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or ch == '_'

def _is_digit(ch: str) -> bool:
    return '0' <= ch <= '9'
```

**Estimated impact:** 5-8% speedup in arithmetic and parameter expansion parsing

**LLM considerations:**
- Range comparison chains are less intuitive than `.isalpha()`
- LLMs may not realize this is semantically different (ASCII-only vs Unicode)
- The semantic intent ("is this a valid bash identifier character") is lost

**Other considerations:**
- Bash identifiers are ASCII-only, so this is correct
- `.isalpha()` returns True for Unicode letters, which would be a bug to accept
- These functions should be module-level or static methods to avoid `self` lookup


## 4. Add `__slots__` to AST Nodes

### Current
```python
@dataclass
class Word(Node):
    value: str
    parts: list[Node] = field(default_factory=list)
```

### Optimized
```python
@dataclass(slots=True)
class Word(Node):
    value: str
    parts: list[Node] = field(default_factory=list)
```

Or for Python 3.10-3.12 compatibility:
```python
@dataclass
class Word(Node):
    __slots__ = ('value', 'parts')
    value: str
    parts: list[Node] = field(default_factory=list)
```

**Estimated impact:** 40-50% memory reduction for AST nodes; slight CPU improvement from cache locality

**LLM considerations:**
- `__slots__` is a well-known Python pattern; LLMs handle it well
- The `slots=True` dataclass parameter is cleaner and more recognizable
- Manual `__slots__` definition alongside dataclass fields can confuse LLMs about which is authoritative

**Other considerations:**
- Inheritance with slots requires care: parent class must also define `__slots__`
- Cannot dynamically add attributes to slotted instances (but we don't need to)
- `dataclass(slots=True)` requires Python 3.10+; manual `__slots__` works on 3.9+


## 5. Unchecked Advance Variant

### Current
```python
def advance(self) -> str | None:
    if self.at_end():
        return None
    ch = self.source[self.pos]
    self.pos += 1
    return ch
```

### Optimized
```python
def _advance_unchecked(self) -> str:
    ch = self.source[self.pos]
    self.pos += 1
    return ch
```

Used in loops where bounds are already verified:
```python
while self.pos < self.length and self.source[self.pos] in _WHITESPACE:
    self._advance_unchecked()
```

**Estimated impact:** 2-3% in tight loops

**LLM considerations:**
- Two similar methods with different safety guarantees is confusing
- LLMs may use the unchecked variant incorrectly
- The `_` prefix suggests internal use but doesn't prevent misuse in prompts

**Other considerations:**
- Risk of index errors if used incorrectly
- Could alternatively just inline the logic at call sites


## 6. First-Character Dispatch in parse_word()

### Current
```python
while not self.at_end():
    ch = self.peek()
    if ch == "'":
        # single quote
    elif ch == '"':
        # double quote
    elif ch == "\\":
        # escape
    elif ch == "$" and ...:
        # expansion
    # ... 8 more elif branches
```

### Optimized
```python
_WORD_HANDLERS = {
    "'": '_handle_single_quote',
    '"': '_handle_double_quote',
    '\\': '_handle_escape',
    '$': '_handle_dollar',
    '`': '_handle_backtick',
    '<': '_handle_less_than',
    '>': '_handle_greater_than',
}

while self.pos < self.length:
    ch = self.source[self.pos]
    handler_name = _WORD_HANDLERS.get(ch)
    if handler_name:
        getattr(self, handler_name)(chars, parts)
    elif ch in _METACHAR:
        break
    else:
        chars.append(ch)
        self.pos += 1
```

**Estimated impact:** 3-5% in word parsing

**LLM considerations:**
- Dispatch tables fragment logic across multiple methods
- LLMs struggle to follow the flow when control is indirect
- The original sequential `if-elif` chain is much easier for LLMs to trace
- Method name strings in dicts are opaque to static analysis and LLMs

**Other considerations:**
- `getattr` call overhead may negate gains for simple cases
- Alternative: use a match statement (Python 3.10+), which LLMs understand better
- The sequential if-elif is actually well-predicted by CPU branch predictors for common cases


## 7. Table-Driven Arithmetic Precedence

### Current
27 separate methods for arithmetic parsing, one per precedence level:
```python
def _arith_parse_logical_or(self):
    left = self._arith_parse_logical_and()
    while self._arith_match("||"):
        self._arith_consume("||")
        right = self._arith_parse_logical_and()
        left = ArithBinaryOp("||", left, right)
    return left
```

### Optimized
```python
_ARITH_OPS = [
    (1, ['||'], 'left'),
    (2, ['&&'], 'left'),
    (3, ['|'], 'left'),
    (4, ['^'], 'left'),
    (5, ['&'], 'left'),
    (6, ['==', '!='], 'left'),
    (7, ['<=', '>=', '<', '>'], 'left'),
    (8, ['<<', '>>'], 'left'),
    (9, ['+', '-'], 'left'),
    (10, ['*', '/', '%'], 'left'),
    (11, ['**'], 'right'),
]

def _arith_parse_binary(self, min_prec: int):
    left = self._arith_parse_unary()
    while True:
        op, prec, assoc = self._get_binary_op()
        if prec < min_prec:
            break
        self._arith_consume(op)
        next_prec = prec + 1 if assoc == 'left' else prec
        right = self._arith_parse_binary(next_prec)
        left = ArithBinaryOp(op, left, right)
    return left
```

**Estimated impact:** 2-3% speedup, significant code reduction

**LLM considerations:**
- Precedence climbing algorithms are notoriously hard for LLMs to understand
- The current explicit method-per-level is verbose but extremely clear
- Table-driven parsing requires understanding the algorithm to modify correctly
- LLMs frequently make errors when asked to modify precedence tables

**Other considerations:**
- Assignment operators have special semantics (right-associative, require lvalue)
- Ternary operator doesn't fit the binary pattern
- Debugging is harder with table-driven parsing


## 8. Bulk Character Consumption

### Current
```python
# In _consume_param_name()
name_chars = []
while not self.at_end() and (self.peek().isalnum() or self.peek() == "_"):
    name_chars.append(self.advance())
return "".join(name_chars)
```

### Optimized
```python
def _consume_param_name(self) -> str:
    start = self.pos
    source, length = self.source, self.length
    pos = self.pos
    while pos < length:
        ch = source[pos]
        if not (('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or ch == '_'):
            break
        pos += 1
    self.pos = pos
    return source[start:pos]
```

**Estimated impact:** 1-2% for identifier-heavy scripts

**LLM considerations:**
- String slicing (`source[start:pos]`) is idiomatic and LLM-friendly
- The optimized version is actually clearer about intent (extract a span)
- Local variable aliasing is the main LLM obstacle

**Other considerations:**
- The original list-append-join pattern is necessary when characters need transformation
- For simple extraction, slicing is both faster and clearer


## 9. CPython Internals

Research on CPython performance characteristics relevant to parser optimization.

### Membership Testing

| Pattern | Time | Notes |
|---------|------|-------|
| `x in set` | ~100 ns | O(1), constant regardless of size |
| `x in list` (miss) | ~11 ms | O(n), 100,000x slower than set |
| `x in {a, b, c}` | ~100 ns | Compiled to `frozenset` constant (3.2+) |
| `x in "abc"` | O(n) | Linear scan |

Set literals in membership tests are converted to `frozenset` at compile time by the peephole optimizer.

Sources: [switowski.com](https://switowski.com/blog/membership-testing/), [sopython wiki](https://sopython.com/wiki/Peephole_optimisations_for_tuple,_list,_set)

### Local Variable Access

| Opcode | Use | Relative Speed |
|--------|-----|----------------|
| LOAD_FAST | Local variables | 1x (fastest) |
| LOAD_ATTR | `self.x`, `obj.x` | ~2x slower |

Source: [tenthousandmeters.com](https://tenthousandmeters.com/blog/python-behind-the-scenes-5-how-variables-are-implemented-in-cpython/)

### Python 3.11+ Changes

| Pattern | Pre-3.11 | 3.11+ |
|---------|----------|-------|
| `_len = len` (builtin alias) | Helps | No longer needed |
| `_sin = math.sin` (module attr) | Helps | Still helps |
| `source = self.source` (instance attr) | Helps | Still helps |

Builtins are now auto-specialized. Attribute chains still benefit from aliasing.

Source: [codingconfessions.com](https://blog.codingconfessions.com/p/old-python-performance-trick)

### Function Call Overhead

50-100 ns per call, adds up over millions of iterations.

Sources: [futurelearn](https://www.futurelearn.com/info/courses/python-in-hpc/0/steps/65124), [Gregory Szorc](https://gregoryszorc.com/blog/2019/01/10/what-i've-learned-about-optimizing-python/)


## Summary

| Optimization            | Speedup | Memory | LLM Impact |
| ----------------------- | ------- | ------ | ---------- |
| Inline hot paths        | 5-10%   | —      | Moderate   |
| Cached character sets   | 3-5%    | —      | Low        |
| ASCII range checks      | 5-8%    | —      | Moderate   |
| `__slots__` on nodes    | —       | 40-50% | Low        |
| Unchecked advance       | 2-3%    | —      | High       |
| Dispatch tables         | 3-5%    | —      | High       |
| Table-driven precedence | 2-3%    | —      | Very High  |
| Bulk consumption        | 1-2%    | —      | Low        |
