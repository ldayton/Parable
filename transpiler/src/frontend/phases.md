# Frontend Phases

Sequential pipeline with clean phase boundaries. Each phase completes before the next starts.

| Phase | Module          | Description                                                   |
| :---: | --------------- | ------------------------------------------------------------- |
|   0   | `__init__.py`   | Entry point; orchestrates phases                              |
|   1   | `verify.py`     | Subset verification; reject unsupported Python features early |
|   2   | `names.py`      | Scope analysis and name binding                               |
|   3   | `signatures.py` | Type syntax parsing and kind checking                         |
|   4   | `fields.py`     | Dataflow over `__init__`; infer field types                   |
|   5   | `hierarchy.py`  | Class hierarchy; subtyping relations                          |
|   6   | `inference.py`  | Bidirectional type inference (↑synth / ↓check)                |
|   7   | `lowering.py`   | Type-directed elaboration to IR                               |

## Design Principles

- **Sequential**: Each phase completes fully before the next starts
- **No back-edges**: Phase N reads outputs of phases 0..N-1, writes one artifact
- **Fail fast**: Reject bad input at the earliest possible phase
- **Decoupled**: Lowering only sees TypedAST, never calls inference

## Module Boundaries

| Module          | Knows about types? | Knows about IR? |
| --------------- | :----------------: | :-------------: |
| `verify.py`     |         no         |       no        |
| `names.py`      |         no         |       no        |
| `signatures.py` |   yes (parsing)    |       no        |
| `fields.py`     |  yes (inference)   |       no        |
| `hierarchy.py`  |  yes (subtyping)   |       no        |
| `inference.py`  |    yes (bidir)     |       no        |
| `lowering.py`   |  no (just reads)   |       yes       |

## Data Flow

```
         AST
          │
          ▼
┌─────────────────┐
│  0. __init__    │──▶ Context (empty tables)
└────────┬────────┘
         ▼
┌─────────────────┐
│  1. verify      │──▶ (rejects bad input or passes through)
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. names       │──▶ NameTable { name → kind }
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. signatures  │──▶ SigTable { func → (params, ret) }
└────────┬────────┘
         ▼
┌─────────────────┐
│  4. fields      │──▶ FieldTable { class → [(name, type)] }
└────────┬────────┘
         ▼
┌─────────────────┐
│  5. hierarchy   │──▶ SubtypeRel { class → ancestors }
└────────┬────────┘
         ▼
┌─────────────────┐
│  6. inference   │──▶ TypedAST (↑synth / ↓check)
└────────┬────────┘
         ▼
┌─────────────────┐
│  7. lowering    │──▶ IR Module
└────────┬────────┘
         ▼
         IR
```

## Future Work

### Phase 0: `__init__.py`

Module docstring should explain overall philosophy:

- Sequential pipeline with clean phase boundaries
- Each phase completes fully before the next starts
- No back-edges: phase N reads outputs of phases 0..N-1, writes one artifact
- Fail fast: reject bad input at the earliest possible phase
- Decoupled: lowering only sees TypedAST, never calls inference
- Research-oriented: phases map to PL literature (scope analysis, kind checking, bidirectional typing, elaboration)

This makes the philosophy discoverable from code, not just documentation.

### Phase 1: `verify.py`

Document invariants as explicit postconditions. If verification passes, downstream phases can assume:

| Invariant                | What it enables                                      |
| ------------------------ | ---------------------------------------------------- |
| No dynamic dispatch      | Call graph is static; all calls resolve at compile time |
| No runtime introspection | No `getattr`/`setattr`/`__dict__` — field access is static |
| No closures              | No nested functions — all functions are top-level or methods |
| No generators            | Control flow is eager; no lazy evaluation            |
| All types annotated      | Signatures have types; inference only needed for locals |
| No bare collections      | `list[T]` not `list` — element types always known    |
| Single inheritance       | Class hierarchy is a tree, not a DAG                 |
| No decorators            | Functions/classes aren't modified at runtime         |
| No mutable defaults      | Default args are immutable; no shared-state bugs     |
| Static imports           | Only `typing`, `__future__`, `collections.abc`       |

Express via a `VerifiedAST` wrapper type that documents the contract.

### Phase 2: `names.py`

Build a symbol table mapping names to their declarations. Resolve what each name refers to.

**Academic terms:** name binding, name resolution, scope graph, lexical scoping, shadowing.

**Prior art:**
- [Scope Graphs](https://link.springer.com/chapter/10.1007/978-3-662-46669-8_9) — language-independent theory (Neron, Visser et al., ESOP 2015)
- [Spoofax/Statix](https://spoofax.dev/references/statix/scope-graphs/) — declarative scope graph constraints
- [Python LEGB](https://realpython.com/python-scope-legb-rule/) — Local → Enclosing → Global → Builtin

**Simplification for Tongues:** Full LEGB is overkill. Since phase 1 guarantees no nested functions and no `global`/`nonlocal`, scoping collapses to:

| Scope       | Contains                                  |
| ----------- | ----------------------------------------- |
| Builtin     | `len`, `range`, `str`, `int`, `Exception` |
| Module      | Classes, functions, constants             |
| Class       | Fields, methods                           |
| Local       | Parameters, local variables               |

No enclosing scope. No closures. Resolution is a simple two-level lookup: local → module (→ builtin).

**Postconditions:** All names resolve; no shadowing ambiguity; kind (class/function/variable/parameter/field) is known for each name.

### Phase 3: `signatures.py`

Parse type annotations into internal type representations. Verify types are well-formed.

**Academic terms:** kind, kind checking, type constructor, arity, higher-kinded type.

**Key insight:** Kinds are to types what types are to values. `*` is a concrete type, `* -> *` is a unary type constructor (List, Optional), `* -> * -> *` is binary (Dict).

**Prior art:**
- [Kind (type theory)](https://en.wikipedia.org/wiki/Kind_(type_theory)) — kinds classify type constructors
- [Haskell kinds](https://wiki.haskell.org/Kind) — explicit kind system
- [PEP 484](https://peps.python.org/pep-0484/) — Python type hints specification

**Simplification for Tongues:** No higher-kinded types. Kind checking reduces to arity validation:

| Constructor      | Arity | Kind            |
| ---------------- | ----- | --------------- |
| `List`, `Set`    | 1     | `* -> *`        |
| `Dict`           | 2     | `* -> * -> *`   |
| `Optional`       | 1     | `* -> *`        |
| `Callable`       | 2     | `[*...] -> * -> *` |

**Postconditions:** All type annotations parsed to IR types; all types well-formed (correct arity, valid references); SigTable maps every function to `(params, return_type)`.

### Phase 4: `fields.py`

Analyze `__init__` bodies to infer field types from assignment patterns.

**Academic terms:** definite assignment, flow-sensitive typing, typestate, abstract interpretation.

**Prior art:**
- [Java definite assignment](https://docs.oracle.com/javase/specs/jls/se9/html/jls-16.html) — blank finals must be assigned in constructor
- [TypeScript strictPropertyInitialization](https://www.typescriptlang.org/docs/handbook/2/classes.html) — requires field init
- [mypy type inference](https://mypy.readthedocs.io/en/stable/type_inference_and_annotations.html) — infers from initial assignment

**Simplification for Tongues:** Since phase 1 guarantees annotations or obvious types, analysis is simple pattern matching:

| Pattern                | Inference                              |
| ---------------------- | -------------------------------------- |
| `self.x: T = ...`      | Field `x` has type `T`                 |
| `self.x = param`       | Field `x` has type of `param` (SigTable) |
| `self.x = literal`     | Field `x` has type of literal          |
| `self.x = Constructor()` | Field `x` has type `Constructor`     |

No full dataflow needed. Walk `__init__` assignments, resolve RHS types via SigTable.

**Postconditions:** FieldTable maps every class to `[(field_name, type)]`; all fields typed; init order captured.

### Phase 5: `hierarchy.py`

Build the inheritance tree. Compute subtyping relations for type checking.

**Academic terms:** inheritance, subtyping, variance, transitive closure, least upper bound (LUB).

**Key insight:** Inheritance ≠ subtyping. Inheritance is code reuse; subtyping is substitutability. In Tongues, inheritance implies subtyping (inheritance-based subtyping).

**Prior art:**
- [Inheritance Is Not Subtyping](https://www.cs.utexas.edu/~wcook/papers/InheritanceSubtyping90/CookPOPL90.pdf) — Cook, Hill, Canning (POPL 1990)
- [Variance](https://en.wikipedia.org/wiki/Covariance_and_contravariance_(computer_science)) — covariance (returns), contravariance (params)
- [Scala variances](https://docs.scala-lang.org/tour/variances.html) — `+T` covariant, `-T` contravariant

**Simplification for Tongues:** Since phase 1 guarantees single inheritance:

- Hierarchy is a tree, not DAG
- No diamond problem
- LUB is finding common ancestor (walk up both chains)
- Transitive closure is just ancestor list per class

**Postconditions:** SubtypeRel maps every class to ancestors; `is_subtype(A, B)` works for any A, B; no cycles.

### Phase 6: `inference.py`

Assign types to every expression and statement using bidirectional type inference.

**Academic terms:** synthesis (↑), checking (↓), introduction, elimination, subsumption.

**Core rule:** Introductions check, eliminations synthesize.

| Form        | Mode     | Example                                    |
| ----------- | -------- | ------------------------------------------ |
| Lambda      | check ↓  | `lambda x: x + 1` checks against signature |
| Application | synth ↑  | `f(x)` synthesizes from `f`'s return type  |
| Literal     | synth ↑  | `42` synthesizes `int`                     |
| Variable    | synth ↑  | `x` synthesizes from environment           |

**Prior art:**
- [Bidirectional Typing](https://arxiv.org/abs/1908.05839) — Dunfield & Krishnaswami survey (2019)
- [Local Type Inference](https://www.cis.upenn.edu/~bcpierce/papers/lti-toplas.pdf) — Pierce & Turner (TOPLAS 2000)
- [Bidirectional Typing Rules Tutorial](https://davidchristiansen.dk/tutorials/bidirectional.pdf) — Christiansen

**Why bidirectional?** Decidable for expressive type systems (unlike full inference), good error locality, moderate annotation burden.

**Simplification for Tongues:** Since all signatures are annotated (SigTable) and fields typed (FieldTable), most work is synthesis. Checking happens at function arguments, return statements, and typed assignments.

**Postconditions:** TypedAST complete (every expr has a type); all checks pass; subsumption applied where needed.

### Phase 7: `lowering.py`

Translate TypedAST to IR. Each AST construct has a translation rule.

**Academic terms:** syntax-directed translation, elaboration, lowering, three-address code, A-normal form (ANF).

**Key property:** Lowering only reads types, never computes them. If phase 6 did its job, every expression has a type. Lowering just translates `TypedAST node + type → IR node`. No inference, no checking, pure syntactic transformation.

| AST Node                  | IR Output                              |
| ------------------------- | -------------------------------------- |
| `BinOp(+, a, b)` : `int`  | `ir.BinOp(Add, lower(a), lower(b))`    |
| `Call(f, args)` : `T`     | `ir.Call(f, [lower(a) for a in args])` |
| `Attribute(obj, field)`   | `ir.FieldAccess(lower(obj), field)`    |

**Prior art:**
- [Syntax-Directed Translation](https://www.geeksforgeeks.org/compiler-design/syntax-directed-translation-in-compiler-design/) — semantic actions attached to grammar
- [Three-address code](https://en.wikipedia.org/wiki/Three-address_code) — classic IR format
- [Cornell CS 4120 IR notes](https://www.cs.cornell.edu/courses/cs4120/2023sp/notes/ir/) — IR design

**Simplification for Tongues:** TypedAST has all types attached. No need to call inference or look up tables. Just pattern-match on AST nodes and emit IR.

**Postconditions:** IR Module complete; all IR nodes typed; no AST remnants in output.
