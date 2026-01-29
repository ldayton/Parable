# Frontend Refactor Plan

Split `frontend.py` (3740 lines, 113 methods) into focused modules with explicit context passing.

## Design Principles

1. **Explicit over implicit** — Functions take context as parameters, not via `self`
2. **Clear dependencies** — Each module declares what it needs in function signatures
3. **Thin orchestrator** — `Frontend` class holds state, calls into pure-ish functions
4. **LLM-friendly** — A function's behavior is determinable from its signature and body alone

## Context Objects

Define these in `context.py`:

```python
@dataclass
class FrontendContext:
    """Immutable-ish context passed through lowering."""
    symbols: SymbolTable
    type_ctx: TypeContext
    current_func_info: FuncInfo | None
    current_class_name: str
    node_types: set[str]
    kind_to_struct: dict[str, str]
    kind_to_class: dict[str, str]
    current_catch_var: str | None
```

Functions receive what they need:
- `lower_expr(node, ctx: FrontendContext) -> ir.Expr`
- `infer_type(node, symbols, type_ctx) -> Type`
- `collect_var_types(stmts, symbols) -> dict[str, Type]`

## Chunks

### 0. Extract `context.py`

Create context dataclasses that bundle related state.

- Move `TypeContext` from frontend.py
- Create `FrontendContext` to bundle what lowering needs
- Define helper to build context from Frontend instance

~50 lines, foundation for everything else.

### 1. Extract `type_inference.py`

Pure functions for type inference and coercion.

Functions (take explicit params, return values):
- `infer_type_from_value(node, symbols, param_types) -> Type`
- `infer_expr_type_from_ast(node, symbols, type_ctx) -> Type`
- `infer_iterable_type(node, var_types) -> Type`
- `infer_call_return_type(node, symbols, type_ctx) -> Type`
- `synthesize_type(expr) -> Type`
- `synthesize_field_type(obj_type, field, symbols) -> Type`
- `synthesize_method_return_type(obj_type, method, symbols) -> Type`
- `coerce(expr, from_type, to_type) -> ir.Expr`
- `py_type_to_ir(py_type, symbols, concrete_nodes) -> Type`
- Type parsing helpers: `split_union_types`, `split_type_args`, `parse_callable_type`

Depends on: symbols, type_ctx, IR types

### 2. Extract `lowering.py`

Functions for lowering Python AST to IR.

Functions:
- `lower_expr(node, ctx: FrontendContext) -> ir.Expr`
- `lower_stmt(node, ctx: FrontendContext) -> ir.Stmt`
- `lower_stmts(stmts, ctx) -> list[ir.Stmt]`
- `lower_lvalue(node, ctx) -> ir.LValue`
- `lower_expr_as_bool(node, ctx) -> ir.Expr`
- Dispatch helpers for each node type (can be internal)

Depends on: context.py, type_inference.py

### 3. Extract `collection.py`

Functions for multi-pass symbol/type collection.

Functions:
- `collect_class_names(tree, symbols) -> None` (mutates symbols)
- `collect_signatures(tree, symbols) -> None`
- `collect_fields(tree, symbols) -> None`
- `collect_constants(tree, symbols) -> None`
- `collect_var_types(stmts, symbols, type_ctx) -> tuple[dict, dict, set, dict]`
- `mark_node_subclasses(symbols) -> set[str]`
- `mark_exception_subclasses(symbols) -> None`
- `build_kind_mapping(symbols) -> tuple[dict, dict]`
- `extract_func_info(node, symbols, class_name) -> FuncInfo`
- `detect_mutated_params(node) -> set[str]`

Depends on: symbols, type_inference.py (for field type inference)

### 4. Extract `builders.py`

Functions for constructing IR nodes.

Functions:
- `build_module(tree, ctx) -> Module`
- `build_struct(node, ctx, with_body) -> tuple[Struct | None, Function | None]`
- `build_constructor(class_name, init_ast, info, ctx) -> Function`
- `build_forwarding_constructor(class_name, parent_class, ctx) -> Function`
- `build_function_shell(node, ctx, with_body) -> Function`
- `build_method_shell(node, class_name, ctx, with_body) -> Function`
- `make_default_value(typ, loc) -> ir.Expr`

Depends on: context.py, type_inference.py, lowering.py, collection.py

### 5. Slim `frontend.py`

What remains:

- `Frontend` class with `__init__` and `transpile`
- Holds `SymbolTable` and mutable state
- Builds `FrontendContext` and passes to functions
- Orchestrates: collect → build → return Module

~200 lines of orchestration.

## Execution Order

0. **context.py** — Define context objects first
1. **type_inference.py** — No internal dependencies, foundational
2. **lowering.py** — Depends on type_inference
3. **collection.py** — Depends on type_inference
4. **builders.py** — Depends on all above
5. **Slim frontend.py** — Final orchestration cleanup

## Migration Strategy

For each chunk:
1. Create new module with function stubs
2. Move logic from Frontend methods → standalone functions
3. Add context parameters to signatures
4. Update Frontend methods to call new functions (temporary bridge)
5. Test: `just backend-test python`
6. Once chunk complete, remove bridge methods from Frontend

## Notes

- Preserve behavior exactly; refactor only, no fixes
- Run tests after each function migration, not just each chunk
- Some mutual recursion (lower ↔ infer) may require passing functions as params or late imports
