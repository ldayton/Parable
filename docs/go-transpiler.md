# Go Transpiler Research

This document captures research for building a Python-to-Go transpiler for Parable, modeled after the existing `transpile_js.py`.

## Context

Parable is a recursive descent bash parser (~11k lines Python) that produces an AST. The existing JS transpiler (`tools/transpiler/src/transpiler/transpile_js.py`, ~1000 lines) uses Python's `ast` module to walk the source and emit JavaScript.

The Go transpiler would follow the same pattern:

```
Python source (parable.py)
    → ast.parse()
    → GoTranspiler(ast.NodeVisitor)
    → Go source (parable.go)
```

## Challenge 1: Node Hierarchy

**Problem**: Python uses class inheritance (`class Word(Node)`). Go has no classes.

**Solution**: Interface + structs, following Go's own `go/ast` package pattern.

```go
// Base interface
type Node interface {
    ToSexp() string
    Kind() string
}

// Concrete type
type Word struct {
    kind  string
    Value string
    Parts []Node
}

func (w *Word) Kind() string    { return w.kind }
func (w *Word) ToSexp() string  { /* implementation */ }
```

**Key difference from Python**: When calling a method on an embedded struct, the receiver is the embedded type, not the outer type. This matters if we ever need "super()" behavior.

**Status**: Well-understood. Go's `go/ast` is a clear model.

## Challenge 2: Error Handling

**Problem**: Parable uses exceptions (`raise ParseError(...)`). Go uses error returns.

**Solution**: Use `panic`/`recover` internally, convert to error at API boundary. This is exactly what Go's own parser does.

```go
// Internal error type
type ParseError struct {
    Message string
    Pos     int
    Line    int
}

// Parsing methods panic on error
func (p *Parser) expect(tok TokenType) {
    if p.current.Type != tok {
        panic(ParseError{Message: "unexpected token", Pos: p.pos})
    }
}

// Public API recovers
func Parse(source string) ([]Node, error) {
    defer func() {
        if r := recover(); r != nil {
            if pe, ok := r.(ParseError); ok {
                err = &pe
                return
            }
            panic(r) // re-panic unknown
        }
    }()
    // ... parsing
}
```

Go's parser uses a `bailout` struct and panics after 10 errors unless `AllErrors` mode is set.

**Status**: Well-understood. Clear precedent in Go stdlib.

## Challenge 3: Optional Parameters

**Problem**: Python has default parameter values. Go doesn't.

```python
def __init__(self, message: str, pos: int = None, line: int = None):
```

### Audit Results

**33 functions with defaults found.** Breakdown by pattern:

| Pattern                      | Count | Examples                        | Go Strategy                   |
| ---------------------------- | ----- | ------------------------------- | ----------------------------- |
| `= None` for lists           | 9     | `redirects`, `parts`            | `nil` slice, check in body    |
| `= None` for optional fields | 8     | `pos`, `line`, `op`, `arg`      | Keep as-is, nil works         |
| `= False` boolean flags      | 12    | `extglob`, `in_dquote`, `brace` | Zero value (no change needed) |
| `= 0` numeric flags          | 4     | `flags`, `kind`, `offset`       | Zero value (no change needed) |
| `= "string"` constant        | 1     | `terminator=";;"`               | Pass explicitly at call sites |

### Transpiler Strategy

**Rule 1: Zero-value defaults need no special handling.**
```python
def __init__(self, extglob: bool = False):  # Python
```
```go
func NewParser(source string, extglob bool) *Parser  // Go - caller passes false
```

**Rule 2: `None` list defaults use nil slices.**
All 9 cases already have `if x is None: x = []` guards in the Python:
```python
def __init__(self, redirects: list = None):
    if redirects is None:
        redirects = []
```
```go
func NewWhile(..., redirects []Redirect) *While {
    if redirects == nil {
        redirects = []Redirect{}
    }
    // ...
}
```

**Rule 3: `None` for optional scalars stays as-is.**
Go's `nil` works for pointer types, and `0`/`""` work as sentinels where Python used `None`:
```python
pos: int | None = None   # Python
```
```go
Pos int  // Go - 0 means "not set" (check call sites)
```

**Rule 4: Non-zero string defaults require call-site changes.**
Only one case: `CasePattern(terminator=";;")`
```go
// Transpiler emits the default at call sites
NewCasePattern(..., ";;")
```

**Status**: ✅ Fully analyzed. No complex cases.

## Challenge 4: Type Inference

**Problem**: Go requires explicit types. The JS transpiler doesn't emit types.

### Audit Results

| Category                         | Count     | Inferrable?                             |
| -------------------------------- | --------- | --------------------------------------- |
| Parameters missing type hints    | 2         | Yes (both obviously `Node`)             |
| Functions missing return types   | 75        | Yes (mostly `__init__` → implicit None) |
| Class attributes (in `__init__`) | 218       | Yes (from assignment RHS)               |
| Local variables (literals)       | 396 (54%) | Yes (trivial)                           |
| Local variables (method calls)   | 339 (46%) | Yes (needs signature lookup)            |

**No truly ambiguous types found.** All can be inferred mechanically.

### Type Mapping

| Python              | Go                                                 |
| ------------------- | -------------------------------------------------- |
| `str`               | `string`                                           |
| `int`               | `int`                                              |
| `bool`              | `bool`                                             |
| `list[X]`           | `[]X`                                              |
| `dict[K, V]`        | `map[K]V`                                          |
| `X \| None`         | `X` (use zero value) or `*X` (if nil-check needed) |
| `Node` (base class) | `Node` (interface)                                 |

### Transpiler Strategy

**Phase 1: Literal inference (trivial, no lookup needed)**

| Pattern                 | Inferred Type            | Count |
| ----------------------- | ------------------------ | ----- |
| `x = 0`, `x = 123`      | `int`                    | 71    |
| `x = True`, `x = False` | `bool`                   | 135   |
| `x = ""`, `x = "foo"`   | `string`                 | 88    |
| `x = []`                | `[]T` (from context)     | 73    |
| `x = {}`                | `map[K]V` (from context) | rare  |
| `x = None`              | defer to usage           | 23    |

Implementation:
```python
def infer_literal_type(node: ast.Constant) -> str:
    if isinstance(node.value, bool):
        return "bool"
    if isinstance(node.value, int):
        return "int"
    if isinstance(node.value, str):
        return "string"
    if node.value is None:
        return ""  # defer
    ...
```

**Phase 2: Constructor/call inference (needs symbol table)**

Build a symbol table during first pass:
```python
class GoTranspiler:
    def __init__(self):
        self.return_types: dict[str, str] = {}  # method_name -> return_type

    def visit_FunctionDef(self, node):
        if node.returns:
            self.return_types[node.name] = self.py_type_to_go(node.returns)
```

Then resolve calls:
```python
# x = self._parse_word()
# Look up _parse_word in return_types → "Word"
```

**Phase 3: Class attribute inference**

All 218 class attributes are assigned in `__init__` from either:
1. Parameters (type known from signature)
2. Literals (type known from value)
3. Constructor calls (type is the class name)

```python
def __init__(self, source: str):
    self.source = source      # → string (from param type)
    self.pos = 0              # → int (literal)
    self.quote = QuoteState() # → QuoteState (constructor)
```

Emit as struct fields:
```go
type Lexer struct {
    source string
    pos    int
    quote  QuoteState
}
```

**Phase 4: Empty collection element types**

For `x = []`, infer element type from first `.append()` or usage:
```python
parts = []           # type unclear
parts.append(node)   # node is Node → parts is []Node
```

Fallback: `[]interface{}` (rare, may need manual annotation).

### Edge Cases

1. **Ternary expressions**: All branches have consistent types (verified in audit)
2. **Union types `X | None`**: Use zero value where possible, pointer where nil-check matters
3. **`isinstance()` checks**: Convert to type switches

**Status**: ✅ Fully analyzed. Inference is mechanical, no AI/heuristics needed.

## Challenge 5: Method Dispatch / Polymorphism

**Problem**: Python's `node.to_sexp()` uses virtual dispatch. Go needs explicit interfaces.

**Solution**: Interface-based dispatch works naturally:

```go
func formatNode(n Node) string {
    return n.ToSexp()  // dispatches to concrete type
}
```

For type-specific handling, use type switches:

```go
switch v := n.(type) {
case *Word:
    // Word-specific
case *Command:
    // Command-specific
}
```

**Status**: Well-understood. Standard Go pattern.

## Challenge 6: Python Built-ins → Go

### Audit Results

| Operation       | Count | Go Equivalent                                                |
| --------------- | ----- | ------------------------------------------------------------ |
| `.append()`     | 564   | `x = append(x, y)`                                           |
| `len()`         | 329   | `len(x)` for slices; `utf8.RuneCountInString(s)` for strings |
| `in` operator   | 268   | `strings.Contains()` for strings; loop for slices            |
| `.join()`       | 75    | `strings.Join()` or `strings.Builder`                        |
| `.startswith()` | 28    | `strings.HasPrefix(x, s)`                                    |
| `.endswith()`   | 31    | `strings.HasSuffix(x, s)`                                    |
| `.replace()`    | 29    | `strings.ReplaceAll(x, a, b)` (chained calls common)         |
| `ord()`         | 120   | `rune(c)` or `int(c)`                                        |
| `chr()`         | 3     | `string(rune(n))`                                            |
| `getattr()`     | 19    | Type switch + optional interfaces (see Audit A)              |
| `isinstance()`  | 6     | Type switch                                                  |
| `.isalpha()`    | 11    | `unicode.IsLetter(c)`                                        |
| `.isdigit()`    | 12    | `unicode.IsDigit(c)`                                         |
| `.isalnum()`    | 19    | `unicode.IsLetter(c) \|\| unicode.IsDigit(c)`                |
| `int(s)`        | 15    | `strconv.Atoi(s)` — panic on error                           |
| `.find()`       | 11    | `strings.Index(x, s)`                                        |
| `.rfind()`      | 2     | `strings.LastIndex(x, s)`                                    |
| `.lstrip()`     | 10    | `strings.TrimLeft(x, chars)`                                 |
| `.rstrip()`     | 6     | `strings.TrimRight(x, chars)`                                |
| `.strip()`      | 6     | `strings.TrimSpace(x)`                                       |
| `.pop()`        | 5     | `x, slice = slice[len(slice)-1], slice[:len(slice)-1]`       |
| `range(n)`      | 11    | `for i := 0; i < n; i++`                                     |
| `.get()`        | 3     | `val, ok := m[key]`                                          |

### Critical Patterns

**1. String building** (most common pattern):
```python
chars = []
chars.append(c)
return "".join(chars)
```
```go
var buf strings.Builder
buf.WriteRune(c)
return buf.String()
```

**2. Chained replace**:
```python
value.replace('"', '\\"').replace("\n", "\\n")
```
```go
r := strings.NewReplacer(`"`, `\"`, "\n", "\\n")
return r.Replace(value)
```

**3. Membership test**:
```python
if c in "({[":
```
```go
if strings.ContainsAny("({[", string(c)) {
```

**4. Error-returning conversions**: `int(s)` → `strconv.Atoi(s)` returns error.
Strategy: Wrap in `mustAtoi()` that panics (matches Python behavior).

**Status**: ✅ Fully audited. All have direct Go equivalents.

## Challenge 7: String Handling

**Problem**: Parable does extensive string/byte manipulation. Python strings are Unicode, Go strings are UTF-8 byte sequences.

### Audit Results

**Parable uses CHARACTER-ORIENTED semantics throughout**, with one exception:

| Operation     | Semantics  | Go Equivalent                    |
| ------------- | ---------- | -------------------------------- |
| `source[pos]` | Character  | `[]rune(source)[pos]`            |
| `len(source)` | Characters | `utf8.RuneCountInString(source)` |
| `source[i:j]` | Characters | `string([]rune(source)[i:j])`    |
| `for c in s`  | Characters | `for _, c := range s`            |
| `ord(c)`      | Codepoint  | `rune(c)`                        |
| `chr(n)`      | Codepoint  | `string(rune(n))`                |

### Exception: ANSI-C Escape Processing

The `_expand_ansi_c_escapes()` method (lines 2222-2360) uses **byte-oriented** semantics:

```python
result = bytearray()                           # Byte buffer
result.append(ord(inner[i]))                   # Raw byte
result.extend(chr(codepoint).encode("utf-8"))  # UTF-8 encode
return result.decode("utf-8", errors="replace") # Decode with replacement
```

Go equivalent:
```go
result := make([]byte, 0)
result = append(result, byte(inner[i]))        // Raw byte
buf := make([]byte, utf8.UTFMax)
n := utf8.EncodeRune(buf, rune(codepoint))
result = append(result, buf[:n]...)            // UTF-8 bytes
return string(result)                          // Go handles invalid UTF-8
```

### Transpiler Strategy

**1. Lexer position tracking**:
Python's `self.pos` is a character offset. In Go, either:
- Convert source to `[]rune` upfront (simpler, more memory)
- Use `utf8.DecodeRuneInString()` to advance (efficient, complex)

Recommendation: Use `[]rune` for simplicity. Parable sources are typically small.

**2. String indexing**:
```python
c = self.source[self.pos]  # Python
```
```go
c := p.runes[p.pos]  // Go with rune slice
```

**3. String slicing**:
```python
_substring(s, start, end)  # Python
```
```go
string([]rune(s)[start:end])  // Go
```

**Status**: ✅ Fully audited. Clear strategy for both patterns.

## Challenge 8: Mutable State & References

**Problem**: Python passes objects by reference. Go has value vs pointer semantics.

**Key decisions**:
- Structs should probably use pointer receivers: `func (p *Parser) next()`
- Slices are already reference types (mostly fine)
- Maps are reference types (fine)

**Gap**: The JS transpiler uses `this.` liberally. Go needs explicit pointer receivers and may need `&` for taking addresses.

## Open Questions

1. **Package structure**: Single `parable.go` file or split into packages?
   - Likely single file to match JS transpiler approach

2. **Error accumulation**: Parable collects multiple parse errors. Go pattern is typically fail-fast. Keep Python's behavior or simplify?
   - Recommend: Keep panic/recover pattern, matches Go stdlib parser

3. **Testing**: How to verify transpiled Go matches Python behavior?
   - Share existing fuzz corpus, compare s-expression output

5. **`strconv.Atoi` and friends**: Python `int(s)` doesn't return errors.
   - Option A: Panic on parse failure (matches current Python behavior)
   - Option B: Wrap in must-style helper: `mustAtoi(s)`

## Remaining Research

All major audits complete. Minor items to address during implementation:

1. **Import management**: Track which Go packages are needed (`strings`, `strconv`, `unicode`, `unicode/utf8`, `fmt`)

2. **Helper functions**: Decide whether to emit inline or define helpers:
   - `mustAtoi(s)` for panicking int conversion
   - `substring(s, i, j)` for rune-based slicing (or inline `string([]rune(s)[i:j])`)

3. **Rune slice strategy**: Decide between:
   - Convert entire source to `[]rune` upfront (simple)
   - Use `utf8.DecodeRuneInString()` incrementally (memory-efficient)

## Implementation Plan

Incremental plan with clear milestones. Each increment produces runnable output. Validation gates catch problems early based on prior art learnings.

### Increment 0: Infrastructure
**Goal**: `just transpile-go` works (outputs placeholder), `just check-go` passes

- [ ] Add `--transpile-go` to `tools/transpiler/src/transpiler/__init__.py`
- [ ] Create `tools/transpiler/src/transpiler/transpile_go.py` (minimal scaffold)
- [ ] Add justfile targets:
  - `transpile-go` — runs transpiler, outputs to `src/parable.go`, runs `gofmt`
  - `check-transpile-go` — verifies `src/parable.go` matches transpiler output
  - `check-go` — runs `go build` on `src/parable.go` (fails until Increment 6)
  - `test-go` — placeholder (fails until Increment 7)
- [ ] Initial `src/parable.go` with `package parable` and `// TODO` comment
- [ ] Update `just check` to include `check-transpile-go`

**Exit criterion**: `just transpile-go && just check-transpile-go` passes

**Commit**: `git commit -m "feat(go): add transpile-go infrastructure"`

### Increment 1: Symbol Table (Multi-Pass Foundation)
**Goal**: Build complete type information before emitting any code

*Prior art lesson: py2many uses multi-stage rewriter pipeline. Single-pass emission hits ordering issues.*

- [ ] Pass 1: Collect all class names and inheritance relationships
- [ ] Pass 2: Collect all function/method signatures (params + return types)
- [ ] Pass 3: Collect all struct fields from `__init__` assignments
- [ ] Emit symbol table as JSON or debug output for validation
- [ ] Flag any types that can't be resolved (candidates for `interface{}` fallback)

**Validation gate**: Print unresolved types. If >5, investigate before proceeding.

**Exit criterion**: Symbol table covers all 63 classes, 218 struct fields, all function signatures

**Commit**: `git commit -m "feat(go): build symbol table for type resolution"`

### Increment 2: Error Types
**Goal**: `ParseError` and `MatchedPairError` compile

```go
package parable

type ParseError struct {
    Message string
    Pos     int
    Line    int
}

type MatchedPairError struct {
    ParseError
}
```

- [ ] `visit_ClassDef` for `ParseError` → struct with fields
- [ ] `visit_ClassDef` for `MatchedPairError` → struct embedding `ParseError`
- [ ] Skip all other classes (emit `// TODO: ClassName`)

**Exit criterion**: `go build src/parable.go` compiles (with unused struct warnings OK)

**Commit**: `git commit -m "feat(go): emit ParseError and MatchedPairError structs"`

### Increment 3: Node Interface & All Structs
**Goal**: All 63 structs compile (no methods yet)

- [ ] Emit `Node` interface: `type Node interface { Kind() string }`
- [ ] `visit_ClassDef` for Node subclasses → struct with fields
- [ ] Use symbol table for field types (no re-inference)
- [ ] Handle `list[X]` → `[]X`, `X | None` → `X` (zero value)

**Validation gate**: Verify all 218 struct fields have resolved Go types. Document any `interface{}` fallbacks in a tracking list.

**Exit criterion**: All 63 structs defined, `go build` compiles

**Commit**: `git commit -m "feat(go): emit all 63 struct definitions"`

### Increment 4: Helper Functions
**Goal**: Module-level functions compile

- [ ] `visit_FunctionDef` (non-method) → `func name(params) returnType`
- [ ] Parameter type emission from symbol table
- [ ] Return type emission from symbol table
- [ ] Function body as `panic("TODO")` placeholder

**Exit criterion**: `_isHexDigit`, `_isOctalDigit`, etc. have signatures, `go build` compiles

**Commit**: `git commit -m "feat(go): emit helper function signatures"`

### Increment 5: Method Signatures
**Goal**: All methods have signatures (bodies are `panic("TODO")`)

- [ ] `visit_FunctionDef` (method) → `func (r *Type) name(params) returnType`
- [ ] Convert `self` parameter to receiver
- [ ] Handle `__init__` → constructor function `NewTypeName(...)`
- [ ] Emit `Kind()` and `ToSexp()` method stubs for Node types

**Exit criterion**: All methods declared, `go build` compiles

**Commit**: `git commit -m "feat(go): emit all method signatures with stub bodies"`

### Increment 6a: Expressions & Statements (Non-String)
**Goal**: Method bodies emit real code for non-string operations

- [ ] Literals: `ast.Constant` → Go literals
- [ ] Variables: `ast.Name` → identifier (handle `self.` → `r.`)
- [ ] Binary ops: `ast.BinOp` → Go operators (handle `//` → `/`, `**` → `math.Pow`)
- [ ] Comparisons: `ast.Compare` → Go comparisons (handle chained)
- [ ] Attribute access: `ast.Attribute` → field access
- [ ] Calls: `ast.Call` → function/method calls (basic, no builtins yet)
- [ ] If/While/For: control flow statements
- [ ] Return: `ast.Return` → `return`
- [ ] Assign: `ast.Assign`, `ast.AugAssign` → variable assignment

**Exit criterion**: Bodies emit Go code for non-string operations

**Commit**: `git commit -m "feat(go): emit expressions and control flow"`

### Increment 6b: String Handling
**Goal**: String operations use correct rune semantics

*Prior art lesson: Python is character-oriented, Go is byte-oriented. This caused bugs in other transpilers.*

- [ ] Decide: `[]rune` upfront vs incremental decode (recommend `[]rune` for Lexer.source)
- [ ] `len(s)` on strings → `utf8.RuneCountInString(s)`
- [ ] `s[i]` on strings → rune access (context-dependent)
- [ ] `s[i:j]` on strings → `string([]rune(s)[i:j])`
- [ ] `for c in s` → `for _, c := range s`

**Validation gate**: Hand-verify transpiled output for `_isHexDigit` (simple) and `_expand_ansi_c_escapes` (complex, byte-oriented). These two functions exercise both string patterns.

**Exit criterion**: String-heavy functions transpile correctly

**Commit**: `git commit -m "feat(go): handle string/rune semantics"`

### Increment 6c: Builtin Dispatch Table
**Goal**: Python builtins map to Go equivalents

- [ ] `.append(x)` → `slice = append(slice, x)`
- [ ] `.join()` → `strings.Join()`
- [ ] `.startswith()` / `.endswith()` → `strings.HasPrefix()` / `strings.HasSuffix()`
- [ ] `.replace()` → `strings.ReplaceAll()` (handle chained)
- [ ] `.find()` / `.rfind()` → `strings.Index()` / `strings.LastIndex()`
- [ ] `.strip()` / `.lstrip()` / `.rstrip()` → `strings.Trim*`
- [ ] `.isalpha()` / `.isdigit()` / `.isalnum()` → `unicode.Is*`
- [ ] `ord()` / `chr()` → `rune()` / `string(rune())`
- [ ] `int(s)` → `mustAtoi(s)` (panics on error)
- [ ] `in` for strings → `strings.Contains()` / `strings.ContainsRune()`
- [ ] `in` for tuples/lists → `||` chain (at transpile time)

**Exit criterion**: All 25 builtin patterns from Challenge 6 table have mappings

**Commit**: `git commit -m "feat(go): add Python builtin dispatch table"`

### Increment 6d: Duck Typing (getattr)
**Goal**: The 19 getattr calls work via optional interfaces

*Prior art lesson: py2many explicitly punts on duck typing. This is novel territory.*

- [ ] Hand-write the 8 optional interfaces from Audit A:
  - `HasLeft`, `HasRight`, `HasExpression`, `HasOperand`
  - `HasCondition`, `HasElements`, `HasParts`, `HasKind`
- [ ] Emit interface definitions in transpiled output
- [ ] `getattr(node, "left", None)` → type assertion with ok check
- [ ] Verify against all 19 getattr call sites

**Validation gate**: Manually test each of the 19 getattr usages compiles and runs correctly.

**Exit criterion**: All getattr patterns transpile to working Go

**Commit**: `git commit -m "feat(go): implement getattr via optional interfaces"`

### Increment 6e: Exception Handling
**Goal**: `raise` and `try/except` transpile correctly

*Prior art lesson: No prior art helps here. Go stdlib parser's panic/recover is our model.*

- [ ] `raise ParseError(...)` → `panic(ParseError{...})`
- [ ] `raise MatchedPairError(...)` → `panic(MatchedPairError{...})`
- [ ] `try/except ParseError` → `defer func() { if r := recover()... }()`
- [ ] `except MatchedPairError` before `except ParseError` (subclass first)
- [ ] Handle the 4 bare `except Exception:` blocks (recover all, re-panic non-errors)

**Exit criterion**: All 7 catch sites from Audit C transpile correctly

**Commit**: `git commit -m "feat(go): implement exception handling via panic/recover"`

### Increment 6f: Remaining Type Fixes
**Goal**: `go build src/parable.go` compiles with no errors

- [ ] Import management: track and emit required imports
- [ ] f-strings → `fmt.Sprintf()` (34 cases from Audit B)
- [ ] `isinstance()` → type switch (6 cases)
- [ ] Tuple returns → multiple return values or named structs (18 functions)
- [ ] Fix remaining type mismatches iteratively
- [ ] Any `interface{}` fallbacks: document in tracking list

**Exit criterion**: `go build src/parable.go` exits 0

**Commit**: `git commit -m "feat(go): fix remaining type errors, parable.go compiles"`

### Increment 7: Test Parity
**Goal**: `just test-go` passes same tests as Python/JS

- [ ] Create `tests/bin/run-go-tests.go` (mirrors `run-js-tests.js`)
- [ ] Export `Parse()` function matching Python's `parse()`
- [ ] Export `ParseError` for test runner
- [ ] Run against `.tests` corpus, compare s-expression output
- [ ] Fix semantic bugs until test parity achieved

**Exit criterion**: `just test-go` passes, same pass/fail as `just test`

**Commit**: `git commit -m "feat(go): add Go test runner, achieve test parity"`

### Increment 8: Integration
**Goal**: Go transpiler is part of standard workflow

- [ ] Add `just transpile` to run all three (js, dts, go)
- [ ] Add `check-transpile-go` to `just check`
- [ ] Add `test-go` to `just check`
- [ ] Documentation updates

**Exit criterion**: `just check` includes Go, CI passes

**Commit**: `git commit -m "feat(go): integrate Go transpiler into CI"`

---

### Fallback Tracking

When type inference fails, emit `// parable:fixme TYPE` comment and track here:

| Location | Issue | Resolution |
|----------|-------|------------|
| *(none yet)* | | |

## References

- [Go AST package](https://pkg.go.dev/go/ast) - Node interface pattern
- [Go parser source](https://go.dev/src/go/parser/parser.go) - bailout/recover pattern
- [Eli Bendersky - Struct embedding](https://eli.thegreenplace.net/2020/embedding-in-go-part-1-structs-in-structs/)
- [Panic/Recover wiki](https://go.dev/wiki/PanicAndRecover)
- [Functional options pattern](https://charlesxu.io/go-opts/)
- [py2many](https://github.com/py2many/py2many) - Multi-target Python transpiler (Go in beta)

---

## Deep-Dive Audits

### Audit A: getattr Duck-Typing Pattern

The original document claimed getattr uses "struct field access (no reflection needed)". This is **incorrect**. The 19 getattr calls implement duck-typing across heterogeneous node types.

**Usage pattern** (lines 2998-3038, 3039-3055):
```python
# Accessing optional attributes that only exist on some node types
node_kind = getattr(node, "kind", None)
left = getattr(node, "left", None)
expression = getattr(node, "expression", None)
```

**Attribute → Node types that have it:**

| Attribute    | Node Classes                                                                               |
| ------------ | ------------------------------------------------------------------------------------------ |
| `kind`       | All Node subclasses (via base class)                                                       |
| `left`       | ArithBinaryOp, ArithComma, BinaryTest, CondAnd, CondOr                                     |
| `right`      | ArithBinaryOp, ArithComma, BinaryTest, CondAnd, CondOr                                     |
| `expression` | ArithmeticExpansion, ArithmeticCommand, ArithEscape                                        |
| `operand`    | ArithUnaryOp, ArithPreIncr, ArithPostIncr, ArithPreDecr, ArithPostDecr, UnaryTest, CondNot |
| `condition`  | If, While, Until, ArithTernary                                                             |
| `elements`   | Array                                                                                      |
| `parts`      | Word                                                                                       |

**Bug found**: Lines 3028-3035 access `true_value` and `false_value`, but ArithTernary uses `if_true` and `if_false`. These getattr calls always return None (dead code).

**Go strategy**: Define optional accessor interfaces:
```go
type HasLeft interface { Left() Node }
type HasExpression interface { Expression() Node }

func collectCmdsubs(node Node) []Node {
    if v, ok := node.(HasLeft); ok {
        result = append(result, collectCmdsubs(v.Left())...)
    }
    // ...
}
```

### Audit B: F-String Patterns

**39 f-strings found.** Categorized by complexity:

| Category                     | Count | Example                                 | Go Strategy                    |
| ---------------------------- | ----- | --------------------------------------- | ------------------------------ |
| Simple substitution          | 31    | `f"Parse error at position {self.pos}"` | `fmt.Sprintf("... %d", p.pos)` |
| Repr format `!r`             | 3     | `f"Token({self.type}, {self.value!r})"` | `fmt.Sprintf("... %q", ...)`   |
| Nested braces (set literals) | 5     | `{"elif", "else", "fi"}`                | Not f-strings, false positive  |

**Actual f-strings requiring transpilation: 34**

All are simple `%s`/`%d`/`%q` patterns. No complex expressions inside braces.

### Audit C: Exception Flow

**Two error types:**
- `ParseError(Exception)` — main parse error (92 raise sites)
- `MatchedPairError(ParseError)` — subclass for matched-pair failures (8 raise sites)

**Catch patterns:**

| Pattern                         | Count | Lines                  | Purpose                                  |
| ------------------------------- | ----- | ---------------------- | ---------------------------------------- |
| `except MatchedPairError as e:` | 1     | 1976                   | Re-raise after cleanup                   |
| `except ParseError as e:`       | 1     | 7723                   | Capture for error recovery               |
| `except ParseError:`            | 1     | 7869                   | Silent fallback                          |
| `except Exception:`             | 4     | 1989, 3233, 3383, 3450 | Fallback formatting on sub-parse failure |

**Go strategy**:
```go
type MatchedPairError struct { ParseError }  // Embed for "inheritance"

defer func() {
    if r := recover(); r != nil {
        switch e := r.(type) {
        case MatchedPairError:
            // handle specifically
        case ParseError:
            // handle base type
        default:
            panic(r)  // re-panic unknown
        }
    }
}()
```

**Concern**: The 4 bare `except Exception:` blocks catch ALL exceptions including bugs. In Go, these `recover()` calls will catch all panics. Need to be careful not to swallow programming errors.

### Audit D: `in` Operator Breakdown

**268 total `in` usages.** Categorized:

| Pattern                     | Count | Go Equivalent                   | Cost                 |
| --------------------------- | ----- | ------------------------------- | -------------------- |
| `c in "string_literal"`     | 38    | `strings.ContainsRune(lit, c)`  | O(n) but n is small  |
| `x not in "string_literal"` | 14    | `!strings.ContainsRune(lit, c)` | O(n) but n is small  |
| `x in (tuple_literal)`      | 15    | Multi-condition `\|\|`          | O(1)                 |
| `x in [list_literal]`       | 11    | Multi-condition `\|\|`          | O(1)                 |
| `x in set_literal`          | ~5    | Map lookup or `\|\|` chain      | O(1)                 |
| `x in self.field`           | 17    | Depends on field type           | Varies               |
| `for x in iterable`         | ~168  | `for _, x := range iterable`    | N/A (not membership) |

**Most `in` usages are iteration, not membership.** The ~83 membership tests are:
- 52 against string literals (cheap, strings are short like `"({["`)
- 26 against tuple/list literals (convert to `||` chain at transpile time)
- 5 against set literals (use map or `||` chain)

**No performance concern.** All membership tests are against small constant collections.

### Audit E: Tuple Returns and Unpacking

**18 functions return typed tuples** (`-> tuple[...]`):

| Return Type                | Count | Functions                                                 |
| -------------------------- | ----- | --------------------------------------------------------- |
| `tuple[Node \| None, str]` | 12    | `_read_ansi_c_quote`, `_parse_command_substitution`, etc. |
| `tuple[str, bool]`         | 2     | `_parse_heredoc_delimiter`, etc.                          |
| `tuple[int, int]`          | 1     | `_skip_matched_pair` helper                               |
| `tuple[bool, str]`         | 1     | `_line_matches_delimiter`                                 |
| `tuple[str, int]`          | 1     | `_read_heredoc_line`                                      |
| `tuple[int, str] \| None`  | 1     | `_lex_peek_operator`                                      |

**Go strategy**: Use named struct types for readability:
```go
type parseResult struct {
    node Node
    text string
}

func (p *Parser) parseCommandSubstitution() parseResult {
    // ...
    return parseResult{node, text}
}
```

Or use multiple return values directly:
```go
func (p *Parser) parseCommandSubstitution() (Node, string) {
    return node, text
}
```

**Stack tuple unpacking** (line 325):
```python
self.single, self.double = self._stack.pop()
```

The `_stack` contains `(bool, bool)` tuples. Go equivalent:
```go
type quotePair struct { single, double bool }
// ...
pair := qs.stack[len(qs.stack)-1]
qs.stack = qs.stack[:len(qs.stack)-1]
qs.single, qs.double = pair.single, pair.double
```

### Audit F: Node Class Inventory

**63 total classes** in parable.py:

| Category       | Count | Examples                                                 |
| -------------- | ----- | -------------------------------------------------------- |
| Error types    | 2     | ParseError, MatchedPairError                             |
| Internal state | 8     | TokenType, Token, QuoteState, Lexer, Parser, etc.        |
| AST Node types | 53    | Word, Command, Pipeline, If, While, ParamExpansion, etc. |

All 53 Node subclasses need Go struct definitions.

---

## Prior Art Research

Examined three Python-to-Go transpilation approaches (January 2026):

### py2many (Active, Multi-target)

**Relevance: Medium.** Most applicable to our use case.

| Aspect | Approach | Applicability |
|--------|----------|---------------|
| Type inference | Requires annotations; falls back to `interface{}` | Partial - Parable is fully annotated |
| Exceptions | Only `assert` → `panic()`; no try/except | None - need custom handling |
| Builtins | Dispatch table (`DISPATCH_MAP`) | High - adoptable pattern |
| Duck typing | Explicitly unsupported | None |

**Patterns worth adopting:**
1. **Multi-stage rewriter pipeline** - AST passes for different concerns (visibility, ternary elimination, etc.)
2. **Dispatch tables** - Clean mapping of Python builtins to Go equivalents
3. **Graceful degradation** - Emit comments for untranslatable constructs rather than failing
4. **IfExp rewriter** - Go has no ternary; rewrite `x if cond else y` to if-statement

### Grumpy (Google, Abandoned)

**Relevance: Low.** Fundamentally different goal.

Grumpy preserved full Python semantics via a heavyweight runtime where all values were `*Object` with dynamic dispatch through slot tables. This is the opposite of our goal (idiomatic, statically-typed Go).

**One notable pattern:** Error returns `(*Object, *BaseException)` instead of panic/recover. Every function returned an error tuple, with control flow implemented via loops and `continue`. More verbose but avoids panic overhead.

**Why abandoned:** Python 2 only, no C extensions, ~50% CPython performance, incomplete stdlib.

### pytype (Google, Type Analyzer)

**Relevance: Low** for inference, but educational.

Pytype uses forward dataflow analysis where types *widen* (accumulate unions), not narrow from usage. This means:
- `x = None` followed by `x = Foo()` yields `None | Foo`, not `Foo`
- No backward inference from how a variable is used

**Does NOT help** with the 23 "defer to usage" None cases. However, their empty collection handling (inferring element type from `.append()` calls via `merge_instance_type_parameter`) validates our proposed approach.

### Implications for Parable Transpiler

1. **Type inference claim revised**: "All types mechanically inferrable" is optimistic. Plan for `interface{}` fallback in edge cases, with manual annotation override.

2. **Duck typing (getattr) remains unsolved** by prior art. The optional-interface approach in Audit A is novel but appears necessary.

3. **Exception handling**: No prior art helps. Go stdlib parser's panic/recover pattern remains best precedent.

4. **Architecture**: Adopt py2many's multi-stage rewriter pipeline rather than single-pass emission.

---

*Last updated: 2026-01-24*

**Audits completed:**
- Optional parameters: 33 functions analyzed
- Type annotations: 735 local vars, 218 class attrs
- String semantics: character-oriented (except ANSI-C escapes)
- Python builtins: 1,500+ usages catalogued across 25 operations
- getattr duck-typing: 19 usages across 8 optional attributes
- F-strings: 34 actual f-strings, all simple substitutions
- Exception flow: 2 error types, 7 catch sites
- `in` operator: 268 usages, ~83 membership tests (all cheap)
- Tuple returns: 18 functions, all convertible to Go multiple returns or structs
