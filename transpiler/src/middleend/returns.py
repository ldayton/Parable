"""Return pattern analysis: contains_return, always_returns, needs_named_returns."""

from src.ir import (
    Block,
    ForClassic,
    ForRange,
    If,
    Match,
    Module,
    Return,
    Stmt,
    TryCatch,
    TypeSwitch,
    While,
)


def analyze_returns(module: Module) -> None:
    """Set needs_named_returns on functions that have TryCatch with catch-body returns."""
    for func in module.functions:
        func.needs_named_returns = _function_needs_named_returns(func.body)
    for struct in module.structs:
        for method in struct.methods:
            method.needs_named_returns = _function_needs_named_returns(method.body)


def contains_return(stmts: list[Stmt]) -> bool:
    """Check if statement list contains any Return statements (recursively)."""
    for stmt in stmts:
        if isinstance(stmt, Return):
            return True
        if isinstance(stmt, If):
            if contains_return(stmt.then_body) or contains_return(stmt.else_body):
                return True
        elif isinstance(stmt, While):
            if contains_return(stmt.body):
                return True
        elif isinstance(stmt, ForRange):
            if contains_return(stmt.body):
                return True
        elif isinstance(stmt, ForClassic):
            if contains_return(stmt.body):
                return True
        elif isinstance(stmt, Block):
            if contains_return(stmt.body):
                return True
        elif isinstance(stmt, TryCatch):
            if contains_return(stmt.body) or contains_return(stmt.catch_body):
                return True
        elif isinstance(stmt, Match):
            for case in stmt.cases:
                if contains_return(case.body):
                    return True
            if contains_return(stmt.default):
                return True
        elif isinstance(stmt, TypeSwitch):
            for case in stmt.cases:
                if contains_return(case.body):
                    return True
            if contains_return(stmt.default):
                return True
    return False


def always_returns(stmts: list[Stmt]) -> bool:
    """Check if a list of statements always returns (on all paths)."""
    for stmt in stmts:
        if isinstance(stmt, Return):
            return True
        if isinstance(stmt, If):
            if always_returns(stmt.then_body) and always_returns(stmt.else_body):
                return True
        if isinstance(stmt, (Match, TypeSwitch)):
            all_return = all(always_returns(case.body) for case in stmt.cases)
            if all_return and always_returns(stmt.default):
                return True
        if isinstance(stmt, TryCatch):
            if always_returns(stmt.body) and always_returns(stmt.catch_body):
                return True
        if isinstance(stmt, Block):
            if always_returns(stmt.body):
                return True
    return False


def _function_needs_named_returns(stmts: list[Stmt]) -> bool:
    """Check if any TryCatch in the statements has returns in its catch body."""
    for stmt in stmts:
        if isinstance(stmt, TryCatch):
            if contains_return(stmt.catch_body):
                return True
            if _function_needs_named_returns(stmt.body) or _function_needs_named_returns(
                stmt.catch_body
            ):
                return True
        elif isinstance(stmt, If):
            if _function_needs_named_returns(stmt.then_body) or _function_needs_named_returns(
                stmt.else_body
            ):
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
