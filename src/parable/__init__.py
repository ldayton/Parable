"""Parable - A recursive descent bash parser."""

from .ast import Node
from .parser import parse

__all__ = ["parse", "Node"]
__version__ = "0.1.0"
