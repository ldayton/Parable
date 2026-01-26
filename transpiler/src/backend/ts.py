"""TypeScript backend."""

from __future__ import annotations


class TsBackend:
    def emit(self, module) -> str:
        raise NotImplementedError
