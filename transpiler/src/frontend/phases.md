# Tongues Phases

Sequential pipeline with clean phase boundaries. Each phase completes before the next starts.

## Design Principles

- **Sequential**: Each phase completes fully before the next starts
- **Monotonic**: Phase N reads outputs of phases 1..N-1; invariants accumulate
- **Fail fast**: Reject bad input at the earliest possible phase

## Overview

| Phase | Stage     | Module           | Description                                         |
| :---: | --------- | ---------------- | --------------------------------------------------- |
|   0   | frontend  | `__init__.py`    | Orchestrate phases 1–8                              |
|   1   | frontend  | `parse.py`       | Tokenize and parse source; produce dict-based AST   |
|   2   | frontend  | `subset.py`      | Reject unsupported Python features early            |
|   3   | frontend  | `names.py`       | Scope analysis and name binding                     |
|   4   | frontend  | `signatures.py`  | Type syntax parsing and kind checking               |
|   5   | frontend  | `fields.py`      | Dataflow over `__init__`; infer field types         |
|   6   | frontend  | `hierarchy.py`   | Class hierarchy; subtyping relations                |
|   7   | frontend  | `inference.py`   | Bidirectional type inference (↑synth / ↓check)      |
|   8   | frontend  | `lowering.py`    | Type-directed elaboration to IR                     |
|   9   | middleend | `__init__.py`    | Orchestrate phases 10–13                            |
|  10   | middleend | `scope.py`       | Variable declarations, reassignments, modifications |
|  11   | middleend | `returns.py`     | Return pattern analysis                             |
|  12   | middleend | `liveness.py`    | Unused values, catch vars, bindings                 |
|  13   | middleend | `hoisting.py`    | Variables needing hoisting for Go emission          |
|  14   | backend   | `<lang>.py`      | Emit target language source from annotated IR       |

## Frontend (Phases 0–8)

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

#### Phase 0: `frontend/__init__.py`

Orchestrate phases 1–8. Initialize empty context tables, invoke each phase, thread outputs forward.

#### Phase 1: `frontend/parse.py`

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

#### Phase 2: `frontend/subset.py`

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

#### Phase 3: `frontend/names.py`

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

#### Phase 4: `frontend/signatures.py`

Parse type annotations into internal type representations. Verify types are well-formed via kind checking—kinds classify type constructors the way types classify values. No higher-kinded types, so kind checking reduces to arity validation:

| Constructor   | Arity | Kind               |
| ------------- | ----- | ------------------ |
| `List`, `Set` | 1     | `* -> *`           |
| `Dict`        | 2     | `* -> * -> *`      |
| `Optional`    | 1     | `* -> *`           |
| `Callable`    | 2     | `[*...] -> * -> *` |

**Postconditions:** All type annotations parsed to IR types; all types well-formed (correct arity, valid references); SigTable maps every function to `(params, return_type)`.

**Prior art:** [Kind (type theory)](https://en.wikipedia.org/wiki/Kind_(type_theory)), [PEP 484](https://peps.python.org/pep-0484/)

#### Phase 5: `frontend/fields.py`

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

#### Phase 6: `frontend/hierarchy.py`

Build the inheritance tree and compute subtyping relations. Inheritance implies subtyping in Tongues. Since phase 2 guarantees single inheritance:

- Hierarchy is a tree, not DAG
- No diamond problem
- LUB is finding common ancestor (walk up both chains)
- Transitive closure is just ancestor list per class

**Postconditions:** SubtypeRel maps every class to ancestors; `is_subtype(A, B)` works for any A, B; no cycles.

**Prior art:** [Inheritance Is Not Subtyping](https://www.cs.utexas.edu/~wcook/papers/InheritanceSubtyping90/CookPOPL90.pdf), [Variance](https://en.wikipedia.org/wiki/Covariance_and_contravariance_(computer_science))

#### Phase 7: `frontend/inference.py`

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

#### Phase 8: `frontend/lowering.py`

Translate TypedAST to IR. Lowering only reads types, never computes them—if phase 7 did its job, every expression has a type. Pure syntactic transformation: pattern-match on AST nodes and emit IR.

| AST Node                 | IR Output                              |
| ------------------------ | -------------------------------------- |
| `BinOp(+, a, b)` : `int` | `ir.BinOp(Add, lower(a), lower(b))`    |
| `Call(f, args)` : `T`    | `ir.Call(f, [lower(a) for a in args])` |
| `Attribute(obj, field)`  | `ir.FieldAccess(lower(obj), field)`    |

**Postconditions:** IR Module complete; all IR nodes typed; no AST remnants in output.

**Prior art:** [Three-address code](https://en.wikipedia.org/wiki/Three-address_code), [Cornell CS 4120 IR notes](https://www.cs.cornell.edu/courses/cs4120/2023sp/notes/ir/)

## Middleend (Phases 9–13)

Read-only analysis passes that annotate IR nodes in place. No transformations—just computing properties needed for code generation.

| Module         | Depends on     | Annotations added                                         |
| -------------- | -------------- | --------------------------------------------------------- |
| `scope.py`     | —              | `is_reassigned`, `is_modified`, `is_unused`, `is_declaration` |
| `returns.py`   | —              | `needs_named_returns`                                     |
| `liveness.py`  | scope, returns | `initial_value_unused`, `catch_var_unused`, `binding_unused` |
| `hoisting.py`  | scope, returns | `hoisted_vars`                                            |

#### Phase 9: `middleend/__init__.py`

Orchestrate phases 10–13. Run all analysis passes on the IR Module.

#### Phase 10: `middleend/scope.py`

Analyze variable scope: declarations, reassignments, parameter modifications. Walks each function body tracking which variables are declared vs assigned, and whether parameters are modified.

| Annotation               | Meaning                                      |
| ------------------------ | -------------------------------------------- |
| `VarDecl.is_reassigned`  | Variable assigned after declaration          |
| `Param.is_modified`      | Parameter assigned/mutated in function body  |
| `Param.is_unused`        | Parameter never referenced                   |
| `Assign.is_declaration`  | First assignment to a new variable           |

**Postconditions:** Every VarDecl, Param, and Assign annotated; reassignment counts accurate.

#### Phase 11: `middleend/returns.py`

Analyze return patterns: which statements contain returns, which always return, which functions need named returns for Go emission.

| Function           | Purpose                                          |
| ------------------ | ------------------------------------------------ |
| `contains_return`  | Does statement list contain any Return?          |
| `always_returns`   | Does statement list return on all paths?         |

**Postconditions:** `Function.needs_named_returns` set for functions with TryCatch containing catch-body returns.

#### Phase 12: `middleend/liveness.py`

Analyze liveness: unused initial values, unused catch variables, unused bindings. Determines whether the initial value of a VarDecl is ever read before being overwritten.

| Annotation                   | Meaning                                    |
| ---------------------------- | ------------------------------------------ |
| `VarDecl.initial_value_unused` | Initial value overwritten before read    |
| `TryCatch.catch_var_unused`  | Catch variable never referenced            |
| `TypeSwitch.binding_unused`  | Binding variable never referenced          |
| `TupleAssign.unused_indices` | Which tuple targets are never used         |

**Postconditions:** All liveness annotations set; enables dead store elimination in codegen.

#### Phase 13: `middleend/hoisting.py`

Compute variables needing hoisting for Go emission. Go requires variables to be declared before use, but Python allows first assignment in branches. This pass identifies variables that need to be hoisted to an outer scope.

Variables need hoisting when:
- First assigned inside a control structure (if/try/while/for/match)
- Used after that control structure exits

**Postconditions:** `If.hoisted_vars`, `TryCatch.hoisted_vars`, `While.hoisted_vars`, etc. contain `[(name, type)]` for variables needing hoisting.

**Prior art:** [Go variable scoping](https://go.dev/ref/spec#Declarations_and_scope)

## Backend (Phase 14)

Emit target language source from annotated IR. Each backend is a single module that walks the IR and produces output text.

| Target | Module    | Output                  |
| ------ | --------- | ----------------------- |
| Go     | `go.py`   | `.go` source files      |
| C      | `c.py`    | `.c` / `.h` source files |
| Rust   | `rust.py` | `.rs` source files      |

#### Phase 14: `backend/<lang>.py`

Walk the annotated IR and emit target language source. The backend reads all annotations from phases 0–13 but adds none—pure output generation.

| IR Node       | Go Output                | C Output                  |
| ------------- | ------------------------ | ------------------------- |
| `Function`    | `func name(...) { ... }` | `type name(...) { ... }`  |
| `Struct`      | `type Name struct { }`   | `typedef struct { } Name` |
| `VarDecl`     | `var x T` or `x := ...`  | `T x = ...`               |
| `MethodCall`  | `obj.Method(args)`       | `Method(obj, args)`       |

The backend consumes middleend annotations:
- `is_reassigned` → Go: `var` vs `:=`
- `hoisted_vars` → Go: emit declarations before control structure
- `needs_named_returns` → Go: use named return values
- `initial_value_unused` → Go: omit initializer, use zero value

**Postconditions:** Valid target language source emitted; all IR nodes consumed; output compiles with target toolchain.
