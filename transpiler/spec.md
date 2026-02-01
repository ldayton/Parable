# Tongues Specification

Tongues is a transpiler for a well-behaved subset of Python. Programs in this subset are valid Python—they execute normally with CPython, work with standard IDEs, debuggers, test frameworks, and tooling. The subset trades dynamic flexibility for compile-time guarantees: all types are known, all calls resolve statically, all ownership is inferrable. This enables generation of idiomatic output in multiple target languages from a single source —- all without shipping a runtime dependency.

Sequential pipeline with clean phase boundaries. Each phase completes before the next starts.

## Design Principles

- **Sequential**: Each phase completes fully before the next starts
- **Monotonic**: Phase N reads outputs of phases 1..N-1; invariants accumulate
- **Fail fast**: Reject bad input at the earliest possible phase
- **Self-hosting**: Tongues can transpile itself; the compiler is written in the subset it accepts

## Supported Output Languages

| Language | Role   | Reference            |
| -------- | ------ | -------------------- |
| C        | target | C11 (clang 18)       |
| Go       | target | Go 1.23              |
| Java     | target | OpenJDK 21           |
| Python¹  | source | CPython 3.12         |
| Rust     | target | rustc (2021 edition) |

¹ Output Python reintroduces idioms that the subset input banned

## Supported Types

| Type       | Syntax                                 | Notes                       |
| ---------- | -------------------------------------- | --------------------------- |
| Primitives | `int`, `float`, `str`, `bool`, `bytes` | `bytes` for binary I/O      |
| Optional   | `T \| None`                            | Nullable types              |
| Union      | `A \| B \| C`                          | Discriminated by type       |
| List       | `list[T]`                              | Bare `list` banned          |
| Dict       | `dict[K, V]`                           | Bare `dict` banned          |
| Set        | `set[T]`                               | Bare `set` banned           |
| Tuple      | `tuple[A, B, C]`                       | Fixed-length, heterogeneous |
| Callable   | `Callable[[A, B], R]`                  | Function types; bound methods include receiver |

## Overview

| Phase | Stage     | Module          | Description                                         |
| :---: | --------- | --------------- | --------------------------------------------------- |
|   1   | cli       | `cli.py`        | Parse arguments, read input, invoke pipeline        |
|  1.5  | frontend  | `__init__.py`   | Orchestrate phases 2–9                              |
|   2   | frontend  | `parse.py`      | Tokenize and parse source; produce dict-based AST   |
|   3   | frontend  | `subset.py`     | Reject unsupported Python features early            |
|   4   | frontend  | `names.py`      | Scope analysis and name binding                     |
|   5   | frontend  | `signatures.py` | Type syntax parsing and kind checking               |
|   6   | frontend  | `fields.py`     | Dataflow over `__init__`; infer field types         |
|   7   | frontend  | `hierarchy.py`  | Class hierarchy; subtyping relations                |
|   8   | frontend  | `inference.py`  | Bidirectional type inference (↑synth / ↓check)      |
|   9   | frontend  | `lowering.py`   | Type-directed elaboration to IR                     |
|  9.5  | middleend | `__init__.py`   | Orchestrate phases 10–14                            |
|  10   | middleend | `scope.py`      | Variable declarations, reassignments, modifications |
|  11   | middleend | `returns.py`    | Return pattern analysis                             |
|  12   | middleend | `liveness.py`   | Unused values, catch vars, bindings                 |
|  13   | middleend | `hoisting.py`   | Variables needing hoisting for Go emission          |
|  14   | middleend | `ownership.py`  | Ownership inference and escape analysis             |
|  15   | backend   | `<lang>.py`     | Emit target language source from annotated IR       |

## CLI (Phase 1)

#### Phase 1: `cli.py`

Program entry point. Parses command-line arguments, reads source input, invokes the compilation pipeline, writes output. Written in the Tongues subset—uses only allowed I/O primitives (stdin/stdout/stderr, no file I/O).

| Responsibility      | Implementation                                                       |
| ------------------- | -------------------------------------------------------------------- |
| Argument parsing    | Manual `sys.argv` processing (no argparse)                           |
| Source input        | `sys.stdin.read()`                                                   |
| Target selection    | `--target` flag: `go`, `rust`, `c`, `java`, `py`                     |
| Output              | `print()` to stdout                                                  |
| Error reporting     | `print(..., file=sys.stderr)` with exit code                         |
| Pipeline invocation | Call `frontend.compile()` → `middleend.analyze()` → `backend.emit()` |

**Usage:**

```
tongues [OPTIONS] < input.py > output.go

Options:
  --target TARGET   Output language: go, rust, c, java, py (default: go)
  --verify          Check subset compliance only, no codegen
  --help            Show this help message
```

File redirection is handled by the shell; the transpiler itself only uses stdin/stdout.

**Postconditions:** Source read from stdin; target language selected; pipeline invoked; output written to stdout or error reported to stderr with non-zero exit.

## Frontend (Phases 2–9)

| Module          | Knows types? | Knows IR? | Output                                |
| --------------- | :----------: | :-------: | ------------------------------------- |
| `parse.py`      |      no      |    no     | dict-based AST                        |
| `subset.py`     |      no      |    no     | (rejects bad input or passes through) |
| `names.py`      |      no      |    no     | NameTable { name → kind }             |
| `signatures.py` | yes (parse)  |    no     | SigTable { func → (params, ret) }     |
| `fields.py`     | yes (infer)  |    no     | FieldTable { class → [(name, type)] } |
| `hierarchy.py`  |  yes (sub)   |    no     | SubtypeRel { class → ancestors }      |
| `inference.py`  | yes (bidir)  |    no     | TypedAST (↑synth / ↓check / narrow)   |
| `lowering.py`   | yes (narrow) |    yes    | IR Module                             |

#### Phase 1.5: `frontend/__init__.py`

Orchestrate phases 2–9. Initialize empty context tables, invoke each phase, thread outputs forward.

#### Phase 2: `frontend/parse.py`

Tokenize source code and parse into dict-based AST. Enables self-hosting by removing CPython bootstrap dependency.

| Component      | Lines | Description                                      |
| -------------- | ----- | ------------------------------------------------ |
| `tokenize.py`  | ~350  | While-loop state machine; returns `list[Token]`  |
| `grammar.py`   | ~250  | Pre-compiled DFA tables as static data           |
| `parse.py`     | ~175  | LR shift-reduce parser; stack-based              |
| `ast_build.py` | ~250  | Grammar rules → dict nodes matching `ast` module |

The tokenizer uses explicit `while i < len(...)` loops (no generators). Grammar tables are pre-compiled under CPython once, then embedded as data. The parser is a simple stack machine consuming tokens and emitting dict-based AST nodes.

The restricted subset eliminates major parsing pain points:

| Constraint               | Simplification                                     |
| ------------------------ | -------------------------------------------------- |
| f-strings: `{expr}` only | No `!conversion`, no `:format_spec`                |
| No generators            | Tokenizer returns `list[Token]`, not lazy iterator |
| No nested functions      | No closure/scope tracking during parse             |
| Walrus operator          | `x := expr` allowed; scopes to enclosing function  |
| No async/await           | No context-dependent keyword handling              |
| Single grammar version   | No version switching; one static grammar           |

**Postconditions:** Source code parsed to dict-based AST; structure matches `ast.parse()` output; all tokens consumed; syntax errors reported with line/column.

**Prior art:** [Dragon Book Ch. 3-4](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools), [pgen2](https://github.com/python/cpython/tree/main/Parser/pgen), [parso](https://github.com/davidhalter/parso)

#### Phase 3: `frontend/subset.py`

Reject unsupported Python features early. If verification passes, downstream phases can assume:

| Invariant                 | What it enables                                               |
| ------------------------- | ------------------------------------------------------------- |
| No dynamic dispatch       | Call graph is static; all calls resolve at compile time       |
| No runtime introspection  | No `getattr`/`setattr`/`__dict__` — field access is static    |
| No closures               | No nested functions — all functions are top-level or methods  |
| Eager iteration only      | Comprehensions and generators must be statically eager        |
| All types annotated       | Signatures have types; inference only needed for locals       |
| No bare collections       | `list[T]` not `list` — element types always known             |
| Single inheritance        | Class hierarchy is a tree, not a DAG                          |
| `@dataclass` only         | No arbitrary decorators; `@dataclass` (no args) allowed       |
| No mutable defaults       | Default args are immutable; no shared-state bugs              |
| Static imports            | Only `typing`, `__future__`, `collections.abc`, `dataclasses` |
| No back-references        | Fields cannot reference their container (no cycles)           |
| No borrowed field storage | Parameters cannot be stored in fields without copy            |
| Immutable string params   | String parameters are borrowed; copy if storing               |

**Allowed built-in functions:**

| Category    | Functions                                                    |
| ----------- | ------------------------------------------------------------ |
| Math        | `abs`, `min`, `max`, `sum`, `round`, `divmod`, `pow`         |
| Conversion  | `int`, `float`, `str`, `bool`, `bytes`, `chr`, `ord`         |
| Collections | `list`, `dict`, `set`, `tuple`, `frozenset`, `len`, `sorted` |
| Type check  | `isinstance`                                                 |
| Iteration   | `range`, `enumerate`, `zip`                                  |
| Formatting  | `repr`, `ascii`, `bin`, `hex`, `oct`                         |
| Boolean     | `all`, `any`                                                 |
| Other       | `slice`, `super`, `object`                                   |

**Allowed methods:**

| Type   | Methods                                                                                                                                                                                         |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `str`  | `join`, `split`, `strip`, `lstrip`, `rstrip`, `lower`, `upper`, `startswith`, `endswith`, `replace`, `find`, `rfind`, `count`, `isalnum`, `isalpha`, `isdigit`, `isspace`, `isupper`, `islower` |
| `list` | `append`, `extend`, `pop`, `insert`, `remove`, `copy`, `clear`, `index`, `count`, `reverse`, `sort`                                                                                             |
| `dict` | `get`, `keys`, `values`, `items`, `pop`, `setdefault`, `update`, `clear`, `copy`                                                                                                                |
| `set`  | `add`, `remove`, `discard`, `pop`, `clear`, `copy`, `union`, `intersection`, `difference`, `issubset`, `issuperset`                                                                             |

**Allowed I/O:**

| Category      | Constructs                                                                           |
| ------------- | ------------------------------------------------------------------------------------ |
| Output        | `print(x)`, `print(x, end='')`, `print(x, file=sys.stderr)`                          |
| Input text    | `sys.stdin.readline()`, `sys.stdin.read()`                                           |
| Input binary  | `sys.stdin.buffer.read()`, `sys.stdin.buffer.read(n)`, `sys.stdin.buffer.readline()` |
| Output binary | `sys.stdout.buffer.write(b)`, `sys.stderr.buffer.write(b)`                           |
| Arguments     | `sys.argv`                                                                           |
| Environment   | `os.getenv(name)`, `os.getenv(name, default)`                                        |

**Eager iteration constructs:**

Iteration constructs are allowed when statically analyzable as eager (non-lazy). No generator functions, no lazy pipelines, no infinite sequences.

| Construct          | Allowed                | Notes                    |
| ------------------ | ---------------------- | ------------------------ |
| List comprehension | `[expr for x in iter]` | Always eager             |
| Set comprehension  | `{expr for x in iter}` | Always eager             |
| Dict comprehension | `{k: v for x in iter}` | Always eager             |
| Generator function | `yield`, `yield from`  | Structural recursion only |

**Generator expressions** — allowed only as immediate argument to eager consumers:

| Consumer     | Example                     |
| ------------ | --------------------------- |
| `tuple()`    | `tuple(x for x in iter)`    |
| `list()`     | `list(x for x in iter)`     |
| `set()`      | `set(x for x in iter)`      |
| `any()`      | `any(p(x) for x in iter)`   |
| `all()`      | `all(p(x) for x in iter)`   |
| `sum()`      | `sum(x for x in iter)`      |
| `min()`      | `min(x for x in iter)`      |
| `max()`      | `max(x for x in iter)`      |
| `sorted()`   | `sorted(x for x in iter)`   |
| `str.join()` | `",".join(s for s in iter)` |

Not allowed: `g = (x for x in iter)` (assigned), `foo(x for x in iter)` (unknown consumer), `return (x for x in iter)` (returned).

**enumerate / zip** — allowed only in for-loop headers or eager consumers:

| Allowed                        | Not allowed              |
| ------------------------------ | ------------------------ |
| `for i, x in enumerate(iter):` | `e = enumerate(iter)`    |
| `for a, b in zip(xs, ys):`     | `foo(zip(xs, ys))`       |
| `list(enumerate(iter))`        | `return enumerate(iter)` |

**Structural recursion** — `yield`/`yield from` allowed for tree traversal:

| Allowed | Not allowed |
|---------|-------------|
| `for x in items: yield x` | `while True: yield next()` |
| `yield from traverse(node.children)` | `yield from infinite_stream()` |

Structural recursion over acyclic data is statically provable as finite. The subset guarantees no back-references, so recursion depth is bounded by tree depth.

**Tuple unpacking** — from call result or guarded variable:

| Allowed                      | Not allowed            |
| ---------------------------- | ---------------------- |
| `a, b = func()`              | `a, b = some_var`      |
| `x = func(); if x: a, b = x` | `x = func(); a, b = x` |

Unpacking from a variable is allowed only when the variable is the condition of an enclosing `if` statement and the unpack occurs in the then-branch. This proves the variable is non-None when the tuple contains an optional result.

**Dataclasses:**

The `@dataclass` decorator is allowed with limited arguments:
- `@dataclass` - no arguments (default eq=True)
- `@dataclass(eq=True)` - explicit equality generation
- `@dataclass(unsafe_hash=True)` - hash generation for use as dict keys
- `@dataclass(kw_only=True)` - keyword-only fields

Not allowed: `frozen=True` (immutability cannot be guaranteed in target languages), `order=True`, `field()` options.

| Allowed                         | Not allowed                             |
| ------------------------------- | --------------------------------------- |
| `@dataclass`                    | `@dataclass(frozen=True)`               |
| `@dataclass(unsafe_hash=True)`  | `@dataclass(order=True)`                |
| `x: int = 0`                    | `x: list = field(default_factory=list)` |

**Postconditions:** AST conforms to Tongues subset; all invariants above hold; rejected programs produce clear error messages with source locations.

#### Phase 4: `frontend/names.py`

Build a symbol table mapping names to their declarations. Since phase 3 guarantees no nested functions and no `global`/`nonlocal`, scoping collapses to:

| Scope   | Contains                                  |
| ------- | ----------------------------------------- |
| Builtin | `len`, `range`, `str`, `int`, `Exception` |
| Module  | Classes, functions, constants             |
| Class   | Fields, methods                           |
| Local   | Parameters, local variables               |

No enclosing scope. Resolution is a simple two-level lookup: local → module (→ builtin).

**Postconditions:** All names resolve; no shadowing ambiguity; kind (class/function/variable/parameter/field) is known for each name.

**Prior art:** [Scope Graphs](https://link.springer.com/chapter/10.1007/978-3-662-46669-8_9), [Python LEGB](https://realpython.com/python-scope-legb-rule/)

#### Phase 5: `frontend/signatures.py`

Parse type annotations into internal type representations. Verify types are well-formed via kind checking—kinds classify type constructors the way types classify values. No higher-kinded types, so kind checking reduces to arity validation:

| Constructor   | Arity | Kind               |
| ------------- | ----- | ------------------ |
| `List`, `Set` | 1     | `* -> *`           |
| `Dict`        | 2     | `* -> * -> *`      |
| `Optional`    | 1     | `* -> *`           |
| `Callable`    | 2     | `[*...] -> * -> *` |

**Postconditions:** All type annotations parsed to IR types; all types well-formed (correct arity, valid references); SigTable maps every function to `(params, return_type)`.

**Prior art:** [Kind (type theory)](https://en.wikipedia.org/wiki/Kind_(type_theory)), [PEP 484](https://peps.python.org/pep-0484/)

#### Phase 6: `frontend/fields.py`

Analyze `__init__` bodies to infer field types. Since phase 3 guarantees annotations or obvious types, analysis is simple pattern matching:

| Pattern                  | Inference                                |
| ------------------------ | ---------------------------------------- |
| `self.x: T = ...`        | Field `x` has type `T`                   |
| `self.x = param`         | Field `x` has type of `param` (SigTable) |
| `self.x = literal`       | Field `x` has type of literal            |
| `self.x = Constructor()` | Field `x` has type `Constructor`         |

No full dataflow needed. Walk `__init__` assignments, resolve RHS types via SigTable.

**Postconditions:**
- FieldTable maps every class to `[(field_name, type)]`; all fields typed; init order captured
- Fields assigned `None` or conditionally assigned wrapped in `Optional[T]}`
- No manual type override tables needed; types inferred from `__init__` patterns

**Prior art:** [Java definite assignment](https://docs.oracle.com/javase/specs/jls/se9/html/jls-16.html), [TypeScript strictPropertyInitialization](https://www.typescriptlang.org/docs/handbook/2/classes.html)

#### Phase 7: `frontend/hierarchy.py`

Build the inheritance tree and compute subtyping relations. Inheritance implies subtyping in Tongues. Since phase 3 guarantees single inheritance:

- Hierarchy is a tree, not DAG
- No diamond problem
- LUB is finding common ancestor (walk up both chains)
- Transitive closure is just ancestor list per class

**Postconditions:** SubtypeRel maps every class to ancestors; `is_subtype(A, B)` works for any A, B; no cycles.

**Prior art:** [Inheritance Is Not Subtyping](https://www.cs.utexas.edu/~wcook/papers/InheritanceSubtyping90/CookPOPL90.pdf), [Variance](https://en.wikipedia.org/wiki/Covariance_and_contravariance_(computer_science))

#### Phase 8: `frontend/inference.py`

Assign types to every expression and statement using bidirectional type inference and control-flow-sensitive narrowing. Bidirectional typing is decidable (unlike full inference), has good error locality, and requires moderate annotations. Core rule: introductions check, eliminations synthesize.

| Form        | Mode    | Example                                    |
| ----------- | ------- | ------------------------------------------ |
| Lambda      | check ↓ | `lambda x: x + 1` checks against signature |
| Application | synth ↑ | `f(x)` synthesizes from `f`'s return type  |
| Literal     | synth ↑ | `42` synthesizes `int`                     |
| Variable    | synth ↑ | `x` synthesizes from environment           |

Since all signatures are annotated (SigTable) and fields typed (FieldTable), most work is synthesis. Checking happens at function arguments, return statements, and typed assignments.

**Type narrowing:** Type narrowing (also called flow-sensitive typing or occurrence typing) refines a variable's type based on control flow. The type of a variable depends on which predicates dominate its use.

| Pattern                         | Narrowing                              |
| ------------------------------- | -------------------------------------- |
| `isinstance(x, T)`              | `x` narrows to `T` in then-branch      |
| `x.kind == "value"`             | `x` narrows to struct with that kind   |
| `if x:` where `x: T \| None`    | `x` narrows to `T` in then-branch      |
| `kind = x.kind; if kind == ...` | `x` narrows via alias tracking         |

**Implementation note:** Type narrowing is control-flow sensitive—a specific instance of dataflow analysis. Two strategies are supported:

1. **Pre-computation**: For simple patterns (`isinstance`, truthiness), types are pre-computed by simulating control flow during Phase 8.

2. **On-demand inference**: For complex patterns (kind aliasing, attribute paths, chained assertions), Phase 9 may request type inference with full narrowing context. This follows TypeScript and Pyright's architecture, where narrowed types are evaluated lazily at reference points rather than eagerly pre-computed.

**Truthiness semantics:** Python's `if x:` has type-dependent meaning. Tongues restricts to unambiguous patterns:

| Type        | Pattern     | Meaning      |
| ----------- | ----------- | ------------ |
| `bool`      | `if flag:`  | Boolean test |
| `T \| None` | `if node:`  | Not None     |
| `list[T]`   | `if items:` | Non-empty    |
| `str`       | `if s:`     | Non-empty    |

Ambiguous types like `list[T] | None` require explicit checks (`if x is not None`, `if len(x) > 0`).

**Postconditions:**
- TypedAST complete (every expr has a type); all checks pass; subsumption applied where needed
- Truthiness patterns validated; ambiguous types rejected with diagnostic
- String expressions annotated with indexing semantics: `byte` vs `char` (enables Go `[]rune`, Java `char`)
- Variables assigned different types in branches typed as union
- Nullability propagates through control flow; nullable exprs typed `Optional[T]`
- Single-char literals and `s[i]` results distinguished from multi-char strings
- Method receivers have precise type (not widened to `interface{}` / `any`)
- String variables indexed by character typed as `CharSequence` (enables Go `[]rune`, Java `char[]`); single conversion point inferred at scope entry
- Predicate parameters receiving single-char arguments typed as `Char` (not `String`)
- Expressions have precise narrowed type after type guards; no widening to `interface{}`

**Prior art:** [Bidirectional Typing](https://arxiv.org/abs/1908.05839), [Local Type Inference](https://www.cis.upenn.edu/~bcpierce/papers/lti-toplas.pdf), [Flow-Sensitive Typing](https://en.wikipedia.org/wiki/Flow-sensitive_typing), [Typed Racket Occurrence Typing](https://docs.racket-lang.org/ts-guide/occurrence-typing.html)

#### Phase 9: `frontend/lowering.py`

Translate TypedAST to IR. Lowering primarily reads types from Phase 8, but may invoke type inference for expressions requiring full narrowing context. Pattern-match on AST nodes and emit IR.

| AST Node                 | IR Output                              |
| ------------------------ | -------------------------------------- |
| `BinOp(+, a, b)` : `int` | `ir.BinOp(Add, lower(a), lower(b))`    |
| `Call(f, args)` : `T`    | `ir.Call(f, [lower(a) for a in args])` |
| `Attribute(obj, field)`  | `ir.FieldAccess(lower(obj), field)`    |

**Type resolution strategy:** Following TypeScript's architecture, Phase 9 builds narrowing context (tracking `isinstance` checks, kind comparisons, alias assignments) as it traverses control flow. When a pre-computed type is unavailable, it requests the narrowed type on-demand.

| Pattern                  | Strategy                                |
| ------------------------ | --------------------------------------- |
| `isinstance(x, T)`       | Pre-computed in Phase 8                 |
| `x.kind == "value"`      | On-demand with kind→struct mapping      |
| `kind = x.kind; if ...`  | On-demand with alias tracking           |
| `x.attr.kind == "value"` | On-demand with attribute path tracking  |

**Postconditions:**
- IR Module complete; all IR nodes typed; no AST remnants in output
- Truthy checks (`if x`, `if s`) emit `Truthy(expr)`, not `BinaryOp(Len(x), ">", 0)`
- No marker variables (`_pass`, `_skip_docstring`); use `NoOp` or omit
- Bound method references emit `FuncRef(obj, method)` with `FuncType.receiver` set; backends emit correct function pointer signatures
- String operations emit semantic IR: `CharAt`, `CharLen`, `Substring` (not Python method names)
- Character classification emits semantic IR: `IsAlnum`, `IsDigit`, `IsAlpha`, `IsSpace`, `IsUpper`, `IsLower`; backends map to `unicode.IsLetter`/`Character.isDigit`/regex
- String trimming with char set emits `TrimChars(expr, chars, mode)` where mode is `left`/`right`/`both`; backends map to regex or stdlib
- `TryCatch` carries exception type for catch clause
- Constructors emit `StructLit` with all fields (not field-by-field assignment)
- `range()` iteration emits `ForClassic` (not `Call` to range helper)
- While loops with index iteration pattern (`while i < len(x): ... x[i] ... i += 1`) emit `ForRange` or `ForClassic`; enables Go `for i, c := range` and avoids manual index management
- Module exports emit `Export` nodes (not hardcoded in backend)
- Enum definitions emit `Enum` IR (not prefixed constants)
- Exception classes marked with `extends_error: bool` for target Error inheritance
- Numeric conversion emits `ParseInt(expr)` / `IntToStr(expr)` semantic IR (not helper function names); backends map to `int()`/`strconv.Atoi()`/`Integer.parseInt()`
- Sentinel-to-optional conversion emits `SentinelToOptional(expr, sentinel)` IR; backends map to `None if x == sentinel else x` / `if x == sentinel { return nil }`
- Index with `-1` emits `LastElement(expr)` IR; backends map to `[-1]`/`[len-1]`/`getLast()`
- Conditional expressions emit `Ternary(cond, then, else)` with `needs_statement: bool` flag; backends without ternary operator emit if/else variable assignment
- Pointer creation emits `AddrOf(expr)` semantic IR (not helper function)
- Interface definitions emit `InterfaceDef` with explicit field list (not inferred by backend); includes discriminant fields like `kind: string` for tagged unions
- Type switch emits `TypeSwitch` with `binding` field containing the narrowed variable name; no hardcoded naming conventions in backend
- Slice covariance emits `SliceConvert(source, target_element_type)` when element types differ but are compatible; backends handle covariant/invariant semantics per language
- Comprehensions emit `ListComp`, `SetComp`, `DictComp` with `element`, `target`, `iterable`, `condition` fields; backends emit idiomatic loops or builtins
- Slicing emits `SliceExpr(obj, low, high, step)` with optional fields; backends map to `[a:b]`/`substring()`/`subList()`
- Bitwise operations emit `BinaryOp(op, left, right)` where op is `&`/`|`/`^`/`~`/`<<`/`>>`
- Entry point `main() -> int` with `if __name__ == "__main__"` emits `EntryPoint` IR; backends emit `func main()` / `public static void main()` / `fn main()`
- `print(x)` emits `Print(expr, newline=True, stderr=False)`; `print(x, end='')` sets `newline=False`; `print(x, file=sys.stderr)` sets `stderr=True`
- `sys.stdin.readline()` emits `ReadLine()`; `sys.stdin.read()` emits `ReadAll()`
- `sys.stdin.buffer.read()` emits `ReadBytes()`; `sys.stdin.buffer.read(n)` emits `ReadBytesN(n)`
- `sys.stdout.buffer.write(b)` emits `WriteBytes(expr, stderr=False)`
- `sys.argv` emits `Args` IR; backends map to `os.Args`/`args`/`argv`
- `os.getenv(name)` emits `GetEnv(name, default)` with optional default

**Prior art:** [Three-address code](https://en.wikipedia.org/wiki/Three-address_code), [Cornell CS 4120 IR notes](https://www.cs.cornell.edu/courses/cs4120/2023sp/notes/ir/), [TypeScript Flow Nodes](https://effectivetypescript.com/2024/03/24/flownodes/), [Pyright Lazy Evaluation](https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md)

## Middleend (Phases 10–14)

Read-only analysis passes that annotate IR nodes in place. No transformations—just computing properties needed for code generation.

| Module         | Depends on     | Annotations added                                                                              |
| -------------- | -------------- | ---------------------------------------------------------------------------------------------- |
| `scope.py`     | —              | `is_reassigned`, `is_modified`, `is_unused`, `is_declaration`, `is_interface`, `narrowed_type` |
| `returns.py`   | —              | `needs_named_returns`                                                                          |
| `liveness.py`  | scope, returns | `initial_value_unused`, `catch_var_unused`, `binding_unused`                                   |
| `hoisting.py`  | scope, returns | `hoisted_vars`, `rune_vars`                                                                    |
| `ownership.py` | scope          | `ownership`, `region`, `escapes`                                                               |

#### Phase 9.5: `middleend/__init__.py`

Orchestrate phases 10–14. Run all analysis passes on the IR Module.

#### Phase 10: `middleend/scope.py`

Analyze variable scope: declarations, reassignments, parameter modifications. Walks each function body tracking which variables are declared vs assigned, and whether parameters are modified.

| Annotation              | Meaning                                     |
| ----------------------- | ------------------------------------------- |
| `VarDecl.is_reassigned` | Variable assigned after declaration         |
| `Param.is_modified`     | Parameter assigned/mutated in function body |
| `Param.is_unused`       | Parameter never referenced                  |
| `Assign.is_declaration` | First assignment to a new variable          |
| `Expr.is_interface`     | Expression statically typed as interface    |
| `Name.narrowed_type`    | Precise type at use site after type guards  |

**Postconditions:**
- Every VarDecl, Param, and Assign annotated; reassignment counts accurate
- Variables annotated with `is_const` (never reassigned after declaration); enables `const`/`let` in TS, `final` in Java
- Expressions annotated with `is_interface: bool` when statically typed as interface; enables direct `== nil` vs reflection-based nil check in Go
- Variables annotated with precise narrowed type at each use site (not just declaration type); eliminates redundant casts when type is statically known

#### Phase 11: `middleend/returns.py`

Analyze return patterns: which statements contain returns, which always return, which functions need named returns for Go emission.

| Function          | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `contains_return` | Does statement list contain any Return?  |
| `always_returns`  | Does statement list return on all paths? |

**Postconditions:** `Function.needs_named_returns` set for functions with TryCatch containing catch-body returns.

#### Phase 12: `middleend/liveness.py`

Analyze liveness: unused initial values, unused catch variables, unused bindings. Determines whether the initial value of a VarDecl is ever read before being overwritten.

| Annotation                     | Meaning                               |
| ------------------------------ | ------------------------------------- |
| `VarDecl.initial_value_unused` | Initial value overwritten before read |
| `TryCatch.catch_var_unused`    | Catch variable never referenced       |
| `TypeSwitch.binding_unused`    | Binding variable never referenced     |
| `TupleAssign.unused_indices`   | Which tuple targets are never used    |

**Postconditions:** All liveness annotations set; enables dead store elimination in codegen.

#### Phase 13: `middleend/hoisting.py`

Compute variables needing hoisting for Go emission. Go requires variables to be declared before use, but Python allows first assignment in branches. This pass identifies variables that need to be hoisted to an outer scope.

Variables need hoisting when:
- First assigned inside a control structure (if/try/while/for/match)
- Used after that control structure exits

**Postconditions:**
- `If.hoisted_vars`, `TryCatch.hoisted_vars`, `While.hoisted_vars`, etc. contain `[(name, type)]` for variables needing hoisting
- All hoisted vars have concrete type (no `None`/`interface{}`/`any` fallback)
- Type derived from all assignment sites, not just first encountered
- String variables needing character indexing listed in `Function.rune_vars: list[str]`; Go backend emits `runes := []rune(s)` at scope entry, uses `runes[i]` thereafter

**Prior art:** [Go variable scoping](https://go.dev/ref/spec#Declarations_and_scope)

#### Phase 14: `middleend/ownership.py`

Infer ownership and region annotations for memory-safe code generation. Since phase 3 guarantees
no back-references, no borrowed field storage, and strict tree structures, ownership analysis
reduces to simple patterns:

| Pattern                    | Ownership        | Region              |
| -------------------------- | ---------------- | ------------------- |
| Constructor call (`Foo()`) | owned            | caller's region     |
| Factory function return    | owned            | caller's region     |
| Parameter                  | borrowed         | caller's region     |
| Field access               | borrowed         | object's region     |
| Return value               | owned (transfer) | caller's region     |
| Collection element         | owned            | collection's region |
| Explicit `.copy()` call    | owned (new)      | caller's region     |

**Escape analysis** detects when borrowed references outlive their region:

| Violation                    | Diagnostic                                                                   |
| ---------------------------- | ---------------------------------------------------------------------------- |
| Borrowed ref stored in field | Error: "cannot store borrowed `x` in field; use `.copy()` or take ownership" |
| Borrowed ref returned        | Error: "reference to `x` escapes function scope"                             |
| Borrowed ref in collection   | Error: "cannot add borrowed `x` to collection; transfer ownership or copy"   |

**Ambiguous ownership** (Lobster-style fallback): When inference cannot determine ownership
statically, mark as `shared`. Backends emit:
- Go: no change (GC handles)
- Rust: `Rc<T>` or `Arc<T>`
- C: reference-counted wrapper

| Annotation          | Meaning                                           |
| ------------------- | ------------------------------------------------- |
| `VarDecl.ownership` | `owned`, `borrowed`, or `shared`                  |
| `Param.ownership`   | `owned` (takes ownership) or `borrowed` (default) |
| `Field.ownership`   | `owned` (default) or `weak` (back-reference)      |
| `Expr.escapes`      | Expression's value escapes current scope          |

**Postconditions:**
- Every VarDecl, Param, Field annotated with ownership
- No escaping borrowed references (or diagnostic emitted)
- Ambiguous cases marked `shared` for runtime fallback
- Backends can emit memory management without re-analysis

**Prior art:** [Tofte-Talpin Region Inference](https://www.sciencedirect.com/science/article/pii/S0890540196926139), [Lobster Compile-Time RC](https://aardappel.github.io/lobster/memory_management.html), [Cyclone Regions](https://www.cs.umd.edu/projects/cyclone/papers/cyclone-regions.pdf)

## Backend (Phase 15)

Emit target language source from annotated IR. Each backend is a single module that walks the IR and produces output text.

| Target | Module    | Output                   |
| ------ | --------- | ------------------------ |
| Go     | `go.py`   | `.go` source files       |
| C      | `c.py`    | `.c` / `.h` source files |
| Rust   | `rust.py` | `.rs` source files       |

#### Phase 15: `backend/<lang>.py`

Walk the annotated IR and emit target language source. The backend reads all annotations from phases 1–14 but adds none—pure output generation.

| IR Node      | Go Output                | C Output                  | Rust Output             |
| ------------ | ------------------------ | ------------------------- | ----------------------- |
| `Function`   | `func name(...) { ... }` | `type name(...) { ... }`  | `fn name(...) { ... }`  |
| `Struct`     | `type Name struct { }`   | `typedef struct { } Name` | `struct Name { }`       |
| `VarDecl`    | `var x T` or `x := ...`  | `T x = ...`               | `let mut x = ...`       |
| `MethodCall` | `obj.Method(args)`       | `Method(obj, args)`       | `obj.method(args)`      |
| `Print`      | `fmt.Println(x)`         | `printf("%s\n", x)`       | `println!("{}", x)`     |
| `ReadLine`   | `bufio.Scanner`          | `fgets()`                 | `stdin().read_line()`   |
| `ReadAll`    | `io.ReadAll(os.Stdin)`   | `read()` loop             | `read_to_string(stdin)` |
| `Args`       | `os.Args`                | `argv[0..argc]`           | `env::args().collect()` |
| `GetEnv`     | `os.Getenv()`            | `getenv()`                | `env::var().ok()`       |

The backend consumes middleend annotations:
- `is_reassigned` → Go: `var` vs `:=`; Rust: `let mut` vs `let`; TS: `let` vs `const`
- `hoisted_vars` → Go: emit declarations before control structure
- `needs_named_returns` → Go: use named return values
- `initial_value_unused` → Go: omit initializer, use zero value
- `is_interface` → Go: direct `== nil` vs `_isNilInterface()` reflection
- `narrowed_type` → Java/TS: omit redundant casts when type is known
- `rune_vars` → Go: emit `[]rune` conversion at scope entry
- `ownership=owned` → Rust: owned value; C: arena-allocated
- `ownership=borrowed` → Rust: `&T`; C: pointer to caller's memory
- `ownership=shared` → Rust: `Rc<T>`; C: refcounted wrapper
- `ownership=weak` → Rust: `Weak<T>`; C: non-owning pointer (back-refs)

**Postconditions:** Valid target language source emitted; all IR nodes consumed; output compiles with target toolchain.
