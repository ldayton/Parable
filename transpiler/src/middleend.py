"""IR analysis passes (read-only, no transformations).

Annotations added:
    VarDecl.is_reassigned: bool  - variable is assigned after its declaration
    VarDecl.assignment_count: int - number of assignments after declaration
    VarDecl.initial_value_unused: bool - initial value overwritten before any read
    Param.is_modified: bool      - parameter is assigned/mutated in function body
    Param.is_unused: bool        - parameter is never referenced in function body
    Assign.is_declaration: bool  - first assignment to a new variable
    TupleAssign.is_declaration: bool - first assignment to new variables
    TryCatch.hoisted_vars: list[tuple[str, Type | None]] - variables needing hoisting
    TryCatch.catch_var_unused: bool - catch variable is never referenced
    If.hoisted_vars: list[tuple[str, Type | None]] - variables needing hoisting from branches
"""

from src.ir import (
    Assign,
    Block,
    DerefLV,
    ExprStmt,
    FieldLV,
    ForClassic,
    ForRange,
    Function,
    If,
    IndexLV,
    Interface,
    Match,
    MethodCall,
    Module,
    OpAssign,
    Param,
    Return,
    Stmt,
    TryCatch,
    Tuple,
    TupleAssign,
    Type,
    TypeSwitch,
    Var,
    VarDecl,
    VarLV,
    While,
)
from src.type_overrides import VAR_TYPE_OVERRIDES


def analyze(module: Module) -> None:
    """Run all analysis passes, annotating IR nodes in place."""
    _analyze_reassignments(module)
    _analyze_initial_value_usage(module)  # Sets has_catch_returns on TryCatch
    _analyze_named_returns(module)  # Check if functions need named returns (must be after initial_value_usage)
    _analyze_hoisting_all(module)
    _analyze_unused_tuple_targets_all(module)


def _analyze_named_returns(module: Module) -> None:
    """Set needs_named_returns on functions that have TryCatch with catch-body returns."""
    for func in module.functions:
        func.needs_named_returns = _function_needs_named_returns(func.body)
    for struct in module.structs:
        for method in struct.methods:
            method.needs_named_returns = _function_needs_named_returns(method.body)


def _always_returns(stmts: list[Stmt]) -> bool:
    """Check if a list of statements always returns (on all paths)."""
    for stmt in stmts:
        if isinstance(stmt, Return):
            return True
        if isinstance(stmt, If):
            # Both branches must return
            if _always_returns(stmt.then_body) and _always_returns(stmt.else_body):
                return True
        if isinstance(stmt, (Match, TypeSwitch)):
            # All cases and default must return
            all_return = all(_always_returns(case.body) for case in stmt.cases)
            if all_return and _always_returns(stmt.default):
                return True
        if isinstance(stmt, TryCatch):
            # Both try and catch must return
            if _always_returns(stmt.body) and _always_returns(stmt.catch_body):
                return True
        if isinstance(stmt, Block):
            if _always_returns(stmt.body):
                return True
    return False


def _collect_assigned_vars(stmts: list[Stmt]) -> set[str]:
    """Collect variable names that are assigned in a list of statements."""
    result: set[str] = set()
    for stmt in stmts:
        if isinstance(stmt, Assign):
            if isinstance(stmt.target, VarLV):
                result.add(stmt.target.name)
        elif isinstance(stmt, TupleAssign):
            for target in stmt.targets:
                if isinstance(target, VarLV):
                    result.add(target.name)
        elif isinstance(stmt, If):
            result.update(_collect_assigned_vars(stmt.then_body))
            result.update(_collect_assigned_vars(stmt.else_body))
        elif isinstance(stmt, While):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, ForRange):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, ForClassic):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, Block):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, TryCatch):
            result.update(_collect_assigned_vars(stmt.body))
            result.update(_collect_assigned_vars(stmt.catch_body))
    return result


def _collect_used_vars(stmts: list[Stmt]) -> set[str]:
    """Collect all variable names referenced in statements and expressions."""
    result: set[str] = set()

    def visit_expr(expr) -> None:
        if expr is None:
            return
        if isinstance(expr, Var):
            result.add(expr.name)
        # Recursively visit all expression attributes
        for attr in ('obj', 'left', 'right', 'operand', 'cond', 'then_expr', 'else_expr',
                     'expr', 'index', 'low', 'high', 'ptr', 'value', 'message', 'pos',
                     'iterable', 'target', 'inner', 'on_type', 'length', 'capacity'):
            if hasattr(expr, attr):
                visit_expr(getattr(expr, attr))
        if hasattr(expr, 'args'):
            for arg in expr.args:
                visit_expr(arg)
        if hasattr(expr, 'elements'):
            for elem in expr.elements:
                visit_expr(elem)
        if hasattr(expr, 'parts'):
            for part in expr.parts:
                visit_expr(part)
        if hasattr(expr, 'entries'):
            entries = expr.entries
            if isinstance(entries, dict):
                for v in entries.values():
                    visit_expr(v)
            else:
                for item in entries:
                    if isinstance(item, tuple) and len(item) == 2:
                        visit_expr(item[1])
        if hasattr(expr, 'fields') and isinstance(expr.fields, dict):
            for v in expr.fields.values():
                visit_expr(v)

    def visit_stmt(stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            if stmt.value:
                visit_expr(stmt.value)
        elif isinstance(stmt, (Assign, OpAssign)):
            visit_expr(stmt.value)
            # Also check lvalue targets for variable usage
            target = stmt.target
            if hasattr(target, 'obj'):
                visit_expr(target.obj)
            if hasattr(target, 'index'):
                visit_expr(target.index)
            if hasattr(target, 'ptr'):
                visit_expr(target.ptr)
        elif isinstance(stmt, TupleAssign):
            visit_expr(stmt.value)
        elif isinstance(stmt, ExprStmt):
            visit_expr(stmt.expr)
        elif isinstance(stmt, Return):
            if stmt.value:
                visit_expr(stmt.value)
        elif isinstance(stmt, If):
            visit_expr(stmt.cond)
            if stmt.init:
                visit_stmt(stmt.init)
            for s in stmt.then_body:
                visit_stmt(s)
            for s in stmt.else_body:
                visit_stmt(s)
        elif isinstance(stmt, While):
            visit_expr(stmt.cond)
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, ForRange):
            visit_expr(stmt.iterable)
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                visit_stmt(stmt.init)
            if stmt.cond:
                visit_expr(stmt.cond)
            if stmt.post:
                visit_stmt(stmt.post)
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, Block):
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, TryCatch):
            for s in stmt.body:
                visit_stmt(s)
            for s in stmt.catch_body:
                visit_stmt(s)
        elif isinstance(stmt, Match):
            visit_expr(stmt.expr)
            for case in stmt.cases:
                for s in case.body:
                    visit_stmt(s)
            for s in stmt.default:
                visit_stmt(s)
        elif isinstance(stmt, TypeSwitch):
            visit_expr(stmt.expr)
            for case in stmt.cases:
                for s in case.body:
                    visit_stmt(s)
            for s in stmt.default:
                visit_stmt(s)

    for stmt in stmts:
        visit_stmt(stmt)
    return result


def _analyze_reassignments(module: Module) -> None:
    """Find variables and parameters that are reassigned/modified."""
    for func in module.functions:
        _analyze_function(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_function(method)


def _analyze_function(func: Function) -> None:
    """Analyze a single function for reassignments."""
    declared: dict[str, VarDecl] = {}
    assigned: set[str] = set()  # Variables already assigned (for is_declaration)
    params: dict[str, Param] = {p.name: p for p in func.params}

    # Initialize annotations
    for p in func.params:
        p.is_modified = False
        p.is_unused = False
        assigned.add(p.name)  # Parameters are already "assigned"

    # Collect all referenced variable names
    used_vars: set[str] = _collect_used_vars(func.body)

    def mark_reassigned(name: str) -> None:
        if name in declared:
            declared[name].is_reassigned = True
            declared[name].assignment_count += 1
        elif name in params:
            params[name].is_modified = True

    def is_new_declaration(lv, local_assigned: set[str]) -> bool:
        """Check if this lvalue represents a first assignment to a variable."""
        if isinstance(lv, VarLV):
            # Check against parameters and local_assigned (which includes VarDecls in current branch)
            return lv.name not in params and lv.name not in local_assigned
        return False

    def check_lvalue(lv) -> None:
        """Mark the base variable of an lvalue as modified."""
        if isinstance(lv, VarLV):
            mark_reassigned(lv.name)
        elif isinstance(lv, IndexLV):
            if isinstance(lv.obj, Var):
                mark_reassigned(lv.obj.name)
        elif isinstance(lv, FieldLV):
            if isinstance(lv.obj, Var):
                mark_reassigned(lv.obj.name)
        elif isinstance(lv, DerefLV):
            if isinstance(lv.ptr, Var):
                mark_reassigned(lv.ptr.name)

    def check_stmt(stmt: Stmt, local_assigned: set[str] | None = None) -> None:
        if local_assigned is None:
            local_assigned = set()
        if isinstance(stmt, VarDecl):
            stmt.is_reassigned = False
            stmt.assignment_count = 0
            declared[stmt.name] = stmt
            local_assigned.add(stmt.name)  # Add to branch-local, not global
            if stmt.value:
                check_expr(stmt.value)
        elif isinstance(stmt, Assign):
            # Determine if this is a declaration (first assignment to new variable)
            stmt.is_declaration = is_new_declaration(stmt.target, local_assigned)
            if isinstance(stmt.target, VarLV) and stmt.is_declaration:
                local_assigned.add(stmt.target.name)
                # Note: Don't add to outer 'assigned' - if-else branches need separate scopes
            check_lvalue(stmt.target)
            check_expr(stmt.value)
        elif isinstance(stmt, OpAssign):
            check_lvalue(stmt.target)
            check_expr(stmt.value)
        elif isinstance(stmt, TupleAssign):
            # Check if all targets are new declarations
            all_new = True
            new_targets: list[str] = []
            for target in stmt.targets:
                if isinstance(target, VarLV):
                    if (target.name in assigned or target.name in declared or
                        target.name in params or target.name in local_assigned):
                        all_new = False
                    else:
                        new_targets.append(target.name)
                        local_assigned.add(target.name)
                else:
                    all_new = False
            stmt.is_declaration = all_new
            stmt.new_targets = new_targets  # Track which specific targets are new
            for target in stmt.targets:
                if isinstance(target, VarLV) and not stmt.is_declaration:
                    mark_reassigned(target.name)
            check_expr(stmt.value)
        elif isinstance(stmt, ExprStmt):
            check_expr(stmt.expr)
        elif isinstance(stmt, Return):
            if stmt.value:
                check_expr(stmt.value)
        elif isinstance(stmt, If):
            check_expr(stmt.cond)
            if stmt.init:
                check_stmt(stmt.init, local_assigned)
            # Each branch inherits parent's assignments so they can see outer declarations
            # But siblings don't see each other's declarations
            then_assigned: set[str] = set(local_assigned)
            for s in stmt.then_body:
                check_stmt(s, then_assigned)
            else_assigned: set[str] = set(local_assigned)
            for s in stmt.else_body:
                check_stmt(s, else_assigned)
        elif isinstance(stmt, While):
            check_expr(stmt.cond)
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, ForRange):
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                check_stmt(stmt.init, local_assigned)
            if stmt.cond:
                check_expr(stmt.cond)
            if stmt.post:
                check_stmt(stmt.post, local_assigned)
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, Block):
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, TryCatch):
            # TryCatch body is wrapped in a closure in Go
            # Closures CAN access outer variables, so inherit parent's assignments
            # But new declarations inside the closure can't escape
            try_assigned: set[str] = set(local_assigned)
            for s in stmt.body:
                check_stmt(s, try_assigned)
            catch_assigned: set[str] = set(local_assigned)
            for s in stmt.catch_body:
                check_stmt(s, catch_assigned)
        elif isinstance(stmt, Match):
            check_expr(stmt.expr)
            for case in stmt.cases:
                # Inherit from outer scope so outer declarations are visible
                case_assigned: set[str] = set(local_assigned)
                for s in case.body:
                    check_stmt(s, case_assigned)
            # Default case also inherits from outer scope
            default_assigned: set[str] = set(local_assigned)
            for s in stmt.default:
                check_stmt(s, default_assigned)
        elif isinstance(stmt, TypeSwitch):
            check_expr(stmt.expr)
            for case in stmt.cases:
                # Inherit from outer scope so outer declarations are visible
                case_assigned: set[str] = set(local_assigned)
                for s in case.body:
                    check_stmt(s, case_assigned)
            # Default case also inherits from outer scope
            default_assigned: set[str] = set(local_assigned)
            for s in stmt.default:
                check_stmt(s, default_assigned)

    def check_expr(expr) -> None:
        """Check for mutating method calls on declared variables."""
        if isinstance(expr, MethodCall):
            if isinstance(expr.obj, Var):
                mark_reassigned(expr.obj.name)
            check_expr(expr.obj)
            for arg in expr.args:
                check_expr(arg)

    func_assigned: set[str] = set()
    for stmt in func.body:
        check_stmt(stmt, func_assigned)

    # Mark unused parameters
    for p in func.params:
        if p.name not in used_vars:
            p.is_unused = True


# ============================================================
# INITIAL VALUE USAGE ANALYSIS
# ============================================================


def _analyze_initial_value_usage(module: Module) -> None:
    """Find VarDecls where initial value is overwritten before any read."""
    for func in module.functions:
        _analyze_initial_value_in_function(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_initial_value_in_function(method)


def _analyze_initial_value_in_function(func: Function) -> None:
    """Analyze a function for unused initial values."""
    _analyze_initial_value_in_stmts(func.body)


def _analyze_initial_value_in_stmts(stmts: list[Stmt]) -> None:
    """Analyze statements for VarDecls with unused initial values."""
    for i, stmt in enumerate(stmts):
        if isinstance(stmt, VarDecl) and stmt.value is not None:
            stmt.initial_value_unused = _is_written_before_read(stmt.name, stmts[i + 1:])
        # Recurse into nested structures
        if isinstance(stmt, If):
            _analyze_initial_value_in_stmts(stmt.then_body)
            _analyze_initial_value_in_stmts(stmt.else_body)
        elif isinstance(stmt, While):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, ForRange):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, ForClassic):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, Block):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, TryCatch):
            _analyze_initial_value_in_stmts(stmt.body)
            _analyze_initial_value_in_stmts(stmt.catch_body)
            # Check if catch variable is used
            if stmt.catch_var:
                used = _collect_used_vars(stmt.catch_body)
                stmt.catch_var_unused = stmt.catch_var not in used
            else:
                stmt.catch_var_unused = True
            # Check if try or catch body contains Return statements
            # This affects how the TryCatch should be emitted (IIFE vs defer pattern)
            stmt.has_returns = _contains_return(stmt.body) or _contains_return(stmt.catch_body)
            # Track if specifically the catch body has returns (needs named return pattern)
            stmt.has_catch_returns = _contains_return(stmt.catch_body)
        elif isinstance(stmt, Match):
            for case in stmt.cases:
                _analyze_initial_value_in_stmts(case.body)
            _analyze_initial_value_in_stmts(stmt.default)
        elif isinstance(stmt, TypeSwitch):
            # Check if the binding variable is used in any case body
            all_stmts: list[Stmt] = []
            for case in stmt.cases:
                all_stmts.extend(case.body)
            all_stmts.extend(stmt.default)
            used_vars = _collect_used_vars(all_stmts)
            stmt.binding_unused = stmt.binding not in used_vars
            # Check if the binding is reassigned in any case body
            # If so, Go's type switch shadowing will cause type errors
            assigned_vars = _collect_assigned_vars(all_stmts)
            stmt.binding_reassigned = stmt.binding in assigned_vars
            # Recurse into case bodies
            for case in stmt.cases:
                _analyze_initial_value_in_stmts(case.body)
            _analyze_initial_value_in_stmts(stmt.default)


def _is_written_before_read(name: str, stmts: list[Stmt]) -> bool:
    """Check if variable is assigned before any read in statement sequence.

    Returns True if the first access to `name` is a write (assignment).
    Returns False if the first access is a read, or if there's no access.
    """
    for stmt in stmts:
        result = _first_access_type(name, stmt)
        if result == "read":
            return False
        if result == "write":
            return True
    return False


def _first_access_type(name: str, stmt: Stmt) -> str | None:
    """Determine if first access to `name` in stmt is 'read', 'write', or None."""
    if isinstance(stmt, VarDecl):
        if stmt.value and _expr_reads(name, stmt.value):
            return "read"
        return None
    elif isinstance(stmt, Assign):
        # Check RHS first (read), then LHS (write)
        if _expr_reads(name, stmt.value):
            return "read"
        if isinstance(stmt.target, VarLV) and stmt.target.name == name:
            return "write"
        # Check for reads in complex lvalues
        if _lvalue_reads(name, stmt.target):
            return "read"
        return None
    elif isinstance(stmt, OpAssign):
        # OpAssign reads before writing (x += 1 reads x)
        if isinstance(stmt.target, VarLV) and stmt.target.name == name:
            return "read"
        if _expr_reads(name, stmt.value):
            return "read"
        if _lvalue_reads(name, stmt.target):
            return "read"
        return None
    elif isinstance(stmt, TupleAssign):
        if _expr_reads(name, stmt.value):
            return "read"
        for target in stmt.targets:
            if isinstance(target, VarLV) and target.name == name:
                return "write"
        return None
    elif isinstance(stmt, ExprStmt):
        if _expr_reads(name, stmt.expr):
            return "read"
        return None
    elif isinstance(stmt, Return):
        if stmt.value and _expr_reads(name, stmt.value):
            return "read"
        return None
    elif isinstance(stmt, Block):
        # Blocks execute sequentially
        for s in stmt.body:
            result = _first_access_type(name, s)
            if result:
                return result
        return None
    elif isinstance(stmt, If):
        # Condition is always evaluated
        if _expr_reads(name, stmt.cond):
            return "read"
        # Branches: conservative - if either branch reads first, consider it a read
        # Only return "write" if BOTH branches write first (guaranteed write)
        then_result = _first_access_in_stmts(name, stmt.then_body)
        else_result = _first_access_in_stmts(name, stmt.else_body)
        if then_result == "read" or else_result == "read":
            return "read"
        if then_result == "write" and else_result == "write":
            return "write"
        return None
    elif isinstance(stmt, While):
        if _expr_reads(name, stmt.cond):
            return "read"
        # Loop body might not execute, so can't guarantee write
        result = _first_access_in_stmts(name, stmt.body)
        if result == "read":
            return "read"
        return None
    elif isinstance(stmt, ForRange):
        if _expr_reads(name, stmt.iterable):
            return "read"
        result = _first_access_in_stmts(name, stmt.body)
        if result == "read":
            return "read"
        return None
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            result = _first_access_type(name, stmt.init)
            if result:
                return result
        if stmt.cond and _expr_reads(name, stmt.cond):
            return "read"
        return None
    elif isinstance(stmt, TryCatch):
        # Try body might partially execute
        result = _first_access_in_stmts(name, stmt.body)
        if result == "read":
            return "read"
        # Catch body might execute
        catch_result = _first_access_in_stmts(name, stmt.catch_body)
        if catch_result == "read":
            return "read"
        return None
    return None


def _first_access_in_stmts(name: str, stmts: list[Stmt]) -> str | None:
    """Find first access type in a list of statements."""
    for stmt in stmts:
        result = _first_access_type(name, stmt)
        if result:
            return result
    return None


def _expr_reads(name: str, expr) -> bool:
    """Check if expression reads the variable."""
    if expr is None:
        return False
    if isinstance(expr, Var):
        return expr.name == name
    # Check all expression children
    for attr in ('obj', 'left', 'right', 'operand', 'cond', 'then_expr', 'else_expr',
                 'expr', 'index', 'low', 'high', 'ptr', 'value', 'message', 'pos',
                 'iterable', 'target', 'inner', 'on_type', 'length', 'capacity'):
        if hasattr(expr, attr) and _expr_reads(name, getattr(expr, attr)):
            return True
    if hasattr(expr, 'args'):
        for arg in expr.args:
            if _expr_reads(name, arg):
                return True
    if hasattr(expr, 'elements'):
        for elem in expr.elements:
            if _expr_reads(name, elem):
                return True
    if hasattr(expr, 'parts'):
        for part in expr.parts:
            if _expr_reads(name, part):
                return True
    if hasattr(expr, 'entries'):
        entries = expr.entries
        if isinstance(entries, dict):
            for v in entries.values():
                if _expr_reads(name, v):
                    return True
        else:
            for item in entries:
                if isinstance(item, tuple) and len(item) == 2:
                    if _expr_reads(name, item[1]):
                        return True
    if hasattr(expr, 'fields') and isinstance(expr.fields, dict):
        for v in expr.fields.values():
            if _expr_reads(name, v):
                return True
    return False


def _lvalue_reads(name: str, lv) -> bool:
    """Check if lvalue reads the variable (e.g., arr[i] reads arr and i)."""
    if isinstance(lv, VarLV):
        return False  # Simple var assignment doesn't read
    elif isinstance(lv, IndexLV):
        return _expr_reads(name, lv.obj) or _expr_reads(name, lv.index)
    elif isinstance(lv, FieldLV):
        return _expr_reads(name, lv.obj)
    elif isinstance(lv, DerefLV):
        return _expr_reads(name, lv.ptr)
    return False


def _contains_return(stmts: list[Stmt]) -> bool:
    """Check if statement list contains any Return statements (recursively)."""
    for stmt in stmts:
        if isinstance(stmt, Return):
            return True
        # Recurse into nested structures
        if isinstance(stmt, If):
            if _contains_return(stmt.then_body) or _contains_return(stmt.else_body):
                return True
        elif isinstance(stmt, While):
            if _contains_return(stmt.body):
                return True
        elif isinstance(stmt, ForRange):
            if _contains_return(stmt.body):
                return True
        elif isinstance(stmt, ForClassic):
            if _contains_return(stmt.body):
                return True
        elif isinstance(stmt, Block):
            if _contains_return(stmt.body):
                return True
        elif isinstance(stmt, TryCatch):
            if _contains_return(stmt.body) or _contains_return(stmt.catch_body):
                return True
        elif isinstance(stmt, Match):
            for case in stmt.cases:
                if _contains_return(case.body):
                    return True
            if _contains_return(stmt.default):
                return True
        elif isinstance(stmt, TypeSwitch):
            for case in stmt.cases:
                if _contains_return(case.body):
                    return True
            if _contains_return(stmt.default):
                return True
    return False


def _function_needs_named_returns(stmts: list[Stmt]) -> bool:
    """Check if any TryCatch in the statements has returns in its catch body."""
    for stmt in stmts:
        if isinstance(stmt, TryCatch):
            if getattr(stmt, 'has_catch_returns', False):
                return True
            # Also check nested TryCatch
            if _function_needs_named_returns(stmt.body) or _function_needs_named_returns(stmt.catch_body):
                return True
        elif isinstance(stmt, If):
            if _function_needs_named_returns(stmt.then_body) or _function_needs_named_returns(stmt.else_body):
                return True
        elif isinstance(stmt, While):
            if _function_needs_named_returns(stmt.body):
                return True
        elif isinstance(stmt, ForRange):
            if _function_needs_named_returns(stmt.body):
                return True
        elif isinstance(stmt, ForClassic):
            if _function_needs_named_returns(stmt.body):
                return True
        elif isinstance(stmt, Block):
            if _function_needs_named_returns(stmt.body):
                return True
        elif isinstance(stmt, Match):
            for case in stmt.cases:
                if _function_needs_named_returns(case.body):
                    return True
            if _function_needs_named_returns(stmt.default):
                return True
        elif isinstance(stmt, TypeSwitch):
            for case in stmt.cases:
                if _function_needs_named_returns(case.body):
                    return True
            if _function_needs_named_returns(stmt.default):
                return True
    return False


# ============================================================
# VARIABLE HOISTING ANALYSIS
# ============================================================


def _merge_types(t1: Type | None, t2: Type | None) -> Type | None:
    """Merge two types, preferring concrete interface over Interface("any").

    When hoisting variables assigned in multiple branches:
    - If one branch assigns nil (Interface("any")) and another assigns Node, use Node
    - Go interfaces are nil-able, so Interface("Node") can hold nil without widening
    """
    if t1 is None:
        return t2
    if t2 is None:
        return t1
    if t1 == t2:
        return t1
    # Prefer named interface over "any" (nil gets typed as Interface("any"))
    if isinstance(t1, Interface) and t1.name == "any" and isinstance(t2, Interface):
        return t2
    if isinstance(t2, Interface) and t2.name == "any" and isinstance(t1, Interface):
        return t1
    # Prefer any concrete type over Interface("any")
    if isinstance(t1, Interface) and t1.name == "any":
        return t2
    if isinstance(t2, Interface) and t2.name == "any":
        return t1
    # Otherwise keep first type (arbitrary but deterministic)
    return t1


def _merge_var_types(result: dict[str, Type | None], new_vars: dict[str, Type | None]) -> None:
    """Merge new_vars into result, using type merging for conflicts."""
    for name, typ in new_vars.items():
        if name in result:
            result[name] = _merge_types(result[name], typ)
        else:
            result[name] = typ


def _vars_first_assigned_in(stmts: list[Stmt], already_declared: set[str]) -> dict[str, Type | None]:
    """Find variables first assigned in these statements (not already declared)."""
    result: dict[str, Type | None] = {}
    for stmt in stmts:
        if isinstance(stmt, Assign) and getattr(stmt, 'is_declaration', False):
            if isinstance(stmt.target, VarLV):
                name = stmt.target.name
                if name not in already_declared:
                    # Prefer decl_typ (unified type from frontend) over value.typ
                    new_type = getattr(stmt, 'decl_typ', None) or getattr(stmt.value, 'typ', None)
                    if name in result:
                        result[name] = _merge_types(result[name], new_type)
                    else:
                        result[name] = new_type
        elif isinstance(stmt, TupleAssign) and getattr(stmt, 'is_declaration', False):
            for i, target in enumerate(stmt.targets):
                if isinstance(target, VarLV):
                    name = target.name
                    if name not in already_declared and name not in result:
                        # Type from tuple element if available
                        val_typ = getattr(stmt.value, 'typ', None)
                        if isinstance(val_typ, Tuple) and i < len(val_typ.elements):
                            result[name] = val_typ.elements[i]
                        else:
                            result[name] = None
        # Recurse into nested structures
        elif isinstance(stmt, If):
            # For sibling branches, use the SAME already_declared set (before processing either branch)
            # This allows the same variable to be assigned in both branches with different types
            branch_declared = already_declared | set(result.keys())
            _merge_var_types(result, _vars_first_assigned_in(stmt.then_body, branch_declared))
            _merge_var_types(result, _vars_first_assigned_in(stmt.else_body, branch_declared))
        elif isinstance(stmt, While):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, ForRange):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, ForClassic):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, Block):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, TryCatch):
            # For try/catch, use the same pattern as if/else - both branches start fresh
            branch_declared = already_declared | set(result.keys())
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, branch_declared))
            _merge_var_types(result, _vars_first_assigned_in(stmt.catch_body, branch_declared))
    return result


def _analyze_hoisting(func: Function) -> None:
    """Annotate TryCatch and If nodes with variables needing hoisting."""
    func_name = func.name
    # Collect function-level declared variables
    func_declared = set(p.name for p in func.params)
    for stmt in func.body:
        if isinstance(stmt, VarDecl):
            func_declared.add(stmt.name)

    def apply_type_overrides(hoisted: list[tuple[str, Type | None]]) -> list[tuple[str, Type | None]]:
        """Apply VAR_TYPE_OVERRIDES to hoisted variables."""
        result = []
        for name, typ in hoisted:
            override_key = (func_name, name)
            if override_key in VAR_TYPE_OVERRIDES:
                result.append((name, VAR_TYPE_OVERRIDES[override_key]))
            else:
                result.append((name, typ))
        return result

    def analyze_stmts(stmts: list[Stmt], outer_declared: set[str]) -> None:
        """Analyze statements, annotating nodes that need hoisting."""
        declared = set(outer_declared)

        for i, stmt in enumerate(stmts):
            if isinstance(stmt, TryCatch):
                # Find vars first assigned inside try/catch bodies
                inner_new = _vars_first_assigned_in(
                    stmt.body + stmt.catch_body, declared
                )

                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])

                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)

                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)

                # Recurse into try/catch bodies
                analyze_stmts(stmt.body, declared)
                analyze_stmts(stmt.catch_body, declared)

            elif isinstance(stmt, If):
                # Find vars first assigned inside if branches
                inner_new = _vars_first_assigned_in(
                    stmt.then_body + stmt.else_body, declared
                )

                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])

                # Find vars assigned in then_body but used in else_body (cross-branch)
                then_new = _vars_first_assigned_in(stmt.then_body, declared)
                else_used = _collect_used_vars(stmt.else_body)

                # Vars needing hoisting = first assigned inside AND (used after OR cross-branch)
                needs_hoisting = []
                for name, typ in inner_new.items():
                    if name in used_after:
                        needs_hoisting.append((name, typ))
                    elif name in then_new and name in else_used:
                        needs_hoisting.append((name, typ))
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)

                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)

                # Recurse into if branches
                if stmt.init:
                    analyze_stmts([stmt.init], declared)
                analyze_stmts(stmt.then_body, declared)
                analyze_stmts(stmt.else_body, declared)

            elif isinstance(stmt, VarDecl):
                declared.add(stmt.name)
            elif isinstance(stmt, Assign) and getattr(stmt, 'is_declaration', False):
                if isinstance(stmt.target, VarLV):
                    declared.add(stmt.target.name)
            elif isinstance(stmt, TupleAssign) and getattr(stmt, 'is_declaration', False):
                for target in stmt.targets:
                    if isinstance(target, VarLV):
                        declared.add(target.name)
            elif isinstance(stmt, While):
                # Find vars first assigned inside while body
                inner_new = _vars_first_assigned_in(stmt.body, declared)
                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])
                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)
                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, ForRange):
                # Find vars first assigned inside for body
                inner_new = _vars_first_assigned_in(stmt.body, declared)
                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])
                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)
                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, ForClassic):
                if stmt.init:
                    analyze_stmts([stmt.init], declared)
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, Block):
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, (Match, TypeSwitch)):
                # Only collect from cases that DON'T return (vars that might escape)
                # Cases that return keep their variables local (no need to hoist)
                non_returning_stmts: list[Stmt] = []
                for case in stmt.cases:
                    if not _always_returns(case.body):
                        non_returning_stmts.extend(case.body)
                if not _always_returns(stmt.default):
                    non_returning_stmts.extend(stmt.default)
                # Find vars first assigned inside non-returning branches
                inner_new = _vars_first_assigned_in(non_returning_stmts, declared)
                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])
                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)
                # Update declared set
                declared.update(name for name, _ in needs_hoisting)
                # Recurse into case bodies
                for case in stmt.cases:
                    analyze_stmts(case.body, declared)
                analyze_stmts(stmt.default, declared)

    analyze_stmts(func.body, func_declared)


def _analyze_hoisting_all(module: Module) -> None:
    """Run hoisting analysis on all functions."""
    for func in module.functions:
        _analyze_hoisting(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_hoisting(method)


def _iter_all_stmts(stmts: list[Stmt]):
    """Iterate over all statements recursively."""
    for stmt in stmts:
        yield stmt
        if isinstance(stmt, If):
            yield from _iter_all_stmts(stmt.then_body)
            yield from _iter_all_stmts(stmt.else_body)
        elif isinstance(stmt, While):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, ForRange):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, ForClassic):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, Block):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, TryCatch):
            yield from _iter_all_stmts(stmt.body)
            yield from _iter_all_stmts(stmt.catch_body)
        elif isinstance(stmt, (Match, TypeSwitch)):
            for case in stmt.cases:
                yield from _iter_all_stmts(case.body)
            yield from _iter_all_stmts(stmt.default)


def _analyze_unused_tuple_targets(func: Function) -> None:
    """Mark indices of unused tuple targets for emitting _ in Go."""
    used_vars = _collect_used_vars(func.body)
    for stmt in _iter_all_stmts(func.body):
        if isinstance(stmt, TupleAssign):
            unused = []
            for i, t in enumerate(stmt.targets):
                if isinstance(t, VarLV) and t.name != "_" and t.name not in used_vars:
                    unused.append(i)
            if unused:
                stmt.unused_indices = unused


def _analyze_unused_tuple_targets_all(module: Module) -> None:
    """Run unused tuple target analysis on all functions."""
    for func in module.functions:
        _analyze_unused_tuple_targets(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_unused_tuple_targets(method)
