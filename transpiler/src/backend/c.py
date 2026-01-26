"""C backend."""

from __future__ import annotations


class CBackend:
    def emit(self, module) -> str:
        raise NotImplementedError
