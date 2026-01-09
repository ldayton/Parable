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
        if len(self.commands) == 1:
            return self.commands[0].to_sexp()
        # Nest right-associatively: (pipe a (pipe b c))
        result = self.commands[-1].to_sexp()
        for cmd in reversed(self.commands[:-1]):
            result = f"(pipe {cmd.to_sexp()} {result})"
        return result


@dataclass
class List(Node):
    """A list of pipelines with operators."""

    parts: list[Node]  # alternating: pipeline, operator, pipeline, ...

    def __init__(self, parts: list[Node]):
        self.kind = "list"
        self.parts = parts

    def to_sexp(self) -> str:
        # parts = [cmd, op, cmd, op, cmd, ...]
        # Bash precedence: && and || bind tighter than ; and &
        parts = list(self.parts)
        op_names = {"&&": "and", "||": "or", ";": "semi", "&": "background"}
        # Strip trailing ; (bash ignores it)
        while len(parts) > 1 and isinstance(parts[-1], Operator) and parts[-1].op == ";":
            parts = parts[:-1]
        if len(parts) == 1:
            return parts[0].to_sexp()
        # Handle trailing & as unary background operator
        if isinstance(parts[-1], Operator) and parts[-1].op == "&":
            inner_parts = parts[:-1]
            if len(inner_parts) == 1:
                return f"(background {inner_parts[0].to_sexp()})"
            inner_list = List(inner_parts)
            return f"(background {inner_list.to_sexp()})"
        # Process by precedence: first split on ; and &, then on && and ||
        return self._to_sexp_with_precedence(parts, op_names)

    def _to_sexp_with_precedence(self, parts: list, op_names: dict) -> str:
        # Split on low-precedence ops (; &) first
        low_prec = {";", "&"}
        # Find rightmost low-precedence operator
        for i in range(len(parts) - 2, 0, -2):
            if isinstance(parts[i], Operator) and parts[i].op in low_prec:
                left = parts[:i]
                op = parts[i]
                right = parts[i + 1 :]
                left_sexp = List(left).to_sexp() if len(left) > 1 else left[0].to_sexp()
                right_sexp = List(right).to_sexp() if len(right) > 1 else right[0].to_sexp()
                return f"({op_names[op.op]} {left_sexp} {right_sexp})"
        # No low-prec ops, process high-prec ops (&&, ||) left-associatively
        result = parts[0].to_sexp()
        for i in range(1, len(parts) - 1, 2):
            op = parts[i]
            cmd = parts[i + 1]
            op_name = op_names.get(op.op, op.op)
            result = f"({op_name} {result} {cmd.to_sexp()})"
        return result


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
class PipeBoth(Node):
    """Marker for |& pipe (stdout + stderr)."""

    def __init__(self):
        self.kind = "pipe-both"

    def to_sexp(self) -> str:
        return "(pipe-both)"


@dataclass
class Empty(Node):
    """Empty input."""

    def __init__(self):
        self.kind = "empty"

    def to_sexp(self) -> str:
        return "(empty)"


@dataclass
class Comment(Node):
    """A comment (# to end of line)."""

    text: str

    def __init__(self, text: str):
        self.kind = "comment"
        self.text = text

    def to_sexp(self) -> str:
        return f'(comment "{self.text}")'


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
        # Strip fd prefix from operator (e.g., "2>" -> ">")
        op = self.op.lstrip("0123456789")
        target_val = self.target.value
        # For fd duplication, target starts with & (e.g., "&1", "&2", "&-")
        if target_val.startswith("&"):
            # Determine the real operator
            if op == ">":
                op = ">&"
            elif op == "<":
                op = "<&"
            fd_target = target_val[1:].rstrip("-")  # "&1" -> "1", "&1-" -> "1"
            if fd_target.isdigit():
                return f'(redirect "{op}" {fd_target})'
            elif target_val == "&-":
                return f'(redirect ">&-" 0)'
        escaped = target_val.replace("\\", "\\\\").replace("\n", "\\n")
        return f'(redirect "{op}" "{escaped}")'


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
        escaped_content = (
            self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        )
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
    redirects: list["Redirect | HereDoc"] | None = None

    def __init__(self, body: Node, redirects: list["Redirect | HereDoc"] | None = None):
        self.kind = "subshell"
        self.body = body
        self.redirects = redirects

    def to_sexp(self) -> str:
        result = f"(subshell {self.body.to_sexp()}"
        if self.redirects:
            for r in self.redirects:
                result += f" {r.to_sexp()}"
        return result + ")"


@dataclass
class BraceGroup(Node):
    """A brace group { list; }."""

    body: Node
    redirects: list["Redirect | HereDoc"] | None = None

    def __init__(self, body: Node, redirects: list["Redirect | HereDoc"] | None = None):
        self.kind = "brace-group"
        self.body = body
        self.redirects = redirects

    def to_sexp(self) -> str:
        result = f"(brace-group {self.body.to_sexp()}"
        if self.redirects:
            for r in self.redirects:
                result += f" {r.to_sexp()}"
        return result + ")"


@dataclass
class If(Node):
    """An if statement."""

    condition: Node
    then_body: Node
    else_body: Node | None = None
    redirects: list[Node] = field(default_factory=list)

    def __init__(
        self, condition: Node, then_body: Node, else_body: Node = None, redirects: list[Node] = None
    ):
        self.kind = "if"
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        result = f"(if {self.condition.to_sexp()} {self.then_body.to_sexp()}"
        if self.else_body:
            result += f" {self.else_body.to_sexp()}"
        for r in self.redirects:
            result += f" {r.to_sexp()}"
        return result + ")"


@dataclass
class While(Node):
    """A while loop."""

    condition: Node
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, condition: Node, body: Node, redirects: list[Node] = None):
        self.kind = "while"
        self.condition = condition
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        parts = [self.condition.to_sexp(), self.body.to_sexp()]
        parts.extend(r.to_sexp() for r in self.redirects)
        return f"(while {' '.join(parts)})"


@dataclass
class Until(Node):
    """An until loop."""

    condition: Node
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, condition: Node, body: Node, redirects: list[Node] = None):
        self.kind = "until"
        self.condition = condition
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        parts = [self.condition.to_sexp(), self.body.to_sexp()]
        parts.extend(r.to_sexp() for r in self.redirects)
        return f"(until {' '.join(parts)})"


@dataclass
class For(Node):
    """A for loop."""

    var: str
    words: list[Word] | None
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(
        self, var: str, words: list[Word] | None, body: Node, redirects: list[Node] = None
    ):
        self.kind = "for"
        self.var = var
        self.words = words
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        def escape(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')

        redirect_strs = " ".join(r.to_sexp() for r in self.redirects)
        suffix = f" {redirect_strs}" if redirect_strs else ""

        if self.words:
            word_strs = " ".join(f'"{escape(w.value)}"' for w in self.words)
            return f'(for "{self.var}" (words {word_strs}) {self.body.to_sexp()}{suffix})'
        return f'(for "{self.var}" {self.body.to_sexp()}{suffix})'


@dataclass
class ForArith(Node):
    """A C-style for loop: for ((init; cond; incr)); do ... done."""

    init: str
    cond: str
    incr: str
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, init: str, cond: str, incr: str, body: Node, redirects: list[Node] = None):
        self.kind = "for-arith"
        self.init = init
        self.cond = cond
        self.incr = incr
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        def escape(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')

        parts = [self.body.to_sexp()]
        parts.extend(r.to_sexp() for r in self.redirects)
        inner = " ".join(parts)
        return (
            f'(for-arith "{escape(self.init)}" "{escape(self.cond)}" "{escape(self.incr)}" {inner})'
        )


@dataclass
class Select(Node):
    """A select statement."""

    var: str
    words: list[Word] | None
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(
        self, var: str, words: list[Word] | None, body: Node, redirects: list[Node] = None
    ):
        self.kind = "select"
        self.var = var
        self.words = words
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        def escape(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')

        parts = []
        if self.words is not None:
            word_strs = " ".join(f'"{escape(w.value)}"' for w in self.words)
            parts.append(f"(words {word_strs})" if self.words else "(words)")
        parts.append(self.body.to_sexp())
        parts.extend(r.to_sexp() for r in self.redirects)
        inner = " ".join(parts)
        return f'(select "{self.var}" {inner})'


@dataclass
class Case(Node):
    """A case statement."""

    word: Word
    patterns: list["CasePattern"]
    redirects: list[Node]

    def __init__(self, word: Word, patterns: list["CasePattern"], redirects: list[Node] = None):
        self.kind = "case"
        self.word = word
        self.patterns = patterns
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        inner = " ".join(p.to_sexp() for p in self.patterns)
        if self.redirects:
            redir_str = " ".join(r.to_sexp() for r in self.redirects)
            return f"(case {self.word.to_sexp()} {inner} {redir_str})"
        return f"(case {self.word.to_sexp()} {inner})"


@dataclass
class CasePattern(Node):
    """A pattern clause in a case statement."""

    pattern: str
    body: Node | None
    terminator: str = ";;"  # ";;", ";&", or ";;&"

    def __init__(self, pattern: str, body: Node | None, terminator: str = ";;"):
        self.kind = "pattern"
        self.pattern = pattern
        self.body = body
        self.terminator = terminator

    def to_sexp(self) -> str:
        escaped = self.pattern.replace("\\", "\\\\").replace('"', '\\"')
        parts = [f'(pattern "{escaped}"']
        if self.body:
            parts.append(f" {self.body.to_sexp()}")
        if self.terminator == ";&":
            parts.append(" (fallthrough)")
        elif self.terminator == ";;&":
            parts.append(" (falltest)")
        parts.append(")")
        return "".join(parts)


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
    """An indirect parameter expansion ${!var} or ${!var<op><arg>}."""

    param: str
    op: str | None
    arg: str | None

    def __init__(self, param: str, op: str | None = None, arg: str | None = None):
        self.kind = "param-indirect"
        self.param = param
        self.op = op
        self.arg = arg

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace('"', '\\"')
        if self.op is not None:
            escaped_op = self.op.replace("\\", "\\\\").replace('"', '\\"')
            escaped_arg = (self.arg or "").replace("\\", "\\\\").replace('"', '\\"')
            return f'(param-indirect "{escaped}" "{escaped_op}" "{escaped_arg}")'
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
    """An arithmetic expansion $((...)) with parsed internals."""

    expression: "Node | None"  # Parsed arithmetic expression, or None for empty

    def __init__(self, expression: "Node | None"):
        self.kind = "arith"
        self.expression = expression

    def to_sexp(self) -> str:
        if self.expression is None:
            return "(arith)"
        return f"(arith {self.expression.to_sexp()})"


@dataclass
class ArithmeticCommand(Node):
    """An arithmetic command ((...)) with parsed internals."""

    expression: "Node | None"  # Parsed arithmetic expression, or None for empty
    redirects: list[Node]

    def __init__(self, expression: "Node | None", redirects: list[Node] = None):
        self.kind = "arith-cmd"
        self.expression = expression
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        if self.expression is None:
            if self.redirects:
                inner = " ".join(r.to_sexp() for r in self.redirects)
                return f"(arith-cmd {inner})"
            return "(arith-cmd)"
        if self.redirects:
            inner = " ".join(r.to_sexp() for r in self.redirects)
            return f"(arith-cmd {self.expression.to_sexp()} {inner})"
        return f"(arith-cmd {self.expression.to_sexp()})"


# Arithmetic expression nodes


@dataclass
class ArithNumber(Node):
    """A numeric literal in arithmetic context."""

    value: str  # Raw string (may be hex, octal, base#n)

    def __init__(self, value: str):
        self.kind = "number"
        self.value = value

    def to_sexp(self) -> str:
        return f'(number "{self.value}")'


@dataclass
class ArithVar(Node):
    """A variable reference in arithmetic context (without $)."""

    name: str

    def __init__(self, name: str):
        self.kind = "var"
        self.name = name

    def to_sexp(self) -> str:
        return f'(var "{self.name}")'


@dataclass
class ArithBinaryOp(Node):
    """A binary operation in arithmetic."""

    op: str
    left: Node
    right: Node

    def __init__(self, op: str, left: Node, right: Node):
        self.kind = "binary-op"
        self.op = op
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f'(binary-op "{self.op}" {self.left.to_sexp()} {self.right.to_sexp()})'


@dataclass
class ArithUnaryOp(Node):
    """A unary operation in arithmetic."""

    op: str
    operand: Node

    def __init__(self, op: str, operand: Node):
        self.kind = "unary-op"
        self.op = op
        self.operand = operand

    def to_sexp(self) -> str:
        return f'(unary-op "{self.op}" {self.operand.to_sexp()})'


@dataclass
class ArithPreIncr(Node):
    """Pre-increment ++var."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "pre-incr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(pre-incr {self.operand.to_sexp()})"


@dataclass
class ArithPostIncr(Node):
    """Post-increment var++."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "post-incr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(post-incr {self.operand.to_sexp()})"


@dataclass
class ArithPreDecr(Node):
    """Pre-decrement --var."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "pre-decr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(pre-decr {self.operand.to_sexp()})"


@dataclass
class ArithPostDecr(Node):
    """Post-decrement var--."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "post-decr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(post-decr {self.operand.to_sexp()})"


@dataclass
class ArithAssign(Node):
    """Assignment operation (=, +=, -=, etc.)."""

    op: str
    target: Node
    value: Node

    def __init__(self, op: str, target: Node, value: Node):
        self.kind = "assign"
        self.op = op
        self.target = target
        self.value = value

    def to_sexp(self) -> str:
        return f'(assign "{self.op}" {self.target.to_sexp()} {self.value.to_sexp()})'


@dataclass
class ArithTernary(Node):
    """Ternary conditional expr ? expr : expr."""

    condition: Node
    if_true: Node
    if_false: Node

    def __init__(self, condition: Node, if_true: Node, if_false: Node):
        self.kind = "ternary"
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def to_sexp(self) -> str:
        return f"(ternary {self.condition.to_sexp()} {self.if_true.to_sexp()} {self.if_false.to_sexp()})"


@dataclass
class ArithComma(Node):
    """Comma operator expr, expr."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "comma"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f"(comma {self.left.to_sexp()} {self.right.to_sexp()})"


@dataclass
class ArithSubscript(Node):
    """Array subscript arr[expr]."""

    array: str
    index: Node

    def __init__(self, array: str, index: Node):
        self.kind = "subscript"
        self.array = array
        self.index = index

    def to_sexp(self) -> str:
        return f'(subscript "{self.array}" {self.index.to_sexp()})'


@dataclass
class ArithEscape(Node):
    """An escaped character in arithmetic expression."""

    char: str

    def __init__(self, char: str):
        self.kind = "escape"
        self.char = char

    def to_sexp(self) -> str:
        return f'(escape "{self.char}")'


@dataclass
class ArithDeprecated(Node):
    """A deprecated arithmetic expansion $[expr]."""

    expression: str

    def __init__(self, expression: str):
        self.kind = "arith-deprecated"
        self.expression = expression

    def to_sexp(self) -> str:
        escaped = self.expression.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(arith-deprecated "{escaped}")'


@dataclass
class AnsiCQuote(Node):
    """An ANSI-C quoted string $'...'."""

    content: str

    def __init__(self, content: str):
        self.kind = "ansi-c"
        self.content = content

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(ansi-c "{escaped}")'


@dataclass
class LocaleString(Node):
    """A locale-translated string $"..."."""

    content: str

    def __init__(self, content: str):
        self.kind = "locale"
        self.content = content

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(locale "{escaped}")'


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


@dataclass
class Negation(Node):
    """Pipeline negation with !."""

    pipeline: Node

    def __init__(self, pipeline: Node):
        self.kind = "negation"
        self.pipeline = pipeline

    def to_sexp(self) -> str:
        return f"(negation {self.pipeline.to_sexp()})"


@dataclass
class Time(Node):
    """Time measurement with time keyword."""

    pipeline: Node
    posix: bool = False  # -p flag

    def __init__(self, pipeline: Node, posix: bool = False):
        self.kind = "time"
        self.pipeline = pipeline
        self.posix = posix

    def to_sexp(self) -> str:
        if self.posix:
            return f'(time {self.pipeline.to_sexp()} "-p")'
        return f"(time {self.pipeline.to_sexp()})"


@dataclass
class ConditionalExpr(Node):
    """A conditional expression [[ expression ]]."""

    body: "Node | str"  # Parsed node or raw string for backwards compat
    redirects: list[Node]

    def __init__(self, body: "Node | str", redirects: list[Node] = None):
        self.kind = "cond-expr"
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        if isinstance(self.body, str):
            escaped = self.body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            if self.redirects:
                inner = " ".join(r.to_sexp() for r in self.redirects)
                return f'(cond-expr "{escaped}" {inner})'
            return f'(cond-expr "{escaped}")'
        if self.redirects:
            inner = " ".join(r.to_sexp() for r in self.redirects)
            return f"(cond-expr {self.body.to_sexp()} {inner})"
        return f"(cond-expr {self.body.to_sexp()})"


@dataclass
class UnaryTest(Node):
    """A unary test in [[ ]], e.g., -f file, -z string."""

    op: str
    operand: Word

    def __init__(self, op: str, operand: Word):
        self.kind = "unary-test"
        self.op = op
        self.operand = operand

    def to_sexp(self) -> str:
        return f'(unary-test "{self.op}" {self.operand.to_sexp()})'


@dataclass
class BinaryTest(Node):
    """A binary test in [[ ]], e.g., $a == $b, file1 -nt file2."""

    op: str
    left: Word
    right: Word

    def __init__(self, op: str, left: Word, right: Word):
        self.kind = "binary-test"
        self.op = op
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f'(binary-test "{self.op}" {self.left.to_sexp()} {self.right.to_sexp()})'


@dataclass
class CondAnd(Node):
    """Logical AND in [[ ]], e.g., expr1 && expr2."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "cond-and"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f"(cond-and {self.left.to_sexp()} {self.right.to_sexp()})"


@dataclass
class CondOr(Node):
    """Logical OR in [[ ]], e.g., expr1 || expr2."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "cond-or"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f"(cond-or {self.left.to_sexp()} {self.right.to_sexp()})"


@dataclass
class CondNot(Node):
    """Logical NOT in [[ ]], e.g., ! expr."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "cond-not"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(cond-not {self.operand.to_sexp()})"


@dataclass
class Array(Node):
    """An array literal (word1 word2 ...)."""

    elements: list[Word]

    def __init__(self, elements: list[Word]):
        self.kind = "array"
        self.elements = elements

    def to_sexp(self) -> str:
        if not self.elements:
            return "(array)"
        inner = " ".join(e.to_sexp() for e in self.elements)
        return f"(array {inner})"


@dataclass
class Coproc(Node):
    """A coprocess coproc [NAME] command."""

    command: Node
    name: str | None = None

    def __init__(self, command: Node, name: str = None):
        self.kind = "coproc"
        self.command = command
        self.name = name

    def to_sexp(self) -> str:
        if self.name:
            return f'(coproc "{self.name}" {self.command.to_sexp()})'
        return f"(coproc {self.command.to_sexp()})"
