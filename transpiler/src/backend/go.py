"""Go backend."""

from __future__ import annotations


class GoBackend:
    def emit(self, module) -> str:
        raise NotImplementedError
