# IR Specification Gaps

Areas requiring additional specification, based on analysis of `parable.py` (~11,000 lines, ~60 AST node types).

## Priority 0 — Blocking

### Type Narrowing via `.kind` Field

parable.py uses `if node.kind == "command":` patterns extensively (~100+ occurrences). The IR spec mentions `TypeSwitch` but doesn't specify:

1. **Chain coalescing**: How consecutive `if/elif` on same variable become one `TypeSwitch`
2. **Reassignment invalidation**: Does `node = other` inside a branch invalidate narrowing?
3. **Nested conditions**: `if node.kind == "list" and node.parts:` — narrowing + truthiness combined
4. **Fall-through detection**: When `elif` has no `else`, is default case empty or error?

```python
# Source pattern
if node.kind == "command":
    process(node.words)      # node narrowed to Command
elif node.kind == "pipeline":
    process(node.commands)   # node narrowed to Pipeline
```

**Needed**: Specify detection algorithm. Define how `.kind` string constants map to struct types.

### Truthiness Semantics in Practice

The spec defines four patterns but parable.py uses variations:

| Pattern in parable.py   | Type           | Current Spec | Gap                                                |
| ----------------------- | -------------- | ------------ | -------------------------------------------------- |
| `if self._stack:`       | `list[tuple]`  | `len(x) > 0` | ✓ covered                                          |
| `if parts:`             | `list[Node]`   | `len(x) > 0` | ✓ covered                                          |
| `if chars:`             | `list[str]`    | `len(x) > 0` | ✓ covered                                          |
| `if self.word:`         | `Word \| None` | `IsNil`      | ✓ covered                                          |
| `if hex_str:`           | `str`          | `!= ""`      | ✓ covered                                          |
| `if bracket_start_pos:` | `int \| None`  | ?            | **Gap**: `0` is falsy in Python but valid position |

**Needed**: Clarify `int | None` truthiness. Recommend explicit `is not None` in source style guide, or specify how frontend detects this ambiguity.

### Two-Phase Return Pattern

Many parsing methods return `tuple[Node | None, str]` — the parsed node plus raw text consumed:

```python
def _parse_command_substitution(self) -> tuple[Node | None, str]:
    ...
    return (CommandSubstitution(cmd), raw_text)
    # or
    return (None, "")  # soft failure
```

**Current IR gap**: No representation for multi-value returns. Options:

| Strategy      | Go                        | Rust                     | TS                       | C                         |
| ------------- | ------------------------- | ------------------------ | ------------------------ | ------------------------- |
| Tuple return  | `(Node, string)`          | `(Option<Node>, String)` | `[Node \| null, string]` | out-param                 |
| Result struct | `ParseResult{Node, Text}` | `ParseResult`            | `ParseResult`            | `ParseResult*`            |
| Out parameter | `parse(..., &text)`       | `parse(..., &mut text)`  | N/A                      | `parse(..., char** text)` |

**Needed**: Add `TupleType` to IR, or specify struct-wrapping convention for multi-returns.

## Priority 1 — Important

### Default Parameter Strategy Selection

parable.py uses several default patterns:

```python
def __init__(self, parts: list[Node] | None = None):    # None → empty list
def _parse_param_expansion(self, in_dquote: bool = False):  # bool default
def __init__(self, param: str, op: str | None = None, arg: str | None = None):  # multiple optional
```

The spec lists Go strategies but not selection criteria:

| Pattern                    | Detection                       | Go Strategy                   |
| -------------------------- | ------------------------------- | ----------------------------- |
| `bool = False`             | Type is bool, default is False  | Omit param (zero value)       |
| `T \| None = None`         | Optional with None default      | Omit param (nil zero value)   |
| `list \| None = None`      | Optional list, None means empty | Omit param, caller passes nil |
| Multiple trailing optional | 2+ optional params              | Options struct                |

**Needed**: Formalize detection rules. Handle `list[T] | None = None` where `None` means "use empty list" (common in `__init__`).

### Error Type Mapping

parable.py defines:

```python
class ParseError(Exception):
    def __init__(self, message: str, pos: int | None = None, line: int | None = None):

class MatchedPairError(ParseError):  # inheritance
```

**Gaps**:
1. Exception inheritance → how represented? Go: separate types? Rust: enum variants?
2. Optional fields `pos`, `line` → always present in IR error type, or Optional?
3. `_format_message()` method on error → include in IR or backend-generate?

**Needed**: Specify error type definition in IR. Clarify inheritance flattening.

### Name Mangling Rules

| Python                | Unclear Mapping                                            |
| --------------------- | ---------------------------------------------------------- |
| `_parse_matched_pair` | Go: `parseMatchedPair` (unexported) or `ParseMatchedPair`? |
| `ArithBinaryOp`       | Go: `ArithBinaryOp` or `ArithBinaryOP`?                    |
| `_is_hex_digit`       | Go: `isHexDigit`? Rust: `is_hex_digit`?                    |
| `PST_CASEPAT`         | Constant: `PstCasepat`? `PST_CASEPAT`?                     |
| `__init__`            | Constructor — omit from method list                        |

**Needed**: Explicit rules for:
- Leading underscore → unexported (Go), `pub(crate)` (Rust)
- Acronyms: `HTTP`, `EOF`, `AST` — preserve or capitalize?
- Double underscore (`__init__`, `__repr__`) → skip or transform?
- ALL_CAPS constants → `const` block with same names

## Priority 2 — Needed

### Union Type Details

parable.py explicitly defines:

```python
ArithNode = Union[ArithNumber, ArithEmpty, ArithVar, ...]  # 17 variants
CondNode = Union[UnaryTest, BinaryTest, CondAnd, CondOr, CondNot, CondParen]  # 6 variants
```

All nodes have `kind: str` field set in `__init__`.

**Gaps**:
1. How does frontend discover these Union definitions? Scan for `= Union[...]`?
2. Exhaustiveness: If TypeSwitch on `ArithNode` misses `ArithEmpty`, error or warning?
3. `.kind` generation: Derived from class name (`ArithBinaryOp` → `"binary-op"`)? Explicit in source?

**Needed**: Specify Union discovery. Document `.kind` string convention (parable.py uses kebab-case: `"binary-op"`, `"pre-incr"`).

### Class to Struct Extraction

Node classes follow consistent pattern:

```python
class ParamExpansion(Node):
    param: str                    # class-level annotation
    op: str | None = None         # with default
    arg: str | None = None

    def __init__(self, param: str, op: str | None = None, arg: str | None = None):
        self.kind = "param"       # always first
        self.param = param        # field assignment
        self.op = op
        self.arg = arg

    def to_sexp(self) -> str:     # method
        ...
```

**Extraction rules needed**:
1. Class-level annotations → struct fields (some classes use these, some don't)
2. `__init__` assignments → struct fields (authoritative)
3. `self.kind = "..."` → discriminator, not a field
4. Methods → separate from struct, attached via receiver

### Optional vs Nullable vs Default

Three distinct concepts conflated in Python:

```python
op: str | None = None      # nullable AND has default
arg: str | None            # nullable, no default (must be provided)
parts: list[Node] = []     # not nullable, has default (mutable default antipattern)
```

**Needed**: Distinguish in IR:
- `Optional(T)` — nullable, no default
- `Optional(T)` with `default` on Param/Field — nullable with default
- Non-optional with `default` — not nullable but has default

## Priority 3 — Nice to Have

### Stateful Helper Classes

parable.py has internal state classes:

```python
class QuoteState:
    def __init__(self):
        self.single = False
        self.double = False
        self._stack: list[tuple[bool, bool]] = []

    def push(self) -> None: ...
    def pop(self) -> None: ...
    def in_quotes(self) -> bool: ...
```

These are mutable structs with methods. Not AST nodes, not public API.

**Consideration**: Mark as internal? Emit as struct + free functions? Preserve method style?

### Enum-Like Constant Classes

```python
class TokenType:
    EOF = 0
    WORD = 1
    NEWLINE = 2
    SEMI = 10
    ...
```

**Target mapping**:
- Go: `const` block with `TokenType` prefix (`TokenTypeEOF = 0`)
- Rust: `enum TokenType { EOF = 0, ... }` or `mod token_type { pub const EOF: i32 = 0; }`
- TS: `enum TokenType { EOF = 0, ... }`
- C: `enum token_type { TOKEN_TYPE_EOF = 0, ... }`

### String Building Pattern

Common pattern for building strings:

```python
chars: list[str] = []
while ...:
    chars.append(ch)
return "".join(chars)
```

**Optimization opportunity**: Detect this pattern and emit:
- Go: `strings.Builder`
- Rust: `String::with_capacity` + `push`/`push_str`
- C: arena-allocated growing buffer

## Not Applicable

These gaps from initial analysis don't apply to parable.py:

| Gap                     | Why N/A                                      |
| ----------------------- | -------------------------------------------- |
| Ownership inference     | Strict tree structure, no cycles, arena fits |
| Closure captures        | No lambdas in codebase                       |
| Incremental compilation | Single-file parser                           |
| Complex method dispatch | Concrete types, no interface polymorphism    |

## Observations Not in Spec

Patterns found that may need IR support:

1. **Position syncing**: `_sync_to_parser()` / `_sync_from_parser()` — lexer/parser share position
2. **Circular references**: `Lexer._parser: Parser | None` — careful in Rust/C ownership
3. **Heavy indexing**: `self.source[self.pos]` — bounds checking strategy per backend
4. **Bitwise flags**: `flags & MatchedPairFlags.DQUOTE` — emit as-is or use typed flags?

---

## Research: Type Narrowing

Background research on implementing type narrowing for the P0 gap.

### Prior Art

| System | Approach | Key Paper/Doc |
|--------|----------|---------------|
| TypeScript | Control flow analysis with type guards | [PR #8010](https://github.com/Microsoft/TypeScript/pull/8010) |
| mypy | Binder with frame-based tracking | [binder.py](https://github.com/python/mypy/blob/master/mypy/binder.py) |
| Typed Racket | Occurrence typing | [ICFP 2010](https://www2.ccs.neu.edu/racket/pubs/icfp10-thf.pdf) |
| Rust | Pattern matrix usefulness algorithm | [rustc-dev-guide](https://rustc-dev-guide.rust-lang.org/pat-exhaustive-checking.html) |

### TypeScript's Control Flow Analysis

TypeScript introduced CFA in 2016. Key design:

1. **Narrowed type computation**: Start with declared type, follow each code path, narrow based on type guards and assignments
2. **Type guards**: `typeof`, `instanceof`, equality checks, truthiness, `in` operator, user-defined guards
3. **Join points**: When paths merge (after if/else), compute union of narrowed types
4. **Discriminated unions**: Object with literal `.kind` field enables narrowing in switch/case

```typescript
// TypeScript narrows automatically
interface Dog { kind: "dog"; bark(): void }
interface Cat { kind: "cat"; meow(): void }
type Pet = Dog | Cat;

function handle(pet: Pet) {
    if (pet.kind === "dog") {
        pet.bark();  // pet narrowed to Dog
    }
}
```

### mypy's Binder

mypy uses a **frame-based** approach:

1. **Frame**: Snapshot of type bindings at a program point
   - `types: dict[Key, Type]` — narrowed types for expressions
   - `unreachable: bool` — dead code detection
2. **Operations**:
   - `put()` — direct narrowing from isinstance/type guards
   - `assign_type()` — narrowing through assignment
   - `update_from_options()` — merge types at join points
3. **Key insight**: Only track "literal hashable" expressions (names, attributes, subscripts)

### Rust's Exhaustiveness Checking

Rust uses a **pattern matrix** algorithm:

1. **Usefulness**: Is pattern `q` useful given patterns `p_1..p_n`? (matches something new)
2. **Specialization**: Remove one layer of constructor, recurse on fields
3. **Constructor splitting**: Group infinite constructors (integers) into ranges
4. **Exhaustiveness**: Check if wildcard `_` is useful — if yes, match is non-exhaustive

Complexity: NP-complete (encodes SAT), but constructor splitting makes practical cases fast.

### Existing Transpiler Implementation

The Go transpiler already handles narrowing via two mechanisms:

**1. isinstance chains → type switch** (`go_emit_expr.py:1985`):
```python
# Detection: _collect_isinstance_chain() finds if/elif isinstance(x, T)
# Emission: switch v := x.(type) { case *T: ... }
```

**2. .kind checks → type assertion** (`go_emit_stmt.py:589`):
```python
# Detection: _detect_kind_check() finds x.kind == "literal"
# Emission: if v, ok := x.(*Type); ok { ... }
```

**Type context tracking** (`_type_switch_var`, `_type_switch_type`):
- Tracks `(original_var, narrowed_var)` tuple during switch body
- Rewrites variable references to use narrowed name
- Maintains `var_types` map for field access resolution

### Recommended IR Approach

Based on research, the IR should support:

**1. TypeSwitch node** (already exists):
```
TypeSwitch {
    expr: Expr
    binding: string        # narrowed variable name
    cases: [TypeCase]
    default: [Stmt]
}
```

**2. Frontend responsibilities**:
- Detect `if/elif` chains on same variable with `.kind` or `isinstance` checks
- Coalesce into single `TypeSwitch`
- Track narrowed type in scope for body statements
- Invalidate narrowing on reassignment to switched variable

**3. Detection algorithm** (formalize existing transpiler logic):
```
def detect_type_switch(stmt: If) -> TypeSwitch | None:
    cases = []
    current = stmt
    while current:
        if is_kind_check(current.test) or is_isinstance_check(current.test):
            var, type = extract_check(current.test)
            if cases and cases[0].var != var:
                break  # Different variable, stop
            cases.append((type, current.body))
            current = current.orelse[0] if len(current.orelse) == 1 and isinstance(current.orelse[0], If) else None
        else:
            break
    if len(cases) >= 2:
        return TypeSwitch(var, cases, current.orelse if current else [])
    return None
```

**4. Exhaustiveness** (P2, not blocking):
- For closed unions (explicit `Union[A, B, C]`), warn if case missing
- For open interfaces, no exhaustiveness check
- Implementation: Compare case types against union variants

### Open Questions

1. **Compound conditions**: `if x.kind == "a" and x.field:` — narrow first, then check field?
2. **Or patterns**: `if x.kind == "a" or x.kind == "b":` — emit union case `case *A, *B:`?
3. **Negation**: `if x.kind != "a":` — narrow to union-minus-A? (complex)
4. **Nested switches**: TypeSwitch inside TypeSwitch case — straightforward, just scope

### References

- [TypeScript Narrowing Docs](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [mypy Type Narrowing Docs](https://mypy.readthedocs.io/en/stable/type_narrowing.html)
- [Rust Pattern Analysis](https://doc.rust-lang.org/beta/nightly-rustc/rustc_pattern_analysis/usefulness/index.html)
- [Occurrence Typing (Typed Racket)](https://docs.racket-lang.org/ts-guide/occurrence-typing.html)
- [Flow Typing Comparison](https://ayazhafiz.com/articles/22/why-dont-more-languages-offer-flow-typing)
- [If-T Benchmark](https://arxiv.org/pdf/2508.03830) — compares TypeScript, Flow, mypy, Pyright
