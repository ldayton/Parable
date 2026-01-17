#!/usr/bin/env python3
"""Grammar-based generator fuzzer for differential testing.

Generates bash scripts from scratch using grammar rules, then compares
Parable vs bash-oracle to find discrepancies. Supports layered complexity
for incremental testing.
"""

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .common import (
    ORACLE_PATH,
    Discrepancy,
    normalize,
    parse_layer_spec,
    post_process_discrepancies,
    run_oracle,
    run_parable,
)

# Layer definitions - each layer enables constructs from all previous layers
LAYERS = {
    0: "literals",  # bare words, quoted strings
    1: "simple_exp",  # $var, ${var}, special params
    2: "complex_exp",  # ${var:-default}, ${var#pat}, arrays
    3: "cmd_sub",  # $(cmd), `cmd`
    4: "arithmetic",  # $((expr)), ((expr))
    5: "simple_cmd",  # cmd arg1 arg2
    6: "redirections",  # >, <, >>, <<, <<<, <(), >()
    7: "pipelines",  # cmd1 | cmd2, ! cmd
    8: "lists",  # &&, ||, ;, &
    9: "compound_basic",  # { }, ( ), if/then/fi
    10: "loops",  # for, while, until, select
    11: "case_cond",  # case, [[ ]]
    12: "functions",  # f() { }, coproc
}

LAYER_PRESETS = {
    "words": 2,
    "expansions": 4,
    "commands": 5,
    "pipes": 7,
    "control": 10,
    "full": 12,
}


def detect_layer(text: str) -> int:
    """Detect the maximum layer required to parse this input."""
    import re

    layer = 0
    # Layer 12: functions, coproc
    if re.search(r"\b(function\s+\w+|coproc\b|\w+\s*\(\)\s*\{)", text):
        return 12
    # Layer 11: case, [[ ]]
    if re.search(r"\bcase\b.*\besac\b|\[\[", text, re.DOTALL):
        return 11
    # Layer 10: loops
    if re.search(r"\b(for|while|until|select)\b.*\b(do|done)\b", text, re.DOTALL):
        return 10
    # Layer 9: compound commands (brace groups, subshells, if)
    # Brace group: { cmd; } - must have space after {
    # Subshell: ( cmd ) - but not $( or <( or >(
    if re.search(r"\bif\b.*\bthen\b|\bfi\b", text):
        layer = max(layer, 9)
    if re.search(r"(?<![<>$(\[])\(\s*\w", text):  # subshell, not $( or <( or >( or ((
        layer = max(layer, 9)
    if re.search(r"\{\s+\S.*;\s*\}", text):  # brace group
        layer = max(layer, 9)
    # Layer 8: lists
    if re.search(r"&&|\|\||(?<![<>]);(?![;&])|[^<>&]\s*&\s*$", text, re.MULTILINE):
        layer = max(layer, 8)
    # Layer 7: pipelines
    if re.search(r"(?<!\|)\|(?!\||&)|\|&|^\s*!|^\s*time\b", text, re.MULTILINE):
        layer = max(layer, 7)
    # Layer 6: redirections
    if re.search(r"[0-9]*>{1,2}|<{1,3}|>&|<\(|>\(", text):
        layer = max(layer, 6)
    # Layer 5: simple commands (multiple words)
    if re.search(r"^\s*\w+\s+\S", text, re.MULTILINE):
        layer = max(layer, 5)
    # Layer 4: arithmetic
    if re.search(r"\$\(\(|\(\(", text):
        layer = max(layer, 4)
    # Layer 3: command substitution
    if re.search(r"\$\(|`", text):
        layer = max(layer, 3)
    # Layer 2: complex expansions
    if re.search(r"\$\{[^}]*(:-|:=|:\+|:\?|##?|%%?|/|@|\[)", text):
        layer = max(layer, 2)
    # Layer 1: simple expansions
    if re.search(r"\$[\w@*#?$!_]|\$\{[\w@*#?$!_]+\}", text):
        layer = max(layer, 1)
    return layer


# Default probability weights (Csmith-inspired)
DEFAULT_PROBS = {
    # Word generation
    "word_quoted": 0.3,
    "word_double_quoted": 0.6,  # vs single when quoted
    "word_has_expansion": 0.4,
    "expansion_braced": 0.5,
    "expansion_complex": 0.3,  # ${var:-...} vs ${var}
    "expansion_array": 0.1,
    # Command structure
    "cmd_has_args": 0.7,
    "cmd_extra_arg": 0.4,  # probability of each additional arg
    "cmd_has_redirect": 0.2,
    "cmd_has_assignment": 0.1,
    # Pipelines and lists
    "pipeline_continues": 0.3,
    "list_continues": 0.3,
    "list_and": 0.4,  # && vs ||
    "list_background": 0.1,
    # Compound commands
    "if_has_else": 0.4,
    "if_has_elif": 0.2,
    "loop_body_complex": 0.3,
    "case_extra_pattern": 0.3,
    # Recursion
    "nest_cmd_sub": 0.2,
    "nest_compound": 0.3,
}


@dataclass
class GeneratorConfig:
    """Configuration for the generator."""

    max_layer: int = 12
    min_layer: int = 0
    max_depth: int = 5
    probs: dict[str, float] = field(default_factory=lambda: DEFAULT_PROBS.copy())
    seed: int | None = None


class Generator:
    """Grammar-guided bash script generator with layered complexity."""

    # Word pools for generation
    COMMANDS = [
        "echo",
        "cat",
        "grep",
        "sed",
        "awk",
        "wc",
        "sort",
        "head",
        "tail",
        "tr",
        "cut",
        "true",
        "false",
        "test",
        "pwd",
        "ls",
        "cd",
        "read",
        "printf",
    ]
    VARIABLES = ["var", "x", "y", "name", "file", "dir", "result", "tmp", "i", "n", "str", "arr"]
    WORDS = [
        "hello",
        "world",
        "foo",
        "bar",
        "baz",
        "test",
        "file",
        "data",
        "output",
        "input",
        "value",
        "arg",
    ]
    PATTERNS = ["*", "?", "[abc]", "[0-9]", "*.txt", "test*", "*file*"]
    SPECIAL_PARAMS = ["@", "*", "#", "?", "$", "!", "0", "1", "2", "_"]

    def __init__(self, config: GeneratorConfig | None = None):
        self.config = config or GeneratorConfig()
        self.depth = 0
        self.heredoc_stack: list[tuple[str, bool]] = []  # (delimiter, quoted)
        self.rng = random.Random(self.config.seed)

    def _prob(self, key: str) -> bool:
        """Check probability for a given key."""
        return self.rng.random() < self.config.probs.get(key, 0.5)

    def _choice(self, items: list) -> any:
        """Random choice from list."""
        return self.rng.choice(items)

    def _layer_enabled(self, layer: int) -> bool:
        """Check if a layer is enabled."""
        return self.config.min_layer <= layer <= self.config.max_layer

    def _can_recurse(self) -> bool:
        """Check if we can recurse deeper."""
        return self.depth < self.config.max_depth

    # ========== Layer 0: Literals ==========

    def gen_bare_word(self) -> str:
        """Generate a bare word (no quotes, no expansions)."""
        return self._choice(self.WORDS)

    def gen_single_quoted(self) -> str:
        """Generate a single-quoted string."""
        content = self._choice(self.WORDS)
        if self.rng.random() < 0.3:
            content += " " + self._choice(self.WORDS)
        return f"'{content}'"

    def gen_double_quoted_literal(self) -> str:
        """Generate a double-quoted string without expansions."""
        content = self._choice(self.WORDS)
        if self.rng.random() < 0.3:
            content += " " + self._choice(self.WORDS)
        return f'"{content}"'

    def gen_literal(self) -> str:
        """Generate a literal word (layer 0)."""
        choice = self.rng.random()
        if choice < 0.5:
            return self.gen_bare_word()
        elif choice < 0.8:
            return self.gen_double_quoted_literal()
        else:
            return self.gen_single_quoted()

    # ========== Layer 1: Simple Expansions ==========

    def gen_simple_var(self) -> str:
        """Generate a simple variable reference."""
        var = self._choice(self.VARIABLES)
        if self._prob("expansion_braced"):
            return f"${{{var}}}"
        return f"${var}"

    def gen_special_param(self) -> str:
        """Generate a special parameter ($@, $*, $#, etc)."""
        param = self._choice(self.SPECIAL_PARAMS)
        if len(param) == 1 and param.isdigit():
            return f"${param}"
        return f"${{{param}}}"

    def gen_simple_expansion(self) -> str:
        """Generate a simple expansion (layer 1)."""
        if self.rng.random() < 0.8:
            return self.gen_simple_var()
        return self.gen_special_param()

    # ========== Layer 2: Complex Expansions ==========

    def gen_default_expansion(self) -> str:
        """Generate ${var:-default} style expansion."""
        var = self._choice(self.VARIABLES)
        op = self._choice([":-", ":=", ":+", "-", "=", "+"])
        default = self.gen_literal() if self.rng.random() < 0.7 else self.gen_simple_var()
        return f"${{{var}{op}{default}}}"

    def gen_substring_expansion(self) -> str:
        """Generate ${var:offset:length} expansion."""
        var = self._choice(self.VARIABLES)
        offset = self.rng.randint(0, 10)
        if self.rng.random() < 0.5:
            length = self.rng.randint(1, 10)
            return f"${{{var}:{offset}:{length}}}"
        return f"${{{var}:{offset}}}"

    def gen_pattern_expansion(self) -> str:
        """Generate ${var#pattern} style expansion."""
        var = self._choice(self.VARIABLES)
        op = self._choice(["#", "##", "%", "%%"])
        pattern = self._choice(self.PATTERNS)
        return f"${{{var}{op}{pattern}}}"

    def gen_replacement_expansion(self) -> str:
        """Generate ${var/pat/rep} expansion."""
        var = self._choice(self.VARIABLES)
        op = self._choice(["/", "//", "/#", "/%"])
        pattern = self._choice(["old", "test", "*", "?"])
        replacement = self._choice(["new", "replaced", ""])
        return f"${{{var}{op}{pattern}/{replacement}}}"

    def gen_length_expansion(self) -> str:
        """Generate ${#var} expansion."""
        var = self._choice(self.VARIABLES)
        return f"${{#{var}}}"

    def gen_transform_expansion(self) -> str:
        """Generate ${var@op} expansion."""
        var = self._choice(self.VARIABLES)
        op = self._choice(["U", "u", "L", "Q", "E", "P", "A", "K", "a"])
        return f"${{{var}@{op}}}"

    def gen_array_expansion(self) -> str:
        """Generate ${arr[idx]} or ${arr[@]} expansion."""
        var = self._choice(self.VARIABLES)
        if self.rng.random() < 0.5:
            return f"${{{var}[@]}}"
        elif self.rng.random() < 0.5:
            return f"${{{var}[*]}}"
        else:
            idx = self.rng.randint(0, 5)
            return f"${{{var}[{idx}]}}"

    def gen_complex_expansion(self) -> str:
        """Generate a complex expansion (layer 2)."""
        choice = self.rng.random()
        if choice < 0.25:
            return self.gen_default_expansion()
        elif choice < 0.4:
            return self.gen_pattern_expansion()
        elif choice < 0.55:
            return self.gen_replacement_expansion()
        elif choice < 0.7:
            return self.gen_substring_expansion()
        elif choice < 0.8:
            return self.gen_length_expansion()
        elif choice < 0.9:
            return self.gen_transform_expansion()
        else:
            return self.gen_array_expansion()

    # ========== Layer 3: Command Substitution ==========

    def gen_cmd_sub(self) -> str:
        """Generate $(cmd) or `cmd` command substitution."""
        if not self._can_recurse():
            return self.gen_simple_expansion()
        self.depth += 1
        try:
            # Generate a simple command inside
            inner = self.gen_simple_command_inner()
            if self.rng.random() < 0.8:
                return f"$({inner})"
            else:
                return f"`{inner}`"
        finally:
            self.depth -= 1

    # ========== Layer 4: Arithmetic ==========

    def gen_arith_expr(self) -> str:
        """Generate an arithmetic expression."""
        var = self._choice(self.VARIABLES)
        num = self.rng.randint(0, 100)
        ops = ["+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"]
        op = self._choice(ops)
        if self.rng.random() < 0.5:
            return f"{var} {op} {num}"
        else:
            var2 = self._choice(self.VARIABLES)
            return f"{var} {op} {var2}"

    def gen_arith_expansion(self) -> str:
        """Generate $((expr)) arithmetic expansion."""
        return f"$(({self.gen_arith_expr()}))"

    def gen_arith_command(self) -> str:
        """Generate ((expr)) arithmetic command."""
        return f"(({self.gen_arith_expr()}))"

    # ========== Word Generation (combines layers 0-4) ==========

    def gen_word(self) -> str:
        """Generate a word according to enabled layers."""
        # Determine what kind of word to generate based on layers
        if not self._layer_enabled(1):
            return self.gen_literal()

        if self._prob("word_quoted"):
            # Quoted word
            if self._prob("word_double_quoted"):
                # Double quoted - can contain expansions
                if self._layer_enabled(1) and self._prob("word_has_expansion"):
                    exp = self._gen_expansion_for_layer()
                    prefix = self._choice(self.WORDS) + " " if self.rng.random() < 0.3 else ""
                    suffix = " " + self._choice(self.WORDS) if self.rng.random() < 0.3 else ""
                    return f'"{prefix}{exp}{suffix}"'
                return self.gen_double_quoted_literal()
            else:
                return self.gen_single_quoted()
        else:
            # Unquoted word - might have expansion
            if self._layer_enabled(1) and self._prob("word_has_expansion"):
                return self._gen_expansion_for_layer()
            return self.gen_bare_word()

    def _gen_expansion_for_layer(self) -> str:
        """Generate an expansion appropriate for current layer config."""
        choices = []
        if self._layer_enabled(1):
            choices.append(self.gen_simple_expansion)
        if self._layer_enabled(2):
            choices.append(self.gen_complex_expansion)
        if self._layer_enabled(3) and self._can_recurse():
            choices.append(self.gen_cmd_sub)
        if self._layer_enabled(4):
            choices.append(self.gen_arith_expansion)
        if not choices:
            return self.gen_literal()
        return self._choice(choices)()

    # ========== Layer 5: Simple Commands ==========

    def gen_simple_command_inner(self) -> str:
        """Generate a simple command without redirections (for nesting)."""
        cmd = self._choice(self.COMMANDS)
        parts = [cmd]
        if self._prob("cmd_has_args"):
            parts.append(self.gen_word())
            while self._prob("cmd_extra_arg"):
                parts.append(self.gen_word())
        return " ".join(parts)

    def gen_assignment(self) -> str:
        """Generate a variable assignment."""
        var = self._choice(self.VARIABLES)
        value = self.gen_word()
        return f"{var}={value}"

    def gen_simple_command(self) -> str:
        """Generate a simple command (layer 5)."""
        parts = []
        # Optional leading assignment
        if self._layer_enabled(5) and self._prob("cmd_has_assignment"):
            parts.append(self.gen_assignment())
        # Command and args
        parts.append(self.gen_simple_command_inner())
        # Optional redirections
        if self._layer_enabled(6) and self._prob("cmd_has_redirect"):
            parts.append(self.gen_redirection())
        return " ".join(parts)

    # ========== Layer 6: Redirections ==========

    def gen_redirection(self) -> str:
        """Generate a redirection."""
        choice = self.rng.random()
        target = self.gen_word() if self.rng.random() < 0.8 else self._choice(["&1", "&2"])

        if choice < 0.3:
            return f"> {target}"
        elif choice < 0.5:
            return f">> {target}"
        elif choice < 0.65:
            return f"< {target}"
        elif choice < 0.75:
            return "2>&1"
        elif choice < 0.85:
            return f"2> {target}"
        elif choice < 0.92:
            return self.gen_herestring()
        else:
            return self.gen_process_sub()

    def gen_herestring(self) -> str:
        """Generate a here-string <<<."""
        word = self.gen_word()
        return f"<<< {word}"

    def gen_heredoc(self) -> str:
        """Generate a heredoc redirect (body emitted later)."""
        delim = self._choice(["EOF", "END", "DOC", "HERE"])
        quoted = self.rng.random() < 0.3
        self.heredoc_stack.append((delim, quoted))
        if quoted:
            return f"<<'{delim}'"
        return f"<<{delim}"

    def gen_heredoc_body(self, delim: str, quoted: bool) -> str:
        """Generate the body for a heredoc."""
        lines = []
        for _ in range(self.rng.randint(1, 3)):
            if quoted or self.rng.random() < 0.7:
                lines.append(self._choice(self.WORDS) + " " + self._choice(self.WORDS))
            else:
                lines.append(f"{self._choice(self.WORDS)} {self.gen_simple_expansion()}")
        return "\n".join(lines) + f"\n{delim}"

    def gen_process_sub(self) -> str:
        """Generate process substitution <() or >()."""
        if not self._can_recurse():
            return "> /dev/null"
        self.depth += 1
        try:
            inner = self.gen_simple_command_inner()
            if self.rng.random() < 0.7:
                return f"<({inner})"
            return f">({inner})"
        finally:
            self.depth -= 1

    # ========== Layer 7: Pipelines ==========

    def gen_pipeline(self) -> str:
        """Generate a pipeline."""
        parts = [self.gen_simple_command()]
        while self._layer_enabled(7) and self._prob("pipeline_continues"):
            if self.rng.random() < 0.9:
                parts.append("|")
            else:
                parts.append("|&")
            parts.append(self.gen_simple_command())
        result = " ".join(parts)
        # Optional negation or time
        if self._layer_enabled(7) and self.rng.random() < 0.1:
            result = "! " + result
        elif self._layer_enabled(7) and self.rng.random() < 0.05:
            result = "time " + result
        return result

    # ========== Layer 8: Lists ==========

    def gen_list(self) -> str:
        """Generate a list with && || ; &."""
        parts = [self.gen_pipeline()]
        while self._layer_enabled(8) and self._prob("list_continues"):
            if self._prob("list_and"):
                parts.append("&&")
            elif self.rng.random() < 0.5:
                parts.append("||")
            else:
                parts.append(";")
            parts.append(self.gen_pipeline())
        result = " ".join(parts)
        # Optional trailing &
        if self._layer_enabled(8) and self._prob("list_background"):
            result += " &"
        return result

    # ========== Layer 9: Basic Compound Commands ==========

    def gen_group(self) -> str:
        """Generate a brace group { cmd; }."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            inner = self.gen_list()
            return f"{{ {inner}; }}"
        finally:
            self.depth -= 1

    def gen_subshell(self) -> str:
        """Generate a subshell ( cmd )."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            inner = self.gen_list()
            return f"( {inner} )"
        finally:
            self.depth -= 1

    def gen_if(self) -> str:
        """Generate an if statement."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            cond = self.gen_pipeline()
            then_body = self.gen_list()
            result = f"if {cond}; then {then_body}"
            if self._prob("if_has_elif"):
                elif_cond = self.gen_pipeline()
                elif_body = self.gen_list()
                result += f"; elif {elif_cond}; then {elif_body}"
            if self._prob("if_has_else"):
                else_body = self.gen_list()
                result += f"; else {else_body}"
            result += "; fi"
            return result
        finally:
            self.depth -= 1

    # ========== Layer 10: Loops ==========

    def gen_for(self) -> str:
        """Generate a for loop."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            var = self._choice(self.VARIABLES)
            words = " ".join(self.gen_word() for _ in range(self.rng.randint(1, 4)))
            body = self.gen_list()
            return f"for {var} in {words}; do {body}; done"
        finally:
            self.depth -= 1

    def gen_arith_for(self) -> str:
        """Generate a C-style for loop."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            var = self._choice(["i", "j", "k", "n"])
            limit = self.rng.randint(1, 10)
            body = self.gen_list()
            return f"for (({var}=0; {var}<{limit}; {var}++)); do {body}; done"
        finally:
            self.depth -= 1

    def gen_while(self) -> str:
        """Generate a while loop."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            cond = self.gen_pipeline()
            body = self.gen_list()
            return f"while {cond}; do {body}; done"
        finally:
            self.depth -= 1

    def gen_until(self) -> str:
        """Generate an until loop."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            cond = self.gen_pipeline()
            body = self.gen_list()
            return f"until {cond}; do {body}; done"
        finally:
            self.depth -= 1

    def gen_select(self) -> str:
        """Generate a select statement."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            var = self._choice(self.VARIABLES)
            words = " ".join(self.gen_word() for _ in range(self.rng.randint(2, 4)))
            body = self.gen_list()
            return f"select {var} in {words}; do {body}; done"
        finally:
            self.depth -= 1

    # ========== Layer 11: Case and Conditionals ==========

    def gen_case(self) -> str:
        """Generate a case statement."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            word = self.gen_word()
            patterns = []
            for _ in range(self.rng.randint(1, 3)):
                pat = self._choice(self.PATTERNS + self.WORDS)
                if self._prob("case_extra_pattern"):
                    pat += "|" + self._choice(self.PATTERNS + self.WORDS)
                body = self.gen_list()
                term = self._choice([";;", ";&", ";;&"])
                patterns.append(f"{pat}) {body}{term}")
            return f"case {word} in {' '.join(patterns)} esac"
        finally:
            self.depth -= 1

    def gen_cond(self) -> str:
        """Generate a [[ ]] conditional expression."""
        word1 = self.gen_word()
        word2 = self.gen_word()
        op = self._choice(
            ["==", "!=", "=~", "<", ">", "-eq", "-ne", "-lt", "-gt", "-f", "-d", "-z", "-n"]
        )
        if op in ["-f", "-d", "-z", "-n"]:
            return f"[[ {op} {word1} ]]"
        return f"[[ {word1} {op} {word2} ]]"

    # ========== Layer 12: Functions and Coproc ==========

    def gen_function(self) -> str:
        """Generate a function definition."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            name = self._choice(["func", "helper", "do_thing", "process", "myfn"])
            body = self.gen_list()
            if self.rng.random() < 0.5:
                return f"{name}() {{ {body}; }}"
            return f"function {name} {{ {body}; }}"
        finally:
            self.depth -= 1

    def gen_coproc(self) -> str:
        """Generate a coproc."""
        if not self._can_recurse():
            return self.gen_simple_command()
        self.depth += 1
        try:
            name = self._choice(["COPROC", "worker", "bg"])
            body = self.gen_simple_command()
            if self.rng.random() < 0.5:
                return f"coproc {name} {{ {body}; }}"
            return f"coproc {body}"
        finally:
            self.depth -= 1

    # ========== Top-level Generation ==========

    def gen_command(self) -> str:
        """Generate a command according to enabled layers."""
        if self._layer_enabled(12) and self.rng.random() < 0.05:
            return self.gen_function()
        if self._layer_enabled(12) and self.rng.random() < 0.02:
            return self.gen_coproc()
        if self._layer_enabled(11) and self.rng.random() < 0.1:
            return self._choice([self.gen_case, self.gen_cond])()
        if self._layer_enabled(10) and self.rng.random() < 0.15:
            return self._choice(
                [self.gen_for, self.gen_arith_for, self.gen_while, self.gen_until, self.gen_select]
            )()
        if self._layer_enabled(9) and self.rng.random() < 0.15:
            return self._choice([self.gen_group, self.gen_subshell, self.gen_if])()
        if self._layer_enabled(8):
            return self.gen_list()
        if self._layer_enabled(7):
            return self.gen_pipeline()
        if self._layer_enabled(5):
            return self.gen_simple_command()
        if self._layer_enabled(4) and self.rng.random() < 0.3:
            return self.gen_arith_command()
        return self.gen_word()

    def generate(self) -> str:
        """Generate a complete bash script."""
        self.depth = 0
        self.heredoc_stack = []
        result = self.gen_command()
        # Emit any pending heredoc bodies
        for delim, quoted in self.heredoc_stack:
            result += "\n" + self.gen_heredoc_body(delim, quoted)
        return result


def parse_layer_arg(arg: str) -> tuple[int, int]:
    """Parse layer argument like '5', '0-3', 'words', 'commands'."""
    if arg in LAYER_PRESETS:
        max_layer = LAYER_PRESETS[arg]
        return (0, max_layer)
    if "-" in arg:
        parts = arg.split("-")
        return (int(parts[0]), int(parts[1]))
    return (0, int(arg))


def check_discrepancy(generated: str) -> Discrepancy | None:
    """Check if Parable and oracle disagree on generated input."""
    parable = run_parable(generated)
    oracle = run_oracle(generated)
    if parable is None and oracle is None:
        return None
    if (parable is None) != (oracle is None):
        return Discrepancy(
            original="<generated>",
            mutated=generated,
            mutation_desc="generator",
            parable_result=parable if parable else "<error>",
            oracle_result=oracle if oracle else "<error>",
        )
    if normalize(parable) != normalize(oracle):
        return Discrepancy(
            original="<generated>",
            mutated=generated,
            mutation_desc="generator",
            parable_result=parable,
            oracle_result=oracle,
        )
    return None


def main():
    parser = argparse.ArgumentParser(description="Grammar-based generator fuzzer")
    parser.add_argument("-n", "--iterations", type=int, default=1000)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-s", "--seed", type=int)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--both-succeed", action="store_true")
    parser.add_argument("--stop-after", type=int)
    parser.add_argument(
        "--layer",
        type=str,
        default="full",
        help="Layer spec: 0-12, range like 0-5, or preset (words, expansions, commands, pipes, control, full)",
    )
    parser.add_argument("--max-depth", type=int, default=5, help="Maximum recursion depth")
    parser.add_argument("--list-layers", action="store_true", help="List available layers and exit")
    parser.add_argument(
        "--dry-run", type=int, metavar="N", help="Generate N samples and print them without testing"
    )
    parser.add_argument(
        "--minimize", action="store_true", help="Minimize discrepancies before outputting"
    )
    parser.add_argument(
        "--filter-layer", help="Only show discrepancies at or below this layer (implies --minimize)"
    )
    args = parser.parse_args()

    if args.list_layers:
        print("Layers:")
        for num, name in sorted(LAYERS.items()):
            print(f"  {num:2d}: {name}")
        print("\nPresets:")
        for name, layer in sorted(LAYER_PRESETS.items(), key=lambda x: x[1]):
            print(f"  {name}: 0-{layer}")
        sys.exit(0)

    min_layer, max_layer = parse_layer_arg(args.layer)
    config = GeneratorConfig(
        min_layer=min_layer,
        max_layer=max_layer,
        max_depth=args.max_depth,
        seed=args.seed,
    )
    gen = Generator(config)

    if args.dry_run:
        out = open(args.output, "w") if args.output else sys.stdout
        for i in range(args.dry_run):
            out.write(f"--- {i + 1} ---\n")
            out.write(gen.generate())
            out.write("\n\n")
        if args.output:
            out.close()
            print(f"Wrote {args.dry_run} samples to {args.output}")
        sys.exit(0)

    if not ORACLE_PATH.exists():
        print(f"Error: bash-oracle not found at {ORACLE_PATH}", file=sys.stderr)
        sys.exit(1)

    discrepancies: list[Discrepancy] = []
    seen_signatures: set[str] = set()

    print(f"Generator fuzzer: layers {min_layer}-{max_layer}, max_depth={args.max_depth}")

    for i in range(args.iterations):
        generated = gen.generate()
        d = check_discrepancy(generated)
        if d:
            if args.both_succeed and (
                d.parable_result == "<error>" or d.oracle_result == "<error>"
            ):
                continue
            sig = d.signature()
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            discrepancies.append(d)
            if args.verbose:
                print(f"\n[{i + 1}] DISCREPANCY")
                print(f"  Generated: {d.mutated!r}")
                print(f"  Parable:   {d.parable_result}")
                print(f"  Oracle:    {d.oracle_result}")
            if args.stop_after and len(discrepancies) >= args.stop_after:
                break
        if (i + 1) % 100 == 0:
            print(
                f"\r{i + 1}/{args.iterations}, {len(discrepancies)} discrepancies",
                end="",
                flush=True,
            )

    print()
    print(f"Found {len(discrepancies)} unique discrepancies in {args.iterations} iterations")

    filter_layer = parse_layer_spec(args.filter_layer) if args.filter_layer else None
    discrepancies = post_process_discrepancies(discrepancies, args.minimize, filter_layer)

    if args.output and discrepancies:
        with open(args.output, "w") as f:
            for d in discrepancies:
                f.write(f"=== {d.mutation_desc} ===\n")
                f.write(d.mutated)
                if not d.mutated.endswith("\n"):
                    f.write("\n")
                f.write("---\n")
                f.write(f"parable: {d.parable_result}\n")
                f.write(f"oracle:  {d.oracle_result}\n")
                f.write("---\n\n")
        print(f"Wrote {len(discrepancies)} discrepancies to {args.output}")

    sys.exit(1 if discrepancies else 0)


if __name__ == "__main__":
    main()
