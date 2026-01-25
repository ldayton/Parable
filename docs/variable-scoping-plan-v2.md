# Variable Scoping Plan v2

Simplified approach based on patterns from py2many and pytago.

## Current State

```go
func example() string {
    var x string
    _ = x              // 802 of these in parable.go
    var y int
    _ = y
    // ... actual code
}
```

## Goal

```go
func example() string {
    x := computeX()
    if cond {
        x = updateX(x)
    }
    var y int          // only when truly needed
    if other {
        y = 42
    }
    return x + y
}
```

## Key Insight from py2many

You don't need full LCA/scope-tree computation. Two simple passes handle 95% of cases:

1. **Track declared vars** - use `:=` first time, `=` after
2. **Detect if/else common vars** - hoist only these

## Algorithm

### Data Structure

```python
@dataclass
class VarState:
    declared: bool = False          # has := been emitted?
    needs_hoist: bool = False       # must use var at function top?
    go_type: str = "interface{}"
```

### Pass 1: Detect Hoisting Needs

Only two patterns require hoisting:

**Pattern A: Assigned in both if and else, read outside**
```python
if cond:
    x = 1    # assigned in if
else:
    x = 2    # assigned in else
print(x)     # read outside → hoist
```

**Pattern B: Assigned only in inner scope, read outside**
```python
if cond:
    x = 1    # assigned in if only
print(x)     # read outside → hoist
```

Detection (borrowed from py2many):

```python
def collect_hoist_vars(stmts: list[ast.stmt]) -> set[str]:
    """Find variables that need hoisting."""
    hoist = set()

    for stmt in stmts:
        if isinstance(stmt, ast.If):
            body_assigns = collect_assigns(stmt.body)
            else_assigns = collect_assigns(stmt.orelse)
            body_reads = collect_reads(stmt.body)
            else_reads = collect_reads(stmt.orelse)

            # Pattern A: assigned in both branches
            common = body_assigns & else_assigns

            # Pattern B: assigned in one branch only
            one_branch = (body_assigns - else_assigns) | (else_assigns - body_assigns)

            # Check if read after the if statement
            after_reads = collect_reads(stmts[stmts.index(stmt)+1:])
            hoist |= (common | one_branch) & after_reads

            # Recurse
            hoist |= collect_hoist_vars(stmt.body)
            hoist |= collect_hoist_vars(stmt.orelse)

        elif isinstance(stmt, ast.While):
            # Variables assigned in loop, read after → hoist
            loop_assigns = collect_assigns(stmt.body)
            after_reads = collect_reads(stmts[stmts.index(stmt)+1:])
            hoist |= loop_assigns & after_reads
            hoist |= collect_hoist_vars(stmt.body)

        # Similar for For, Try, With...

    return hoist
```

### Pass 2: Emit with Tracking

```python
class EmitState:
    declared: set[str]      # variables that have been declared
    hoisted: set[str]       # variables that were hoisted at function top

def emit_function_body(stmts, func_info):
    state = EmitState(
        declared=set(p.name for p in func_info.params),
        hoisted=collect_hoist_vars(stmts)
    )

    # Emit hoisted declarations
    for var in state.hoisted:
        go_type = infer_type(var, stmts)
        emit(f"var {var} {go_type}")
        state.declared.add(var)

    # Emit body
    emit_stmts(stmts, state)

def emit_assign(var: str, value: str, state: EmitState):
    if var in state.declared:
        emit(f"{var} = {value}")
    else:
        emit(f"{var} := {value}")
        state.declared.add(var)
```

## Implementation

### Step 1: Add `collect_assigns` and `collect_reads`

```python
def _collect_assigns(self, stmts: list[ast.stmt]) -> set[str]:
    """Collect variable names assigned in these statements (non-recursive)."""
    assigns = set()
    for stmt in stmts:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    assigns.add(self._to_go_var_name(target.id))
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            assigns.add(self._to_go_var_name(stmt.target.id))
    return assigns

def _collect_reads(self, stmts: list[ast.stmt]) -> set[str]:
    """Collect variable names read in these statements."""
    reads = set()
    for stmt in stmts:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                reads.add(self._to_go_var_name(node.id))
    return reads
```

### Step 2: Add `collect_hoist_vars`

```python
def _collect_hoist_vars(self, stmts: list[ast.stmt]) -> set[str]:
    """Find variables needing hoisting due to scope issues."""
    hoist = set()

    for i, stmt in enumerate(stmts):
        after = stmts[i+1:]
        after_reads = self._collect_reads(after)

        if isinstance(stmt, ast.If):
            body_assigns = self._collect_assigns(stmt.body)
            else_assigns = self._collect_assigns(stmt.orelse) if stmt.orelse else set()

            # Assigned in branch(es), read after → hoist
            branch_assigns = body_assigns | else_assigns
            hoist |= branch_assigns & after_reads

            # Recurse into branches
            hoist |= self._collect_hoist_vars(stmt.body)
            if stmt.orelse:
                hoist |= self._collect_hoist_vars(stmt.orelse)

        elif isinstance(stmt, ast.While):
            loop_assigns = self._collect_assigns(stmt.body)
            hoist |= loop_assigns & after_reads
            hoist |= self._collect_hoist_vars(stmt.body)

        elif isinstance(stmt, ast.For):
            loop_assigns = self._collect_assigns(stmt.body)
            hoist |= loop_assigns & after_reads
            hoist |= self._collect_hoist_vars(stmt.body)

        elif isinstance(stmt, ast.Try):
            for handler in stmt.handlers:
                handler_assigns = self._collect_assigns(handler.body)
                hoist |= handler_assigns & after_reads
                hoist |= self._collect_hoist_vars(handler.body)
            if stmt.orelse:
                hoist |= self._collect_hoist_vars(stmt.orelse)
            if stmt.finalbody:
                hoist |= self._collect_hoist_vars(stmt.finalbody)

    return hoist
```

### Step 3: Replace `_predeclare_all_locals`

```python
def _emit_function_locals(self, stmts: list[ast.stmt]):
    """Emit only necessary hoisted declarations."""
    self.hoisted_vars = self._collect_hoist_vars(stmts)

    for var in sorted(self.hoisted_vars):
        go_type = self._infer_var_type(var, stmts)
        self.emit(f"var {var} {go_type}")
        self.declared_vars.add(var)
```

### Step 4: Update `_emit_stmt_Assign`

```python
def _emit_stmt_Assign(self, stmt: ast.Assign):
    target = stmt.targets[0]
    if isinstance(target, ast.Name):
        var = self._to_go_var_name(target.id)
        value = self.visit_expr(stmt.value)

        if var in self.declared_vars:
            self.emit(f"{var} = {value}")
        else:
            self.emit(f"{var} := {value}")
            self.declared_vars.add(var)
    # ... handle tuple targets, etc.
```

### Step 5: Delete `_ = x` emissions

Remove all lines like:
```python
self.emit(f"_ = {var_name}")
```

## Type Inference for Hoisted Vars

Hoisted vars need explicit types. Reuse existing `_infer_var_type`:

```python
def _infer_var_type(self, var: str, stmts: list[ast.stmt]) -> str:
    """Infer Go type from first assignment."""
    for stmt in stmts:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and self._to_go_var_name(target.id) == var:
                    return self._infer_type_from_expr(stmt.value)
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name) and self._to_go_var_name(stmt.target.id) == var:
                if stmt.annotation:
                    return self._py_type_to_go(ast.unparse(stmt.annotation))
        elif isinstance(stmt, (ast.If, ast.While, ast.For)):
            # Recurse
            result = self._infer_var_type(var, stmt.body)
            if result != "interface{}":
                return result
            if hasattr(stmt, 'orelse') and stmt.orelse:
                result = self._infer_var_type(var, stmt.orelse)
                if result != "interface{}":
                    return result
    return "interface{}"
```

## Edge Cases

### Tuple Unpacking

Keep current behavior - always use `:=`:
```go
a, b := funcReturningTuple()
```

### For Loop Variables

Keep current behavior - range handles declaration:
```go
for _, item := range items {
```

### Augmented Assignment

`x += 1` requires `x` to exist. If first use is augmented:
```python
def _collect_assigns(self, stmts):
    # ...
    if isinstance(stmt, ast.AugAssign):
        if isinstance(stmt.target, ast.Name):
            # AugAssign is both read and write - don't count as first assign
            pass
```

### Multiple Assignment Targets

`a = b = 1` - rare, handle by hoisting both if needed.

## Comparison to v1 Plan

| Aspect | v1 Plan | v2 Plan |
|--------|---------|---------|
| Scope tracking | Full tree with IDs, LCA | None needed |
| Hoisting detection | Generic algorithm | Pattern matching |
| Lines of code | ~150 new | ~80 new |
| Complexity | High | Low |
| Coverage | 100% | 95% (good enough) |

## Testing

1. `go build` succeeds
2. `grep -c '_ =' parable.go` → 0 (down from 802)
3. `grep -c ':=' parable.go` → majority of assignments
4. `grep -c '^[[:space:]]*var ' parable.go` → small number (hoisted only)
5. Test suite passes

## Rollout

1. Implement in `transpile_go.py`
2. Run `just transpile`
3. Run `go build ./...`
4. Run test suite
5. Compare output diff - should be cleaner, semantically equivalent
