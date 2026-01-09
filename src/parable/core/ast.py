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
        import re
        value = self.value
        # Strip $ from ANSI-C quotes $'...' and locale strings $"..."
        value = re.sub(r"\$'", "'", value)
        value = re.sub(r'\$"', '"', value)
        # Double backslash for unknown escapes in ANSI-C strings (e.g., \q -> \\q)
        # Known escapes: \n \t \r \a \b \f \v \\ \' \" \0 \x \u \U \c \e \E
        value = re.sub(r"\\([^ntrabfv\\'\"0xuUcEe\\])", r"\\\\\1", value)
        # Format command substitutions with oracle pretty-printing
        value = self._format_command_substitutions(value)
        # Escape double quotes (but not inside single-quoted ANSI-C strings)
        escaped = value.replace('"', '\\"').replace("\n", "\\n")
        return f'(word "{escaped}")'

    def _format_command_substitutions(self, value: str) -> str:
        """Replace $(...)  content with oracle-formatted AST output."""
        cmdsub_parts = [p for p in self.parts if isinstance(p, CommandSubstitution)]
        if not cmdsub_parts:
            return value
        result = []
        i = 0
        cmdsub_idx = 0
        while i < len(value):
            # Check for $( command substitution
            if value[i : i + 2] == "$(" and cmdsub_idx < len(cmdsub_parts):
                # Find matching close paren
                depth = 1
                j = i + 2
                in_single = False
                in_double = False
                while j < len(value) and depth > 0:
                    c = value[j]
                    if c == "\\" and j + 1 < len(value) and not in_single:
                        j += 2
                        continue
                    if c == "'" and not in_double:
                        in_single = not in_single
                    elif c == '"' and not in_single:
                        in_double = not in_double
                    elif c == "(" and not in_single and not in_double:
                        depth += 1
                    elif c == ")" and not in_single and not in_double:
                        depth -= 1
                    j += 1
                # Format this command substitution
                node = cmdsub_parts[cmdsub_idx]
                formatted = _format_cmdsub_node(node.command)
                result.append(f"$({formatted})")
                cmdsub_idx += 1
                i = j
            # Check for backtick command substitution
            elif value[i] == "`" and cmdsub_idx < len(cmdsub_parts):
                # Find matching backtick
                j = i + 1
                while j < len(value):
                    if value[j] == "\\" and j + 1 < len(value):
                        j += 2
                        continue
                    if value[j] == "`":
                        j += 1
                        break
                    j += 1
                # Keep backtick substitutions as-is (oracle doesn't reformat them)
                result.append(value[i:j])
                cmdsub_idx += 1
                i = j
            else:
                result.append(value[i])
                i += 1
        return "".join(result)


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
        # Build list of (cmd, needs_pipe_both_redirect) filtering out PipeBoth markers
        cmds = []
        for i, cmd in enumerate(self.commands):
            if isinstance(cmd, PipeBoth):
                continue
            # Check if next element is PipeBoth
            needs_redirect = (i + 1 < len(self.commands) and isinstance(self.commands[i + 1], PipeBoth))
            cmds.append((cmd, needs_redirect))
        if len(cmds) == 1:
            cmd, needs = cmds[0]
            return self._cmd_sexp(cmd, needs)
        # Nest right-associatively: (pipe a (pipe b c))
        last_cmd, last_needs = cmds[-1]
        result = self._cmd_sexp(last_cmd, last_needs)
        for cmd, needs in reversed(cmds[:-1]):
            if needs and not isinstance(cmd, Command):
                # Compound command: redirect as sibling in pipe
                result = f'(pipe {cmd.to_sexp()} (redirect ">&" 1) {result})'
            else:
                result = f"(pipe {self._cmd_sexp(cmd, needs)} {result})"
        return result

    def _cmd_sexp(self, cmd: Node, needs_redirect: bool) -> str:
        """Get s-expression for a command, optionally injecting pipe-both redirect."""
        if not needs_redirect:
            return cmd.to_sexp()
        if isinstance(cmd, Command):
            # Inject redirect inside command
            parts = [w.to_sexp() for w in cmd.words]
            parts.extend(r.to_sexp() for r in cmd.redirects)
            parts.append('(redirect ">&" 1)')
            return f"(command {' '.join(parts)})"
        # Compound command handled by caller
        return cmd.to_sexp()


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
        import re
        # Strip fd prefix from operator (e.g., "2>" -> ">", "{fd}>" -> ">")
        op = self.op.lstrip("0123456789")
        op = re.sub(r"^\{[a-zA-Z_][a-zA-Z_0-9]*\}", "", op)
        target_val = self.target.value
        # Strip $ from ANSI-C $'...' and locale strings $"..."
        target_val = re.sub(r"\$'", "'", target_val)
        target_val = re.sub(r'\$"', '"', target_val)
        # For here-strings, expand ANSI-C escape sequences
        if op == "<<<" and target_val.startswith("'") and target_val.endswith("'"):
            inner = target_val[1:-1]
            inner = inner.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
            target_val = "'" + inner + "'"
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
            else:
                # Variable fd dup like >&$fd - strip the & from target
                return f'(redirect "{op}" "{target_val[1:]}")'
        return f'(redirect "{op}" "{target_val}")'


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
        op = "<<-" if self.strip_tabs else "<<"
        return f'(redirect "{op}" "{self.content}")'


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
        # Oracle format: (for (word "var") (in (word "a") ...) body)
        redirect_strs = " ".join(r.to_sexp() for r in self.redirects)
        suffix = f" {redirect_strs}" if redirect_strs else ""
        var_escaped = self.var.replace("\\", "\\\\").replace('"', '\\"')
        if self.words:
            word_strs = " ".join(w.to_sexp() for w in self.words)
            return f'(for (word "{var_escaped}") (in {word_strs}) {self.body.to_sexp()}{suffix})'
        return f'(for (word "{var_escaped}") {self.body.to_sexp()}{suffix})'


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
        # Oracle format: (arith-for (init (word "x")) (test (word "y")) (step (word "z")) body)
        def escape(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')
        parts = [self.body.to_sexp()]
        parts.extend(r.to_sexp() for r in self.redirects)
        inner = " ".join(parts)
        init_val = self.init if self.init else "1"
        cond_val = self.cond if self.cond else "1"
        incr_val = self.incr if self.incr else "1"
        return (
            f'(arith-for (init (word "{escape(init_val)}")) '
            f'(test (word "{escape(cond_val)}")) '
            f'(step (word "{escape(incr_val)}")) {inner})'
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
        # Oracle format: (select (word "var") (in (word "a") ...) body)
        redirect_strs = " ".join(r.to_sexp() for r in self.redirects)
        suffix = f" {redirect_strs}" if redirect_strs else ""
        var_escaped = self.var.replace("\\", "\\\\").replace('"', '\\"')
        if self.words is not None:
            word_strs = " ".join(w.to_sexp() for w in self.words)
            in_clause = f"(in {word_strs})" if self.words else "(in)"
            return f'(select (word "{var_escaped}") {in_clause} {self.body.to_sexp()}{suffix})'
        return f'(select (word "{var_escaped}") {self.body.to_sexp()}{suffix})'


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
        # Oracle format: (pattern ((word "a") (word "b")) body)
        # Split pattern by | respecting escapes
        alternatives = []
        current = []
        i = 0
        while i < len(self.pattern):
            if self.pattern[i] == "\\" and i + 1 < len(self.pattern):
                current.append(self.pattern[i : i + 2])
                i += 2
            elif self.pattern[i] == "|":
                alternatives.append("".join(current))
                current = []
                i += 1
            else:
                current.append(self.pattern[i])
                i += 1
        alternatives.append("".join(current))
        word_list = []
        for alt in alternatives:
            escaped = alt.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t")
            word_list.append(f'(word "{escaped}")')
        pattern_str = " ".join(word_list)
        parts = [f"(pattern ({pattern_str})"]
        if self.body:
            parts.append(f" {self.body.to_sexp()}")
        else:
            parts.append(" ()")
        # Oracle doesn't output fallthrough/falltest markers
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
    raw_content: str  # Raw expression text for oracle-compatible output

    def __init__(self, expression: "Node | None", redirects: list[Node] = None, raw_content: str = ""):
        self.kind = "arith-cmd"
        self.expression = expression
        self.redirects = redirects or []
        self.raw_content = raw_content

    def to_sexp(self) -> str:
        # Oracle format: (arith (word "content"))
        escaped = self.raw_content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(arith (word "{escaped}"))'


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
            return f"(time -p {self.pipeline.to_sexp()})"
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
        # Oracle format: (cond ...) not (cond-expr ...)
        if isinstance(self.body, str):
            escaped = self.body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            if self.redirects:
                inner = " ".join(r.to_sexp() for r in self.redirects)
                return f'(cond "{escaped}" {inner})'
            return f'(cond "{escaped}")'
        if self.redirects:
            inner = " ".join(r.to_sexp() for r in self.redirects)
            return f"(cond {self.body.to_sexp()} {inner})"
        return f"(cond {self.body.to_sexp()})"


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
        # Oracle format: (cond-unary "-f" (cond-term "file"))
        # cond-term preserves content as-is (no backslash escaping)
        return f'(cond-unary "{self.op}" (cond-term "{self.operand.value}"))'


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
        # Oracle format: (cond-binary "==" (cond-term "x") (cond-term "y"))
        # cond-term preserves content as-is (no backslash escaping)
        return f'(cond-binary "{self.op}" (cond-term "{self.left.value}") (cond-term "{self.right.value}"))'


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
        # Oracle ignores negation - just output the operand
        return self.operand.to_sexp()


@dataclass
class CondParen(Node):
    """Parenthesized group in [[ ]], e.g., ( expr )."""

    inner: Node

    def __init__(self, inner: Node):
        self.kind = "cond-paren"
        self.inner = inner

    def to_sexp(self) -> str:
        return f"(cond-expr {self.inner.to_sexp()})"


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
        # Use provided name for compound commands, "COPROC" for simple commands
        name = self.name if self.name else "COPROC"
        return f'(coproc "{name}" {self.command.to_sexp()})'


def _format_cmdsub_node(node: Node, indent: int = 0) -> str:
    """Format an AST node for command substitution output (oracle pretty-print format)."""
    sp = " " * indent
    inner_sp = " " * (indent + 4)
    if isinstance(node, Empty):
        return ""
    if isinstance(node, Command):
        parts = [w.value for w in node.words]
        for r in node.redirects:
            parts.append(_format_redirect(r))
        return " ".join(parts)
    if isinstance(node, Pipeline):
        return " | ".join(_format_cmdsub_node(cmd, indent) for cmd in node.commands)
    if isinstance(node, List):
        parts = []
        for p in node.parts:
            if isinstance(p, Operator):
                parts.append(p.op)
            else:
                parts.append(_format_cmdsub_node(p, indent))
        return " ".join(parts)
    if isinstance(node, If):
        cond = _format_cmdsub_node(node.condition, indent)
        then_body = _format_cmdsub_node(node.then_body, indent + 4)
        result = f"if {cond}; then\n{inner_sp}{then_body};"
        if node.else_body:
            else_body = _format_cmdsub_node(node.else_body, indent + 4)
            result += f"\n{sp}else\n{inner_sp}{else_body};"
        result += f"\n{sp}fi"
        return result
    if isinstance(node, While):
        cond = _format_cmdsub_node(node.condition, indent)
        body = _format_cmdsub_node(node.body, indent + 4)
        return f"while {cond}; do\n{inner_sp}{body};\n{sp}done"
    if isinstance(node, Until):
        cond = _format_cmdsub_node(node.condition, indent)
        body = _format_cmdsub_node(node.body, indent + 4)
        return f"until {cond}; do\n{inner_sp}{body};\n{sp}done"
    if isinstance(node, For):
        var = node.var
        body = _format_cmdsub_node(node.body, indent + 4)
        if node.words:
            words = " ".join(w.value for w in node.words)
            return f"for {var} in {words};\ndo\n{inner_sp}{body};\n{sp}done"
        return f"for {var};\ndo\n{inner_sp}{body};\n{sp}done"
    if isinstance(node, Case):
        word = node.word.value
        patterns = []
        for p in node.patterns:
            pat = p.pattern.replace("|", " | ")
            if p.body:
                body = _format_cmdsub_node(p.body, indent + 8)
                patterns.append(f"{pat})\n{' ' * (indent + 8)}{body}\n{' ' * (indent + 4)};;")
            else:
                patterns.append(f"{pat})\n{' ' * (indent + 4)};;")
        pattern_str = "\n" + f"\n{' ' * (indent + 4)}".join(patterns)
        return f"case {word} in{pattern_str}\n{sp}esac"
    if isinstance(node, Function):
        name = node.name
        body = _format_cmdsub_node(node.body, indent + 4)
        return f"function {name} () \n{{ \n{inner_sp}{body}\n}}"
    if isinstance(node, Subshell):
        body = _format_cmdsub_node(node.body, indent)
        return f"( {body} )"
    if isinstance(node, BraceGroup):
        body = _format_cmdsub_node(node.body, indent)
        return f"{{ {body}; }}"
    # Fallback: return empty for unknown types
    return ""


def _format_redirect(r: "Redirect | HereDoc") -> str:
    """Format a redirect for command substitution output."""
    if isinstance(r, HereDoc):
        return f"<< {r.delimiter}"
    return f"{r.op} {r.target.value}"
