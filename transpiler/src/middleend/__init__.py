"""IR analysis passes (read-only, no transformations)."""

from src.ir import Module

from .callbacks import analyze_callbacks
from .hoisting import analyze_hoisting
from .liveness import analyze_liveness
from .ownership import analyze_ownership
from .returns import analyze_returns
from .scope import analyze_scope


def analyze(module: Module) -> None:
    """Run all analysis passes, annotating IR nodes in place."""
    analyze_scope(module)
    analyze_liveness(module)
    analyze_returns(module)
    analyze_hoisting(module)
    analyze_callbacks(module)
    analyze_ownership(module)
