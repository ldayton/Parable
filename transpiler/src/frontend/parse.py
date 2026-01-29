"""Phase 2: Parse Python source to dict-based AST via CPython subprocess."""

import json
import subprocess
from dataclasses import dataclass


@dataclass
class ParseError(Exception):
    msg: str
    lineno: int
    col: int


_SCRIPT = '''
import ast, json, sys
def conv(n):
    if isinstance(n, ast.AST):
        d = {"_type": n.__class__.__name__}
        for f, v in ast.iter_fields(n):
            d[f] = conv(v)
        for a in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if hasattr(n, a): d[a] = getattr(n, a)
        return d
    if isinstance(n, list): return [conv(x) for x in n]
    return n
try:
    print(json.dumps(conv(ast.parse(sys.stdin.read()))))
except SyntaxError as e:
    print(json.dumps({"error": True, "msg": e.msg, "lineno": e.lineno, "col": (e.offset or 1) - 1}))
    sys.exit(1)
'''


def parse(source: str) -> dict:
    """Parse Python source to dict-based AST via CPython subprocess."""
    result = subprocess.run(
        ["python3", "-c", _SCRIPT],
        input=source,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    if result.returncode != 0 or data.get("error"):
        raise ParseError(data["msg"], data["lineno"], data["col"])
    return data
