# Frontend Phases

Sequential pipeline with clean phase boundaries. Each phase completes before the next starts.

| Phase | Module          | Description                                                   |
| :---: | --------------- | ------------------------------------------------------------- |
|   1   | `parse.py`      | Tokenize and parse source; produce dict-based AST             |
|   2   | `subset.py`     | Subset verification; reject unsupported Python features early |
|   3   | `names.py`      | Scope analysis and name binding                               |
|   4   | `signatures.py` | Type syntax parsing and kind checking                         |
|   5   | `fields.py`     | Dataflow over `__init__`; infer field types                   |
|   6   | `hierarchy.py`  | Class hierarchy; subtyping relations                          |
|   7   | `inference.py`  | Bidirectional type inference (↑synth / ↓check)                |
|   8   | `lowering.py`   | Type-directed elaboration to IR                               |

## Design Principles

- **Sequential**: Each phase completes fully before the next starts
- **Monotonic**: Phase N reads outputs of phases 1..N-1; invariants accumulate
- **Fail fast**: Reject bad input at the earliest possible phase

## Module Boundaries

| Module          | Knows types? | Knows IR? | Output                                |
| --------------- | :----------: | :-------: | ------------------------------------- |
| `parse.py`      |      no      |    no     | dict-based AST                        |
| `subset.py`     |      no      |    no     | (rejects bad input or passes through) |
| `names.py`      |      no      |    no     | NameTable { name → kind }             |
| `signatures.py` | yes (parse)  |    no     | SigTable { func → (params, ret) }     |
| `fields.py`     | yes (infer)  |    no     | FieldTable { class → [(name, type)] } |
| `hierarchy.py`  |  yes (sub)   |    no     | SubtypeRel { class → ancestors }      |
| `inference.py`  | yes (bidir)  |    no     | TypedAST (↑synth / ↓check)            |
| `lowering.py`   |  no (reads)  |    yes    | IR Module                             |

## Design Detail

### Phase 0: `__init__.py`

Entry point that runs phases 1–8 in sequence. Initializes empty context tables, invokes each phase, and threads outputs forward. The module docstring should summarize the design principles so they're discoverable from code.

### Phase 1: `parse.py`

Tokenize source code and parse into dict-based AST. Enables self-hosting by removing CPython bootstrap dependency.

| Component      | Lines | Description                                      |
| -------------- | ----- | ------------------------------------------------ |
| `tokenize.py`  | ~350  | While-loop state machine; returns `list[Token]`  |
| `grammar.py`   | ~250  | Pre-compiled DFA tables as static data           |
| `parse.py`     | ~175  | LR shift-reduce parser; stack-based              |
| `ast_build.py` | ~250  | Grammar rules → dict nodes matching `ast` module |

The tokenizer uses explicit `while i < len(...)` loops (no generators). Grammar tables are pre-compiled under CPython once, then embedded as data. The parser is a simple stack machine consuming tokens and emitting dict-based AST nodes.

The restricted subset eliminates major parsing pain points:

| Constraint             | Simplification                                     |
| ---------------------- | -------------------------------------------------- |
| No f-strings           | Tokenizer is straightforward string handling       |
| No generators          | Tokenizer returns `list[Token]`, not lazy iterator |
| No nested functions    | No closure/scope tracking during parse             |
| No walrus operator     | No `:=` ambiguity in expressions                   |
| No async/await         | No context-dependent keyword handling              |
| Single grammar version | No version switching; one static grammar           |

**Postconditions:** Source code parsed to dict-based AST; structure matches `ast.parse()` output; all tokens consumed; syntax errors reported with line/column.

**Prior art:** [Dragon Book Ch. 3-4](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools), [pgen2](https://github.com/python/cpython/tree/main/Parser/pgen), [parso](https://github.com/davidhalter/parso)

### Phase 2: `subset.py`

Reject unsupported Python features early. If verification passes, downstream phases can assume:

| Invariant                | What it enables                                              |
| ------------------------ | ------------------------------------------------------------ |
| No dynamic dispatch      | Call graph is static; all calls resolve at compile time      |
| No runtime introspection | No `getattr`/`setattr`/`__dict__` — field access is static   |
| No closures              | No nested functions — all functions are top-level or methods |
| No generators            | Control flow is eager; no lazy evaluation                    |
| All types annotated      | Signatures have types; inference only needed for locals      |
| No bare collections      | `list[T]` not `list` — element types always known            |
| Single inheritance       | Class hierarchy is a tree, not a DAG                         |
| No decorators            | Functions/classes aren't modified at runtime                 |
| No mutable defaults      | Default args are immutable; no shared-state bugs             |
| Static imports           | Only `typing`, `__future__`, `collections.abc`               |

**Postconditions:** AST conforms to Tongues subset; all invariants above hold; rejected programs produce clear error messages with source locations.

### Phase 3: `names.py`

Build a symbol table mapping names to their declarations. Since phase 2 guarantees no nested functions and no `global`/`nonlocal`, scoping collapses to:

| Scope   | Contains                                  |
| ------- | ----------------------------------------- |
| Builtin | `len`, `range`, `str`, `int`, `Exception` |
| Module  | Classes, functions, constants             |
| Class   | Fields, methods                           |
| Local   | Parameters, local variables               |

No enclosing scope. Resolution is a simple two-level lookup: local → module (→ builtin).

**Postconditions:** All names resolve; no shadowing ambiguity; kind (class/function/variable/parameter/field) is known for each name.

**Prior art:** [Scope Graphs](https://link.springer.com/chapter/10.1007/978-3-662-46669-8_9), [Python LEGB](https://realpython.com/python-scope-legb-rule/)

### Phase 4: `signatures.py`

Parse type annotations into internal type representations. Verify types are well-formed via kind checking—kinds classify type constructors the way types classify values. No higher-kinded types, so kind checking reduces to arity validation:

| Constructor   | Arity | Kind               |
| ------------- | ----- | ------------------ |
| `List`, `Set` | 1     | `* -> *`           |
| `Dict`        | 2     | `* -> * -> *`      |
| `Optional`    | 1     | `* -> *`           |
| `Callable`    | 2     | `[*...] -> * -> *` |

**Postconditions:** All type annotations parsed to IR types; all types well-formed (correct arity, valid references); SigTable maps every function to `(params, return_type)`.

**Prior art:** [Kind (type theory)](https://en.wikipedia.org/wiki/Kind_(type_theory)), [PEP 484](https://peps.python.org/pep-0484/)

### Phase 5: `fields.py`

Analyze `__init__` bodies to infer field types. Since phase 2 guarantees annotations or obvious types, analysis is simple pattern matching:

| Pattern                  | Inference                                |
| ------------------------ | ---------------------------------------- |
| `self.x: T = ...`        | Field `x` has type `T`                   |
| `self.x = param`         | Field `x` has type of `param` (SigTable) |
| `self.x = literal`       | Field `x` has type of literal            |
| `self.x = Constructor()` | Field `x` has type `Constructor`         |

No full dataflow needed. Walk `__init__` assignments, resolve RHS types via SigTable.

**Postconditions:** FieldTable maps every class to `[(field_name, type)]`; all fields typed; init order captured.

**Prior art:** [Java definite assignment](https://docs.oracle.com/javase/specs/jls/se9/html/jls-16.html), [TypeScript strictPropertyInitialization](https://www.typescriptlang.org/docs/handbook/2/classes.html)

### Phase 6: `hierarchy.py`

Build the inheritance tree and compute subtyping relations. Inheritance implies subtyping in Tongues. Since phase 2 guarantees single inheritance:

- Hierarchy is a tree, not DAG
- No diamond problem
- LUB is finding common ancestor (walk up both chains)
- Transitive closure is just ancestor list per class

**Postconditions:** SubtypeRel maps every class to ancestors; `is_subtype(A, B)` works for any A, B; no cycles.

**Prior art:** [Inheritance Is Not Subtyping](https://www.cs.utexas.edu/~wcook/papers/InheritanceSubtyping90/CookPOPL90.pdf), [Variance](https://en.wikipedia.org/wiki/Covariance_and_contravariance_(computer_science))

### Phase 7: `inference.py`

Assign types to every expression and statement using bidirectional type inference. Bidirectional typing is decidable (unlike full inference), has good error locality, and requires moderate annotations. Core rule: introductions check, eliminations synthesize.

| Form        | Mode    | Example                                    |
| ----------- | ------- | ------------------------------------------ |
| Lambda      | check ↓ | `lambda x: x + 1` checks against signature |
| Application | synth ↑ | `f(x)` synthesizes from `f`'s return type  |
| Literal     | synth ↑ | `42` synthesizes `int`                     |
| Variable    | synth ↑ | `x` synthesizes from environment           |

Since all signatures are annotated (SigTable) and fields typed (FieldTable), most work is synthesis. Checking happens at function arguments, return statements, and typed assignments.

**Postconditions:** TypedAST complete (every expr has a type); all checks pass; subsumption applied where needed.

**Prior art:** [Bidirectional Typing](https://arxiv.org/abs/1908.05839), [Local Type Inference](https://www.cis.upenn.edu/~bcpierce/papers/lti-toplas.pdf)

### Phase 8: `lowering.py`

Translate TypedAST to IR. Lowering only reads types, never computes them—if phase 7 did its job, every expression has a type. Pure syntactic transformation: pattern-match on AST nodes and emit IR.

| AST Node                 | IR Output                              |
| ------------------------ | -------------------------------------- |
| `BinOp(+, a, b)` : `int` | `ir.BinOp(Add, lower(a), lower(b))`    |
| `Call(f, args)` : `T`    | `ir.Call(f, [lower(a) for a in args])` |
| `Attribute(obj, field)`  | `ir.FieldAccess(lower(obj), field)`    |

**Postconditions:** IR Module complete; all IR nodes typed; no AST remnants in output.

**Prior art:** [Three-address code](https://en.wikipedia.org/wiki/Three-address_code), [Cornell CS 4120 IR notes](https://www.cs.cornell.edu/courses/cs4120/2023sp/notes/ir/)
