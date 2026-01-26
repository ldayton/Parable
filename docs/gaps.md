# IR Specification Gaps

Areas requiring additional specification, based on analysis of `parable.py` (~11,000 lines, ~60 AST node types).

| Pri | Gap                             | Issue                                    |
| --- | ------------------------------- | ---------------------------------------- |
| P2  | Union Type Details              | Frontend discovery algorithm             |
| P2  | Class to Struct Extraction      | Field source: annotation vs `__init__`   |
| P2  | Optional vs Nullable vs Default | Three concepts conflated in Python       |

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
