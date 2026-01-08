"""AST node types for Parable."""

from dataclasses import dataclass, field


@dataclass
class Node:
    """Base class for all AST nodes."""

    kind: str

    def to_sexp(self) -> str:
        """Convert node to S-expression string for testing."""
        raise NotImplementedError


@dataclass
class Word(Node):
    """A word token, possibly containing expansions."""

    value: str
    parts: list[Node] = field(default_factory=list)

    def __init__(self, value: str, parts: list[Node] = None):
        self.kind = "word"
        self.value = value
        self.parts = parts or []

    def to_sexp(self) -> str:
        escaped = self.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        if self.parts:
            inner = " ".join(p.to_sexp() for p in self.parts)
            return f'(word "{escaped}" {inner})'
        return f'(word "{escaped}")'


@dataclass
class Command(Node):
    """A simple command (words + redirections)."""

    words: list[Word]
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, words: list[Word], redirects: list[Node] = None):
        self.kind = "command"
        self.words = words
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        parts = [w.to_sexp() for w in self.words]
        parts.extend(r.to_sexp() for r in self.redirects)
        inner = " ".join(parts)
        return f"(command {inner})"


@dataclass
class Pipeline(Node):
    """A pipeline of commands."""

    commands: list[Node]

    def __init__(self, commands: list[Node]):
        self.kind = "pipeline"
        self.commands = commands

    def to_sexp(self) -> str:
        inner = " ".join(c.to_sexp() for c in self.commands)
        return f"(pipeline {inner})"


@dataclass
class List(Node):
    """A list of pipelines with operators."""

    parts: list[Node]  # alternating: pipeline, operator, pipeline, ...

    def __init__(self, parts: list[Node]):
        self.kind = "list"
        self.parts = parts

    def to_sexp(self) -> str:
        inner = " ".join(p.to_sexp() for p in self.parts)
        return f"(list {inner})"


@dataclass
class Operator(Node):
    """An operator token (&&, ||, ;, &, |)."""

    op: str

    def __init__(self, op: str):
        self.kind = "operator"
        self.op = op

    def to_sexp(self) -> str:
        names = {
            "&&": "and",
            "||": "or",
            ";": "semi",
            "&": "bg",
            "|": "pipe",
        }
        return f"({names.get(self.op, self.op)})"


@dataclass
class Empty(Node):
    """Empty input."""

    def __init__(self):
        self.kind = "empty"

    def to_sexp(self) -> str:
        return "(empty)"


@dataclass
class Redirect(Node):
    """A redirection."""

    op: str
    target: Word
    fd: int | None = None

    def __init__(self, op: str, target: Word, fd: int = None):
        self.kind = "redirect"
        self.op = op
        self.target = target
        self.fd = fd

    def to_sexp(self) -> str:
        if self.fd is not None:
            return f'(redirect "{self.fd}{self.op}" {self.target.to_sexp()})'
        return f'(redirect "{self.op}" {self.target.to_sexp()})'


@dataclass
class HereDoc(Node):
    """A here document <<DELIM ... DELIM."""

    delimiter: str
    content: str
    strip_tabs: bool = False
    quoted: bool = False
    fd: int | None = None

    def __init__(
        self,
        delimiter: str,
        content: str,
        strip_tabs: bool = False,
        quoted: bool = False,
        fd: int = None,
    ):
        self.kind = "heredoc"
        self.delimiter = delimiter
        self.content = content
        self.strip_tabs = strip_tabs
        self.quoted = quoted
        self.fd = fd

    def to_sexp(self) -> str:
        escaped_content = self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        if self.quoted:
            kind = "heredoc-quoted"
        elif self.strip_tabs:
            kind = "heredoc-strip"
        else:
            kind = "heredoc"
        if self.fd is not None:
            return f'({kind} "{self.delimiter}" "{escaped_content}" {self.fd})'
        return f'({kind} "{self.delimiter}" "{escaped_content}")'


@dataclass
class Subshell(Node):
    """A subshell ( list )."""

    body: Node

    def __init__(self, body: Node):
        self.kind = "subshell"
        self.body = body

    def to_sexp(self) -> str:
        return f"(subshell {self.body.to_sexp()})"


@dataclass
class BraceGroup(Node):
    """A brace group { list; }."""

    body: Node

    def __init__(self, body: Node):
        self.kind = "brace-group"
        self.body = body

    def to_sexp(self) -> str:
        return f"(brace-group {self.body.to_sexp()})"


@dataclass
class If(Node):
    """An if statement."""

    condition: Node
    then_body: Node
    else_body: Node | None = None

    def __init__(self, condition: Node, then_body: Node, else_body: Node = None):
        self.kind = "if"
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

    def to_sexp(self) -> str:
        result = f"(if {self.condition.to_sexp()} {self.then_body.to_sexp()}"
        if self.else_body:
            result += f" {self.else_body.to_sexp()}"
        return result + ")"


@dataclass
class While(Node):
    """A while loop."""

    condition: Node
    body: Node

    def __init__(self, condition: Node, body: Node):
        self.kind = "while"
        self.condition = condition
        self.body = body

    def to_sexp(self) -> str:
        return f"(while {self.condition.to_sexp()} {self.body.to_sexp()})"


@dataclass
class Until(Node):
    """An until loop."""

    condition: Node
    body: Node

    def __init__(self, condition: Node, body: Node):
        self.kind = "until"
        self.condition = condition
        self.body = body

    def to_sexp(self) -> str:
        return f"(until {self.condition.to_sexp()} {self.body.to_sexp()})"


@dataclass
class For(Node):
    """A for loop."""

    var: str
    words: list[Word] | None
    body: Node

    def __init__(self, var: str, words: list[Word] | None, body: Node):
        self.kind = "for"
        self.var = var
        self.words = words
        self.body = body

    def to_sexp(self) -> str:
        if self.words:
            # Escape quotes in word values
            def escape(s: str) -> str:
                return s.replace("\\", "\\\\").replace('"', '\\"')

            word_strs = " ".join(f'"{escape(w.value)}"' for w in self.words)
            return f'(for "{self.var}" (words {word_strs}) {self.body.to_sexp()})'
        return f'(for "{self.var}" {self.body.to_sexp()})'


@dataclass
class Case(Node):
    """A case statement."""

    word: Word
    patterns: list["CasePattern"]

    def __init__(self, word: Word, patterns: list["CasePattern"]):
        self.kind = "case"
        self.word = word
        self.patterns = patterns

    def to_sexp(self) -> str:
        inner = " ".join(p.to_sexp() for p in self.patterns)
        return f"(case {self.word.to_sexp()} {inner})"


@dataclass
class CasePattern(Node):
    """A pattern clause in a case statement."""

    pattern: str
    body: Node | None

    def __init__(self, pattern: str, body: Node | None):
        self.kind = "pattern"
        self.pattern = pattern
        self.body = body

    def to_sexp(self) -> str:
        escaped = self.pattern.replace("\\", "\\\\").replace('"', '\\"')
        if self.body:
            return f'(pattern "{escaped}" {self.body.to_sexp()})'
        return f'(pattern "{escaped}")'


@dataclass
class Function(Node):
    """A function definition."""

    name: str
    body: Node

    def __init__(self, name: str, body: Node):
        self.kind = "function"
        self.name = name
        self.body = body

    def to_sexp(self) -> str:
        return f'(function "{self.name}" {self.body.to_sexp()})'


@dataclass
class ParamExpansion(Node):
    """A parameter expansion ${var} or ${var:-default}."""

    param: str
    op: str | None = None
    arg: str | None = None

    def __init__(self, param: str, op: str = None, arg: str = None):
        self.kind = "param"
        self.param = param
        self.op = op
        self.arg = arg

    def to_sexp(self) -> str:
        escaped_param = self.param.replace("\\", "\\\\").replace('"', '\\"')
        if self.op is not None:
            escaped_op = self.op.replace("\\", "\\\\").replace('"', '\\"')
            escaped_arg = (self.arg or "").replace("\\", "\\\\").replace('"', '\\"')
            return f'(param "{escaped_param}" "{escaped_op}" "{escaped_arg}")'
        return f'(param "{escaped_param}")'


@dataclass
class ParamLength(Node):
    """A parameter length expansion ${#var}."""

    param: str

    def __init__(self, param: str):
        self.kind = "param-len"
        self.param = param

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace('"', '\\"')
        return f'(param-len "{escaped}")'


@dataclass
class ParamIndirect(Node):
    """An indirect parameter expansion ${!var}."""

    param: str

    def __init__(self, param: str):
        self.kind = "param-indirect"
        self.param = param

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace('"', '\\"')
        return f'(param-indirect "{escaped}")'


@dataclass
class CommandSubstitution(Node):
    """A command substitution $(...) or `...`."""

    command: Node

    def __init__(self, command: Node):
        self.kind = "cmdsub"
        self.command = command

    def to_sexp(self) -> str:
        return f"(cmdsub {self.command.to_sexp()})"


@dataclass
class ArithmeticExpansion(Node):
    """An arithmetic expansion $((...))."""

    expression: str

    def __init__(self, expression: str):
        self.kind = "arith"
        self.expression = expression

    def to_sexp(self) -> str:
        escaped = self.expression.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(arith "{escaped}")'


@dataclass
class ArithmeticCommand(Node):
    """An arithmetic command ((...))."""

    expression: str

    def __init__(self, expression: str):
        self.kind = "arith-cmd"
        self.expression = expression

    def to_sexp(self) -> str:
        escaped = self.expression.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(arith-cmd "{escaped}")'


@dataclass
class ProcessSubstitution(Node):
    """A process substitution <(...) or >(...)."""

    direction: str  # "<" for input, ">" for output
    command: Node

    def __init__(self, direction: str, command: Node):
        self.kind = "procsub"
        self.direction = direction
        self.command = command

    def to_sexp(self) -> str:
        return f'(procsub "{self.direction}" {self.command.to_sexp()})'
