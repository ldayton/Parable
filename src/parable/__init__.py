"""Parable - A recursive descent bash parser."""

from .core.ast import Node
from .core.parser import parse

__all__ = ["parse", "Node"]
__version__ = "0.1.0"
