# Middleend Redesign Plan

## Executive Summary

The middleend's core job is **dataflow analysis on a well-typed IR**. Given that the frontend will provide complete type information, the middleend should focus on:

1. **Variable scope and lifetime analysis** (current)
2. **Type flow analysis** at control flow join points (new)
3. **Enabling information** for backend code generation

This document outlines a principled approach based on established compiler theory.

---

## Background: Dataflow Analysis

### Core Concepts

Dataflow analysis computes properties at each program point by propagating information through the control flow graph (CFG). Key references:

- [CMU Dataflow Lecture Notes](https://www.cs.cmu.edu/~janh/courses/411/23/lec/16-dataflow.pdf)
- [Harvard CS153 Dataflow Analysis](https://groups.seas.harvard.edu/courses/cs153/2019fa/lectures/Lec20-Dataflow-analysis.pdf)
- [Wikipedia: Data-flow analysis](https://en.wikipedia.org/wiki/Data-flow_analysis)

### Classification

| Direction | May (∪)              | Must (∩)              |
| --------- | -------------------- | --------------------- |
| Forward   | Reaching definitions | Available expressions |
| Backward  | Live variables       | Very busy expressions |

At **join points** (where control flow merges), we take:
- **Union** for "may" analyses (any path)
- **Intersection** for "must" analyses (all paths)

### Lattice Theory

Types form a **lattice** with join (⊔) and meet (⊓) operations:
- **Top (⊤)**: least specific type (`any`)
- **Bottom (⊥)**: most specific / unreachable
- **Join**: least upper bound (union of types)

Analysis iterates to a **fixpoint** - when computed facts stop changing.

---

## SSA Form and Phi Functions

[Static Single Assignment (SSA)](https://en.wikipedia.org/wiki/Static_single-assignment_form) is the standard middleend representation where each variable is assigned exactly once.

### Phi Functions

At control flow merge points, **phi (φ) functions** select which value to use:

```
if cond:
    x₁ = "hello"
else:
    x₂ = 42
x₃ = φ(x₁, x₂)  # type: string | int
```

For type analysis, the phi node computes the **type union** of its inputs.

### Do We Need Full SSA?

**No.** Full SSA conversion requires:
1. Computing dominance frontiers
2. Placing phi nodes
3. Renaming all variables

This is overkill for our needs. Instead, we can do **flow-sensitive type tracking** without explicit SSA conversion:
- Track `var -> type` at each program point
- At joins, compute union types
- Annotate IR nodes with computed types

---

## Current Middleend Analysis

### What It Does Well

The current middleend (`middleend.py`) handles:

| Analysis               | Purpose                                              |
| ---------------------- | ---------------------------------------------------- |
| `is_declaration`       | First assignment to variable (for `let`/`:=` vs `=`) |
| `is_reassigned`        | Variable assigned after declaration                  |
| `is_modified`          | Parameter mutated in function body                   |
| `hoisted_vars`         | Variables needing hoisting from control flow blocks  |
| `initial_value_unused` | Dead store elimination opportunity                   |

### Current Limitations

1. **No type flow tracking** - Types are only captured at first assignment
2. **Incomplete hoisted_vars types** - `typ=None` when frontend doesn't provide
3. **No join point type computation** - Branches with different types not merged

---

## Parable.py Patterns Requiring Analysis

### Pattern 1: Nullable Variables

```python
else_body = None           # type: None
if condition:
    else_body = If(...)    # type: If
# Join: else_body: If | None
```

~20 occurrences in parable.py (grep `^\s+\w+\s*=\s*None\s*$`)

### Pattern 2: Branch-Varying Types

```python
if chars:
    word = "".join(chars)  # type: str
else:
    word = None            # type: None
# Join: word: str | None
```

### Pattern 3: Try/Catch Escaping Variables

```python
try:
    result = parse_something()  # type: Node
except:
    result = fallback()         # type: Node
# result used after try/catch - needs hoisting with correct type
```

7 try blocks in parable.py.

### Pattern 4: isinstance Narrowing (Already Handled)

```python
if isinstance(node, Word):
    # node: Word (narrowed from Node)
```

Frontend already handles this via `TypeSwitch` IR.

---

## Proposed Middleend Architecture

### Phase 1: CFG Construction (Optional)

Build explicit CFG if needed, or work directly on AST-like IR with implicit CFG.

Current IR structure already encodes control flow via:
- `If` with `then_body` / `else_body`
- `While`, `ForRange`, `ForClassic` with `body`
- `TryCatch` with `body` / `catch_body`
- `Match` / `TypeSwitch` with `cases` / `default`

### Phase 2: Type Flow Analysis

**Goal**: Compute the type of each variable at each use site.

```python
@dataclass
class TypeFlowState:
    """Type environment at a program point."""
    var_types: dict[str, Type]  # var name -> type at this point

def join_states(s1: TypeFlowState, s2: TypeFlowState) -> TypeFlowState:
    """Merge type environments at control flow join."""
    result = {}
    all_vars = set(s1.var_types) | set(s2.var_types)
    for var in all_vars:
        t1 = s1.var_types.get(var)
        t2 = s2.var_types.get(var)
        result[var] = join_types(t1, t2)
    return TypeFlowState(result)
```

**Type Join Rules**:

| t1           | t2           | t1 ⊔ t2                             |
| ------------ | ------------ | ----------------------------------- |
| T            | T            | T                                   |
| T            | None         | Optional(T)                         |
| None         | T            | Optional(T)                         |
| StructRef(A) | StructRef(B) | Interface("Node") if both are nodes |
| Interface(X) | Interface(Y) | Interface(common) or Union          |

### Phase 3: Annotations

Annotate IR nodes with computed information:

```python
# On Var nodes
var.flow_type: Type  # Type at this use site

# On Assign nodes (already exists)
assign.is_declaration: bool

# On If/TryCatch/While/ForRange (already exists)
stmt.hoisted_vars: list[tuple[str, Type]]  # Now with complete types

# New: On function bodies
func.var_flow_types: dict[str, list[tuple[Loc, Type]]]  # Optional: full flow info
```

---

## Implementation Plan

### Step 1: Type Join Function

Implement proper type joining in `middleend.py`:

```python
def join_types(t1: Type | None, t2: Type | None) -> Type:
    """Compute least upper bound of two types."""
    if t1 is None and t2 is None:
        return Interface("any")  # Both None → any
    if t1 is None:
        return Optional(t2) if not isinstance(t2, Optional) else t2
    if t2 is None:
        return Optional(t1) if not isinstance(t1, Optional) else t1
    if t1 == t2:
        return t1
    # Handle structural subtyping...
```

Current `_merge_types` is a start but incomplete.

### Step 2: Forward Type Flow Pass

Walk each function forward, tracking types:

```python
def analyze_type_flow(func: Function) -> None:
    state = TypeFlowState({p.name: p.typ for p in func.params})
    analyze_stmts(func.body, state)

def analyze_stmts(stmts: list[Stmt], state: TypeFlowState) -> TypeFlowState:
    for stmt in stmts:
        state = analyze_stmt(stmt, state)
    return state

def analyze_stmt(stmt: Stmt, state: TypeFlowState) -> TypeFlowState:
    if isinstance(stmt, Assign):
        # Update state with new type
        if isinstance(stmt.target, VarLV):
            state.var_types[stmt.target.name] = stmt.value.typ
    elif isinstance(stmt, If):
        then_state = analyze_stmts(stmt.then_body, state.copy())
        else_state = analyze_stmts(stmt.else_body, state.copy())
        state = join_states(then_state, else_state)
    # ... etc
    return state
```

### Step 3: Hoisted Variable Types

Use flow analysis to determine hoisted variable types:

```python
def compute_hoisted_types(stmt: If | TryCatch, outer_state: TypeFlowState):
    # Analyze both branches
    branch_states = [analyze_stmts(branch, outer_state.copy()) for branch in branches]

    # Find variables first assigned in branches
    new_vars = find_new_vars(branches, outer_state)

    # Compute joined type for each
    hoisted = []
    for var in new_vars:
        types = [s.var_types.get(var) for s in branch_states]
        joined = reduce(join_types, types)
        hoisted.append((var, joined))

    stmt.hoisted_vars = hoisted
```

### Step 4: Annotate Var References

Optionally annotate each `Var` node with its flow type:

```python
def annotate_var_types(stmts: list[Stmt], state: TypeFlowState) -> None:
    for stmt in stmts:
        visit_exprs(stmt, lambda e: annotate_expr(e, state))
        # Update state and recurse...

def annotate_expr(expr: Expr, state: TypeFlowState) -> None:
    if isinstance(expr, Var):
        expr.flow_type = state.var_types.get(expr.name, expr.typ)
```

---

## Module Structure

### Package Layout

```
transpiler/src/middleend/
├── __init__.py        # analyze(module) - orchestrates all analyses
├── scope.py           # is_declaration, is_reassigned, is_modified, is_unused
├── liveness.py        # initial_value_unused, catch_var_unused, binding_unused, unused_indices
├── hoisting.py        # hoisted_vars computation
├── type_flow.py       # Type join at control flow merges (new)
└── returns.py         # has_returns, has_catch_returns, needs_named_returns
```

### Design Principles

1. **One file per analysis** - Each module is self-contained, ~100-200 lines
2. **No shared framework** - Each analysis has its own loop; a generic framework costs more than it saves for 5 analyses
3. **No cross-imports between analyses** - Analyses never import each other
4. **Results as parameters** - If analysis B needs A's results, pass them explicitly
5. **Analyses return data** - Don't mutate IR; the runner applies annotations

### Analysis Interface

Each analysis module exports a single function:

```python
# scope.py
@dataclass
class ScopeResults:
    declarations: dict[str, bool]      # var name -> is first assignment
    reassignments: dict[str, bool]     # var name -> is reassigned
    modified_params: set[str]          # param names that are modified
    unused_params: set[str]            # param names never referenced

def analyze_scope(func: Function) -> ScopeResults:
    """Analyze variable declarations and parameter usage."""
    ...
```

```python
# hoisting.py
@dataclass
class HoistedVar:
    name: str
    typ: Type
    stmt: Stmt  # The If/TryCatch/While that needs this hoisted

def analyze_hoisting(func: Function, scope: ScopeResults) -> list[HoistedVar]:
    """Find variables needing hoisting, with complete types."""
    ...
```

### Runner

The `__init__.py` orchestrates analyses in dependency order:

```python
# middleend/__init__.py
from .scope import analyze_scope
from .liveness import analyze_liveness
from .hoisting import analyze_hoisting
from .type_flow import analyze_type_flow
from .returns import analyze_returns

def analyze(module: Module) -> None:
    """Run all analyses, annotating IR in place."""
    for func in _all_functions(module):
        # Phase 1: Scope analysis (no dependencies)
        scope = analyze_scope(func)
        _apply_scope_annotations(func, scope)

        # Phase 2: Liveness analysis (no dependencies)
        liveness = analyze_liveness(func)
        _apply_liveness_annotations(func, liveness)

        # Phase 3: Return analysis (no dependencies)
        returns = analyze_returns(func)
        _apply_return_annotations(func, returns)

        # Phase 4: Type flow (depends on scope for is_declaration)
        type_flow = analyze_type_flow(func, scope)
        _apply_type_flow_annotations(func, type_flow)

        # Phase 5: Hoisting (depends on scope + type_flow)
        hoisting = analyze_hoisting(func, scope, type_flow)
        _apply_hoisting_annotations(func, hoisting)
```

### Dependencies

```
scope.py ──────────────┬──────────────> hoisting.py
                       │
liveness.py            │
                       │
returns.py             │
                       │
type_flow.py ──────────┘
```

- `scope.py`, `liveness.py`, `returns.py` are independent
- `type_flow.py` needs scope results (to know when variables are declared)
- `hoisting.py` needs scope + type_flow (to get complete types)

### Testing

One test file per analysis in `transpiler/tests/middleend/`:

```
transpiler/tests/middleend/
├── test_scope.py
├── test_liveness.py
├── test_hoisting.py
├── test_type_flow.py
└── test_returns.py
```

Each test file uses small synthetic IR fixtures:

```python
# test_scope.py
def test_simple_declaration():
    func = make_func([
        Assign(VarLV("x"), IntLit(1, typ=INT)),
        Assign(VarLV("x"), IntLit(2, typ=INT)),
    ])
    result = analyze_scope(func)
    assert result.declarations["x"] == True  # First assign is declaration
    assert result.reassignments["x"] == True  # Second assign is reassignment
```

No integration tests initially - existing backend tests catch regressions.

---

## What NOT to Include

The middleend should **not** do:

1. **Optimizations** - No constant folding, dead code elimination, etc. (leave for future)
2. **Source language knowledge** - No Python-specific patterns
3. **Target language knowledge** - No Go/TS/Java-specific concerns
4. **Transformations** - Read-only analysis, only adds annotations

---

## Testing Strategy

1. **Unit tests per analysis** (`transpiler/tests/middleend/test_*.py`):
   - Small synthetic IR fixtures
   - Test each analysis in isolation
   - Example: `test_scope.py`, `test_type_flow.py`, etc.

2. **Unit tests for `join_types`** (in `test_type_flow.py`):
   ```python
   assert join_types(STRING, None) == Optional(STRING)
   assert join_types(StructRef("Word"), StructRef("Command")) == Interface("Node")
   ```

3. **Regression tests** (existing backend tests):
   - Transpiled output should be identical or improved
   - No new `interface{}` or `any` in generated code
   - All `hoisted_vars` should have non-None types

---

## Summary

| Component          | Current                  | Proposed                            |
| ------------------ | ------------------------ | ----------------------------------- |
| Structure          | Single `middleend.py`    | `middleend/` package, 5 modules     |
| Type source        | Frontend only            | Frontend + flow analysis            |
| Join computation   | Ad-hoc `_merge_types`    | Principled lattice join             |
| Hoisted var types  | Sometimes None           | Always complete                     |
| Var use-site types | Not tracked              | Optionally annotated                |
| SSA form           | Not used                 | Not needed (flow analysis suffices) |
| Dependencies       | Implicit (function order)| Explicit (passed as parameters)     |
| Testing            | None                     | Unit tests per analysis             |

The key insight is that we don't need full SSA conversion or a complex pass framework - flow-sensitive type tracking with proper join semantics and simple modular structure is sufficient for our use case.
