"""Rust backend."""

from __future__ import annotations


class RustBackend:
    def emit(self, module) -> str:
        raise NotImplementedError
