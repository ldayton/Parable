# Middle-End Enhancements for C# Compilation (20 errors → 0)

## Current Status
Previous backend fixes reduced errors from 26 → 20. Remaining errors require middle-end/IR fixes.

## Error Summary

| Category | Count | Error Code | Root Cause |
|----------|-------|------------|------------|
| Variable shadowing | 3 | CS0136 | Loop vars `ch`/`op` shadow outer scope vars |
| Hoisted type loss | 5 | CS1503/CS0266 | Hoisted vars typed as `object` not element type |
| BraceGroup narrowing | 9 | CS0029/CS0266 | Variable needs `INode` not first-assigned type |
| Python API patterns | 2 | CS1503 | `str.endswith(tuple)`, `sep.join(list)` |
| Constructor args | 1 | CS7036 | Factory function not forwarding args |

---

## Fix 1: Variable Shadowing (3 errors)

**Problem:** C# forbids loop variables shadowing outer scope variables.
```csharp
string ch = "";           // outer scope
foreach (var _c3 in line) {
    var ch = _c3.ToString();  // CS0136: shadows outer 'ch'
}
```

**Solution:** Enhance hoisting pass to detect shadowing and annotate ForRange with renamed variables.

**File:** `src/middleend/hoisting.py`

Add to ForRange analysis:
```python
# Track outer scope variables, detect conflicts with loop vars
ForRange.value_shadows: bool  # True if value var shadows outer scope
ForRange.index_shadows: bool  # True if index var shadows outer scope
```

**File:** `src/backend/csharp.py`

When emitting ForRange, if `value_shadows` is True, use the temp variable pattern and don't redeclare:
```python
if stmt.value_shadows:
    # Don't use 'var', just assign to existing variable
    self._line(f"{val} = {temp_var}.ToString();")
```

---

## Fix 2: Hoisted Type Loss (5 errors)

**Problem:** When loop variables are hoisted, the element type is lost and defaults to `object`.
```csharp
object op;  // Hoisted, but should be 'string'
foreach (object op in assignOps) {  // CS1503: object not string
```

**Solution:** Track element types through ForRange hoisting.

**File:** `src/middleend/hoisting.py`

In `_vars_first_assigned_in()` and `_analyze_stmts()`:
```python
# When a ForRange loop var is hoisted, compute element type from iterable
if isinstance(stmt, ForRange) and stmt.value:
    if isinstance(stmt.iterable.typ, Slice):
        elem_type = stmt.iterable.typ.element
    elif isinstance(stmt.iterable.typ, Primitive) and stmt.iterable.typ.kind == "string":
        elem_type = Primitive("string")  # Character iteration
    # Include (name, elem_type) in hoisted_vars instead of (name, None)
```

---

## Fix 3: BraceGroup Type Narrowing (9 errors)

**Problem:** Variable typed as `BraceGroup` but assigned `If`, `While`, etc.
```csharp
BraceGroup result = ParseBraceGroup();
result = ParseIf();  // CS0029: If cannot convert to BraceGroup
```

**Solution:** Use `Assign.decl_typ` which already exists for this purpose.

**File:** `src/backend/csharp.py`

In `_emit_stmt()` Assign case, use `decl_typ` when available:
```python
case Assign(target=target, value=value):
    # Use decl_typ if set (unified type from frontend)
    if stmt.decl_typ:
        cs_type = self._type(stmt.decl_typ)
    elif stmt.is_declaration:
        cs_type = self._type(value.typ) if value.typ else "object"
```

**Also check:** VAR_TYPE_OVERRIDES in `src/frontend/type_overrides.py` may already have the override for `_parse_compound_command.result` → `InterfaceRef("Node")`. Verify it's being applied.

---

## Fix 4: Python API Patterns (2 errors)

### 4a: `str.endswith(tuple)` (1 error)

**Problem:** Python `s.endswith((" ", "\n"))` checks against multiple suffixes.

**File:** `src/backend/csharp.py` in `_method_call()`

```python
if method == "endswith":
    if args and isinstance(args[0], TupleLit):
        # Emit: s.EndsWith(" ") || s.EndsWith("\n")
        checks = [f"{obj_str}.EndsWith({self._expr(e)})" for e in args[0].elements]
        return "(" + " || ".join(checks) + ")"
    return f"{obj_str}.EndsWith({args_str})"
```

### 4b: `sep.join(list)` (1 error)

**Problem:** Python `sep.join(list)` vs C# `string.Join(sep, list)`.

**File:** `src/backend/csharp.py` in `_method_call()`

The fix at line 1106 exists but isn't matching. Ensure it's:
```python
if method == "join":
    # Python: sep.join(list) → C#: string.Join(sep, list)
    return f"string.Join({obj_str}, {args_str})"
```

---

## Fix 5: Constructor Forwarding (1 error)

**Problem:** `NewMatchedPairError(msg, pos, line)` returns `new MatchedPairError()` without args.

**Root cause:** Factory function pattern not lowering correctly.

**File:** `src/backend/csharp.py` in `_struct_lit()`

Check if this is a struct with an exception base and fields - the constructor should forward args:
```python
def _struct_lit(self, struct_name, fields, embedded_value):
    # Existing logic gets field_info and builds ordered_args
    # Verify ordered_args includes all constructor parameters
```

**Alternative:** May be a frontend lowering issue where the StructLit IR doesn't include the field values.

---

## Implementation Order

1. **Hoisting enhancement** (`hoisting.py`) - Fix element type tracking + shadow detection
2. **Backend: decl_typ usage** (`csharp.py`) - Use unified type for assignments
3. **Backend: endswith tuple** (`csharp.py`) - Expand tuple to OR conditions
4. **Backend: join pattern** (`csharp.py`) - Verify join fix is applied
5. **Backend: constructor** (`csharp.py`) - Trace why args aren't forwarded

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/middleend/hoisting.py` | Track element types, detect shadowing |
| `src/backend/csharp.py` | Use decl_typ, fix endswith/join, handle shadowing |

---

## Verification

```bash
just prep cs
```

**Expected:** 0 errors (down from 20)

**Fallback:** If some errors remain, they may need frontend changes to the type override system or IR generation.
