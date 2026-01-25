# Variable Scoping Fix Plan

## Problem

The transpiler emits C-style pre-declarations for all variables:

```go
func example() string {
    var x string
    _ = x              // 802 of these in parable.go
    var y int
    _ = y
    // ... actual code
}
```

This avoids Go's block-scoping issues but produces ugly, un-idiomatic output.

## Goal

Emit idiomatic Go:

```go
func example() string {
    x := computeX()           // := at first use
    if cond {
        x = updateX(x)        // = for reassignment
    }
    var y int                 // hoisted: assigned in block, used outside
    if other {
        y = 42
    }
    return x + y
}
```

## The Core Problem

Go has block-level scoping. Python has function-level scoping.

```python
# Python: x exists after the if
if cond:
    x = 1
print(x)  # works (if cond was true)
```

```go
// Go: x does NOT exist after the if
if cond {
    x := 1
}
fmt.Println(x)  // ERROR: undefined x
```

## Algorithm: Scope-Aware Declaration

### Data Structures

```python
@dataclass
class VarInfo:
    name: str
    go_type: str
    assign_scopes: set[int]   # ALL scope IDs where assigned
    read_scopes: set[int]     # scope IDs where read

@dataclass
class ScopeInfo:
    id: int
    parent: int | None        # None for function scope (root)
    depth: int                # 0 for function scope

# Scope tree (simplified)
# scope 0 = function body (depth 0)
# scope 1 = first if block (depth 1, parent 0)
# scope 2 = else block (depth 1, parent 0)
# scope 3 = nested if inside scope 1 (depth 2, parent 1)
```

### Helper Functions

```python
def scope_depth(scope_id, scope_tree) -> int:
    return scope_tree[scope_id].depth

def is_ancestor(ancestor, descendant, scope_tree) -> bool:
    """True if ancestor is a proper ancestor of descendant."""
    current = scope_tree[descendant].parent
    while current is not None:
        if current == ancestor:
            return True
        current = scope_tree[current].parent
    return False

def is_ancestor_or_equal(ancestor, descendant, scope_tree) -> bool:
    return ancestor == descendant or is_ancestor(ancestor, descendant, scope_tree)

def compute_lca(scope_ids, scope_tree) -> int:
    """Compute lowest common ancestor of a set of scopes."""
    if len(scope_ids) == 1:
        return next(iter(scope_ids))
    # Get ancestors for each scope (including self)
    def ancestors(s):
        result = {s}
        current = scope_tree[s].parent
        while current is not None:
            result.add(current)
            current = scope_tree[current].parent
        return result
    common = ancestors(next(iter(scope_ids)))
    for s in scope_ids:
        common &= ancestors(s)
    # Return deepest common ancestor
    return max(common, key=lambda s: scope_tree[s].depth)
```

### Pass 1: Collect Variable Usage

Walk the AST and record, for each variable:
- Which scopes it's assigned in
- Which scopes it's read in
- The scope of its first assignment

```python
def collect_var_usage(stmts, scope_id, var_info):
    for stmt in stmts:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    var = target.id
                    var_info[var].assign_scopes.add(scope_id)
                    if var_info[var].first_assign_scope is None:
                        var_info[var].first_assign_scope = scope_id

        if isinstance(stmt, ast.If):
            collect_var_usage(stmt.body, new_scope_id(), var_info)
            collect_var_usage(stmt.orelse, new_scope_id(), var_info)

        # Also collect reads from all expressions
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name) and is_read_context(node):
                var_info[node.id].read_scopes.add(scope_id)
```

### Pass 2: Determine Declaration Strategy

For each variable, decide:

1. **Inline `:=`** — if all assignments AND reads are in the same scope (or nested within first assignment's scope)
2. **Hoist `var`** — if assignments occur in sibling scopes, OR reads occur in outer scope relative to assignments

```python
def needs_hoisting(var_info, scope_tree):
    """Returns (needs_hoist, hoist_to_scope_id)"""
    all_scopes = var_info.assign_scopes | var_info.read_scopes
    lca = compute_lca(all_scopes, scope_tree)

    # Case 1: Assignments in sibling/divergent branches (e.g., if/else)
    # Must hoist if LCA is not one of the assignment scopes
    if lca not in var_info.assign_scopes:
        return (True, lca)

    # Case 2: Assignment in inner scope, read in outer scope
    for assign_scope in var_info.assign_scopes:
        for read_scope in var_info.read_scopes:
            if not is_ancestor_or_equal(assign_scope, read_scope, scope_tree):
                return (True, lca)

    # Case 3: Multiple assignments where inner would shadow outer
    # e.g., x=1 at scope 0, x=2 inside if (scope 1)
    # The first := at scope 1 would make scope 0's assignment fail
    if len(var_info.assign_scopes) > 1:
        min_scope = min(var_info.assign_scopes, key=lambda s: scope_depth(s, scope_tree))
        for scope in var_info.assign_scopes:
            if scope != min_scope and not is_ancestor(min_scope, scope, scope_tree):
                return (True, lca)

    return (False, None)
```

### Pass 3: Emit Code

Track declared variables per scope. Emit `:=` or `=` based on whether variable is already declared.

```python
class EmitState:
    declared: set[str]  # variables declared at current scope or above
    hoisted: dict[str, int]  # var -> scope_id where it should be declared

def emit_assignment(var, value, current_scope, state):
    if var in state.declared:
        emit(f"{var} = {value}")
    elif state.hoisted.get(var) == current_scope:
        # This is where we should declare it
        emit(f"var {var} {infer_type(value)}")
        emit(f"{var} = {value}")
        state.declared.add(var)
    else:
        # First use, inline declaration
        emit(f"{var} := {value}")
        state.declared.add(var)
```

## What Existing Code Handles Correctly

The current `_collect_all_assignments` already handles:
- `ast.Assign` — regular assignments
- `ast.AnnAssign` — annotated assignments (`x: int = 0`)
- `ast.Tuple` targets — tuple unpacking (skipped, uses `:=`)
- `ast.For` targets — loop variables (skipped, handled by range syntax)
- `ast.With` variables — context manager `as` targets
- `ast.Try` / `except ... as e` — exception handler variables
- Recursive traversal into `If`, `While`, `For`, `Try` bodies

**Not handled but not needed for parable.py:**
- `ast.AugAssign` — no variable's first assignment is AugAssign
- `ast.NamedExpr` — walrus operator not used
- Multiple targets (`a = b = 1`) — only 1 case, in a SKIP_BODY function

## Implementation Steps

### Step 1: Add Scope Tracking Data Structures

Add to `GoTranspiler.__init__`:

```python
def __init__(self):
    # ... existing fields ...
    self.scope_tree: dict[int, ScopeInfo] = {}
    self.next_scope_id: int = 0
    self.var_usage: dict[str, VarInfo] = {}
    self.hoisted_vars: dict[str, int] = {}  # var -> scope_id to declare at
```

### Step 2: Modify `_collect_all_assignments` to Track Scopes

Replace the flat collection with scope-aware collection:

```python
def _collect_var_scopes(self, stmts: list[ast.stmt], scope_id: int):
    """Collect variable assignment/read scopes recursively."""
    for stmt in stmts:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    var = self._to_go_var_name(target.id)
                    self._record_assign(var, scope_id, stmt.value)
                # Tuple targets handled separately (use :=)

        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            var = self._to_go_var_name(stmt.target.id)
            self._record_assign(var, scope_id, stmt.value)

        elif isinstance(stmt, ast.If):
            # Recurse with new scope IDs for each branch
            then_scope = self._new_scope(parent=scope_id)
            self._collect_var_scopes(stmt.body, then_scope)
            if stmt.orelse:
                else_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.orelse, else_scope)

        elif isinstance(stmt, ast.While):
            body_scope = self._new_scope(parent=scope_id)
            self._collect_var_scopes(stmt.body, body_scope)

        elif isinstance(stmt, ast.For):
            # Loop var handled by range syntax, just recurse
            body_scope = self._new_scope(parent=scope_id)
            self._collect_var_scopes(stmt.body, body_scope)

        # ... similar for Try, With ...

        # Collect reads from all expressions in this statement
        self._collect_reads(stmt, scope_id)

def _record_assign(self, var: str, scope_id: int, value: ast.expr | None):
    if var not in self.var_usage:
        self.var_usage[var] = VarInfo(var, "", set(), set())
    self.var_usage[var].assign_scopes.add(scope_id)
    # Infer type from first assignment
    if not self.var_usage[var].go_type and value:
        self.var_usage[var].go_type = self._infer_type_from_expr(value)

def _new_scope(self, parent: int) -> int:
    scope_id = self.next_scope_id
    self.next_scope_id += 1
    parent_depth = self.scope_tree[parent].depth if parent in self.scope_tree else -1
    self.scope_tree[scope_id] = ScopeInfo(scope_id, parent, parent_depth + 1)
    return scope_id
```

### Step 3: Compute Hoisting After Collection

```python
def _compute_hoisting(self):
    """Determine which vars need hoisting vs inline :="""
    for var, info in self.var_usage.items():
        needs_hoist, hoist_scope = self._needs_hoisting(info)
        if needs_hoist:
            self.hoisted_vars[var] = hoist_scope
```

### Step 4: Emit with Scope Awareness

Modify `_emit_body` to:
1. Initialize scope 0 for function body
2. Call `_collect_var_scopes` and `_compute_hoisting` upfront
3. Emit hoisted declarations at scope 0
4. Track current scope during emission

```python
def _emit_body(self, stmts, func_info):
    # Reset state
    self.scope_tree = {0: ScopeInfo(0, None, 0)}
    self.next_scope_id = 1
    self.var_usage = {}
    self.hoisted_vars = {}
    self.declared_vars = set(p.name for p in func_info.params) if func_info else set()

    # Analyze scopes
    self._collect_var_scopes(stmts, scope_id=0)
    self._compute_hoisting()

    # Emit hoisted declarations for scope 0
    for var, hoist_scope in self.hoisted_vars.items():
        if hoist_scope == 0:
            go_type = self.var_usage[var].go_type or "interface{}"
            self.emit(f"var {var} {go_type}")
            self.declared_vars.add(var)

    # Emit statements
    self._emit_stmts(stmts, scope_id=0)
```

### Step 5: Update Assignment Emission

```python
def _emit_stmt_Assign(self, stmt, scope_id: int):
    target = stmt.targets[0]
    if isinstance(target, ast.Name):
        var = self._to_go_var_name(target.id)
        value = self.visit_expr(stmt.value)

        # Check if we need to emit hoisted declaration here
        if var in self.hoisted_vars and self.hoisted_vars[var] == scope_id:
            if var not in self.declared_vars:
                go_type = self.var_usage[var].go_type or "interface{}"
                self.emit(f"var {var} {go_type}")
                self.declared_vars.add(var)

        if var in self.declared_vars:
            self.emit(f"{var} = {value}")
        else:
            self.emit(f"{var} := {value}")
            self.declared_vars.add(var)
```

### Step 6: Thread Scope ID Through Emission

All `_emit_stmt_*` methods need to accept and propagate `scope_id`:

```python
def _emit_stmt_If(self, stmt, scope_id: int):
    self.emit(f"if {self._emit_bool_expr(stmt.test)} {{")
    self.indent += 1
    then_scope = self._get_then_scope(stmt, scope_id)  # lookup from collection phase
    self._emit_scope_hoisted_vars(then_scope)
    self._emit_stmts(stmt.body, then_scope)
    self.indent -= 1
    # ... else handling ...
```

### Step 7: Remove `_ = x` Suppressions

Delete these lines from `_predeclare_all_locals` (which is now `_collect_var_scopes`):
```python
# DELETE:
self.emit(f"_ = {var_name}")
```

### Key Implementation Detail: Scope ID Mapping

The collection pass and emission pass must agree on scope IDs. Two approaches:

**Option A: Deterministic IDs (simpler)**
Assign scope IDs in AST traversal order. Both passes use identical traversal, so IDs match.

**Option B: AST node mapping (robust)**
Store scope ID on AST nodes during collection:
```python
# During collection
stmt._scope_id = scope_id

# During emission
scope_id = stmt._scope_id
```

Recommend **Option A** for simplicity. The traversal order is deterministic (statements in order, if-body before else-body, etc.).

## Edge Cases

### 1. Multiple Assignment Branches

```python
if cond:
    x = 1
else:
    x = 2
print(x)
```

Both branches assign `x`, read is outside. Hoist to function scope:

```go
var x int
if cond {
    x = 1
} else {
    x = 2
}
fmt.Println(x)
```

### 2. Tuple Unpacking

```python
a, b = func_returning_tuple()
```

Both `a` and `b` are assigned at same scope. Use `:=` for both:

```go
a, b := funcReturningTuple()
```

### 3. Assignments in Multiple Scopes

```python
if cond:
    x = 1
x = 2  # also assigned at outer scope
```

Assignments occur in both scope 0 (outer) and scope 1 (if-block). The algorithm detects this:
- `assign_scopes = {0, 1}`
- LCA of {0, 1} = 0
- Scope 0 IS in assign_scopes, but scope 1 is not an ancestor of scope 0
- Therefore: **must hoist**

```go
var x int
if cond {
    x = 1
}
x = 2
```

Without hoisting, `x := 1` inside the if would create a new variable scoped to that block, and `x = 2` outside would fail (undefined).

### 4. Loop Variables

```python
for item in items:
    process(item)
```

`item` is scoped to the loop in Go, which matches Python. Use `:=`:

```go
for _, item := range items {
    process(item)
}
```

## Complexity Assessment

### What Changes
- `_collect_all_assignments` → `_collect_var_scopes` (add scope tracking)
- `_emit_body` → add hoisting computation and scope-aware emission
- `_emit_stmt_Assign` → use `:=` vs `=` based on declared state
- All `_emit_stmt_*` methods → thread scope_id parameter

### Risk Areas
1. **Scope ID consistency** — Collection and emission must use same scope IDs. Solution: Store scope assignments on first pass, lookup on second.
2. **Tuple unpacking** — Currently uses `:=` always. Keep this behavior (correct for Go).
3. **Type inference** — Hoisted vars need types. Existing `_infer_type_from_expr` should work.

### Lines of Code Estimate
- New: ~100 lines (scope tracking, LCA computation, hoisting logic)
- Modified: ~50 lines (threading scope_id, changing = to :=)
- Deleted: ~20 lines (`_ = x` suppression)

## Testing

1. Compile `parable.go` — must have 0 errors
2. Count `_ = ` lines — target: 0 (down from 802)
3. Count `var ` declarations — should decrease significantly (only hoisted vars)
4. Count `:=` declarations — should be majority of assignments
5. Run test suite — output must match Python

### Test Cases to Add

```python
# test_scope_simple.py - var used only in one scope
def f():
    x = 1
    return x
# Expected: x := 1

# test_scope_if_else.py - var assigned in both branches, read outside
def f():
    if cond:
        x = 1
    else:
        x = 2
    return x
# Expected: var x int; if cond { x = 1 } else { x = 2 }

# test_scope_inner_outer.py - var assigned in inner and outer
def f():
    if cond:
        x = 1
    x = 2
    return x
# Expected: var x int; if cond { x = 1 }; x = 2

# test_scope_nested.py - deeply nested but same logical scope
def f():
    if a:
        if b:
            x = 1
    return x
# Expected: var x int (hoisted to function scope)
```

## Rollout

1. Implement behind a flag `--idiomatic-vars`
2. Generate both versions, diff to verify semantic equivalence
3. Run full test suite with flag enabled
4. Verify `go build` succeeds
5. Make it the default
6. Remove old `_predeclare_all_locals` code
