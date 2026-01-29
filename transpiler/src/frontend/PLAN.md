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

### 0. Extract `context.py` ✅

Create context dataclasses that bundle related state.

- ✅ Move `TypeContext` from frontend.py
- ✅ Create `FrontendContext` to bundle what lowering needs
- Define helper to build context from Frontend instance (deferred to chunk 5)

**Completed:** `1e85cae frontend: extract context.py with TypeContext and FrontendContext`

### 1. Extract `type_inference.py` ✅

Pure functions for type inference and coercion.

Functions (take explicit params, return values):
- ✅ `infer_type_from_value(node, symbols, param_types) -> Type`
- ✅ `infer_expr_type_from_ast(node, symbols, type_ctx) -> Type`
- ✅ `infer_iterable_type(node, var_types) -> Type`
- ✅ `infer_call_return_type(node, symbols, type_ctx) -> Type`
- ✅ `infer_container_type_from_ast(node, symbols, ...) -> Type`
- ✅ `synthesize_type(expr) -> Type`
- ✅ `synthesize_field_type(obj_type, field, symbols) -> Type`
- ✅ `synthesize_method_return_type(obj_type, method, symbols) -> Type`
- ✅ `synthesize_index_type(obj_type) -> Type`
- ✅ `coerce(expr, from_type, to_type) -> ir.Expr`
- ✅ `py_type_to_ir(py_type, symbols, concrete_nodes) -> Type`
- ✅ `py_return_type_to_ir(py_type, symbols, node_types) -> Type`
- ✅ Type parsing helpers: `split_union_types`, `split_type_args`, `parse_callable_type`
- ✅ Node type helpers: `extract_struct_name`, `is_node_interface_type`, `is_node_subtype`, `is_node_subclass`

**Completed:** commits `13a4782` through `c8948ed`

Depends on: symbols, type_ctx, IR types

### 2. Extract `lowering.py` ✅

Functions for lowering Python AST to IR.

**Extracted:**
- ✅ Operator/location helpers: `loc_from_node`, `binop_to_str`, `cmpop_to_str`, `unaryop_to_str`
- ✅ Type narrowing helpers: `is_isinstance_call`, `is_kind_check`, `extract_isinstance_or_chain`, `extract_isinstance_from_and`, `extract_kind_check`, `extract_attr_kind_check`, `get_attr_path`, `resolve_type_name`
- ✅ Argument helpers: `convert_negative_index`, `merge_keyword_args`, `fill_default_args`, `add_address_of_for_ptr_params`, `deref_for_slice_params`, `coerce_args_to_node`, `coerce_sentinel_to_ptr`, `is_sentinel_int`, `get_sentinel_value`, `is_pointer_to_slice`, `is_len_call`, `get_inner_slice`
- ✅ Simple expression lowering: `lower_expr_Constant`, `lower_expr_Name`
- ✅ Attribute/Subscript lowering: `lower_expr_Attribute`, `lower_expr_Subscript`
- ✅ Operator expression lowering: `lower_expr_BinOp`, `lower_expr_Compare`, `lower_expr_BoolOp`, `lower_expr_UnaryOp`
- ✅ Collection expression lowering: `lower_expr_List`, `lower_expr_Dict`, `lower_expr_JoinedStr`, `lower_expr_Tuple`, `lower_expr_Set`, `lower_list_call_with_expected_type`
- ✅ Expression dispatcher: `lower_expr_as_bool`, `lower_expr_IfExp`
- ✅ Simple statement lowering: `lower_stmt_Expr`, `lower_stmt_AugAssign`, `lower_stmt_While`, `lower_stmt_Break`, `lower_stmt_Continue`, `lower_stmt_Pass`, `lower_stmt_FunctionDef`, `is_super_init_call`
- ✅ Control flow: `lower_stmt_Return`
- ✅ Exception handling: `lower_stmt_Raise`
- ✅ LValue: `lower_lvalue`

**Skipped (too complex, kept in frontend.py):**
- `lower_expr_Call` (~300 lines, many special cases)
- `lower_stmt_Assign` (~230 lines, tuple unpacking, type tracking)
- `lower_stmt_AnnAssign` (~60 lines, annotation handling)
- `lower_stmt_If` (~55 lines, isinstance chain → TypeSwitch)
- `lower_stmt_For` (~80 lines, tuple unpacking in iteration)
- `lower_stmt_Try` (~20 lines, mutates catch var context)
- `collect_isinstance_chain` (mutates type context)

**Completed:** commits `3cc3c81` through `6fd5d78`

Depends on: context.py, type_inference.py

### 3. Extract `collection.py` ✅

Functions for multi-pass symbol/type collection (signature gathering, field discovery, var type inference).

**Completed:** commits `a396e5c` through `e494a8b`

**Detailed extraction plan (13 iterations):**

#### Iteration 3.1: Create `collection.py` skeleton + `is_exception_subclass`
Create module with imports. Extract first standalone function:
- `is_exception_subclass(name, symbols) -> bool` (recursive, no other deps)

#### Iteration 3.2: Extract `detect_mutated_params`
Pure AST analysis, no dependencies:
- `detect_mutated_params(node) -> set[str]`

#### Iteration 3.3: Extract `collect_class_names`
Simple pass 1 collector:
- `collect_class_names(tree, symbols, get_base_name) -> None`
- Needs callback: `get_base_name(base) -> str`

#### Iteration 3.4: Extract `mark_node_subclasses`
Pass 2 marker using type_inference:
- `mark_node_subclasses(symbols) -> set[str]`
- Uses `type_inference.is_node_subclass`

#### Iteration 3.5: Extract `mark_exception_subclasses`
Pass 2b marker:
- `mark_exception_subclasses(symbols) -> None`
- Uses `is_exception_subclass` (local)

#### Iteration 3.6: Extract `build_kind_mapping`
Pass: build kind -> struct mappings:
- `build_kind_mapping(symbols) -> tuple[dict[str, str], dict[str, str]]`

#### Iteration 3.7: Extract `collect_constants`
Pass 5 constant collector:
- `collect_constants(tree, symbols) -> None`

#### Iteration 3.8: Extract `extract_func_info`
Signature extraction (complex - needs callbacks):
- `extract_func_info(node, symbols, is_method, annotation_to_str, py_type_to_ir, py_return_type_to_ir, lower_expr, detect_mutated_params) -> FuncInfo`
- Consider: define a `CollectionCallbacks` dataclass similar to `LoweringDispatch`

#### Iteration 3.9: Extract `collect_signatures` + `collect_class_methods`
Pass 3 signature collectors:
- `collect_signatures(tree, symbols, extract_func_info) -> None`
- `collect_class_methods(node, symbols, extract_func_info) -> None`

#### Iteration 3.10: Extract `collect_init_fields`
Init field collection:
- `collect_init_fields(init, info, annotation_to_str, py_type_to_ir, infer_type_from_value) -> None`

#### Iteration 3.11: Extract `collect_class_fields` + `collect_fields`
Pass 4 field collectors:
- `collect_class_fields(node, symbols, annotation_to_str, py_type_to_ir, collect_init_fields) -> None`
- `collect_fields(tree, symbols, ...) -> None`

#### Iteration 3.12: Extract branch type helpers
Small helpers for `_collect_var_types`:
- `unify_branch_types(then_vars, else_vars) -> dict[str, Type]`
- `infer_branch_expr_type(node, var_types, branch_vars) -> Type`
- `collect_branch_var_types(stmts, var_types, infer_branch_expr_type) -> dict[str, Type]`
- `infer_element_type_from_append_arg(arg, var_types, symbols, current_class_name, current_func_info) -> Type`

#### Iteration 3.13: Extract `collect_var_types`
The big one (~365 lines) - main var type inference:
- `collect_var_types(stmts, symbols, type_ctx, current_class_name, current_func_info, ...) -> tuple[dict, dict, set, dict]`
- Consider: may need a `VarTypeContext` dataclass to bundle parameters

**Callback strategy:**
Define in collection.py:
```python
@dataclass
class CollectionCallbacks:
    """Callbacks for collection phase that need lowering."""
    annotation_to_str: Callable[[ast.expr | None], str]
    py_type_to_ir: Callable[[str, bool], Type]
    py_return_type_to_ir: Callable[[str], Type]
    infer_type_from_value: Callable[[ast.expr, dict], Type]
    lower_expr: Callable[[ast.expr], ir.Expr]  # for default values
```

Depends on: symbols, type_inference.py (for field type inference)

### 4. Extract `builders.py` ← NEXT

Functions for constructing IR nodes (Module, Struct, Function).

**Detailed extraction plan (7 iterations):**

#### Iteration 4.1: Create `builders.py` skeleton + `BuilderCallbacks`
Create module with imports. Define callback dataclass:
- `BuilderCallbacks` - bundles callbacks for annotation_to_str, py_type_to_ir, lower_expr, lower_stmts, collect_var_types, etc.

#### Iteration 4.2: Extract `build_forwarding_constructor`
Simplest builder - creates forwarding constructor for exception subclasses with no __init__:
- `build_forwarding_constructor(class_name, parent_class, symbols, callbacks) -> Function`

#### Iteration 4.3: Extract `build_constructor`
Constructor builder from __init__ AST:
- `build_constructor(class_name, init_ast, info, symbols, node_types, callbacks) -> Function`

#### Iteration 4.4: Extract `build_method_shell`
Method builder - sets up type context and lowers body:
- `build_method_shell(node, class_name, symbols, node_types, callbacks, with_body) -> Function`

#### Iteration 4.5: Extract `build_function_shell`
Function builder - similar to method_shell but without receiver:
- `build_function_shell(node, symbols, node_types, callbacks, with_body) -> Function`

#### Iteration 4.6: Extract `build_struct`
Struct builder - orchestrates method/constructor building:
- `build_struct(node, symbols, node_types, kind_to_struct, callbacks, with_body) -> tuple[Struct | None, Function | None]`

#### Iteration 4.7: Extract `build_module`
Module builder - orchestrates building all constants, structs, functions:
- `build_module(tree, symbols, node_types, kind_to_struct, kind_to_class, callbacks) -> Module`

**Callback strategy:**
Define in builders.py:
```python
@dataclass
class BuilderCallbacks:
    """Callbacks for builder phase that need lowering/type conversion."""
    annotation_to_str: Callable[[ast.expr | None], str]
    py_type_to_ir: Callable[[str, bool], Type]
    py_return_type_to_ir: Callable[[str], Type]
    lower_expr: Callable[[ast.expr], ir.Expr]
    lower_stmts: Callable[[list[ast.stmt]], list[ir.Stmt]]
    collect_var_types: Callable[[list[ast.stmt]], tuple[dict, dict, set, dict]]
    is_exception_subclass: Callable[[str], bool]
    extract_union_struct_names: Callable[[str], list[str]]
```

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
