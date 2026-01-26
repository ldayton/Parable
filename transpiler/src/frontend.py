"""Frontend: Python AST → IR."""

from __future__ import annotations


class Frontend:
    """Two-pass local inference: collect symbols, then emit IR."""

    def transpile(self, source: str):
        raise NotImplementedError
