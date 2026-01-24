<div align="center">
<pre>
((((        ))))                              The wind blows where it will--
 ((((              ))))                          you hear its sound, but you
         ((((  <strong>P A R A B L E</strong>  ))))                don't know where it's from
   ))))         ((((                                    or where it's going.
))))        ((((                                                  — John 3:8
</pre>
</div>

Parse bash exactly as bash does. Python or Javascript, your choice. One file, zero dependencies. This is the only complete bash parser for Python or JS. Extensively validated against bash itself.

---

## Philosophy

**LLM-driven development.** This project is an exercise in maximizing what LLMs can do. An 11,000-line recursive descent parser for one of the gnarliest grammars in computing, built and maintained almost entirely through AI assistance—it wouldn't exist without them. When performance and clarity conflict, clarity wins. Verbose beats clever. The code should be readable by both humans and models.

**Match bash exactly.** Bash is the oracle. We [patched](https://github.com/ldayton/bash-oracle) GNU Bash 5.3 so it reveals its internal parse tree, then test against it. No spec interpretation, no "close enough"—if bash parses it one way, so do we. Bash always tells the truth, even when it's lying.

**Portable performance.** Hand-written recursive descent—no generators, no native extensions. Pure Python and pure JS, zero dependencies, not even stdlib imports. The Python implementation is canonical; a custom transpiler produces idiomatic Javascript. Both run the same tests.

## Javascript + Typescript

The Python implementation uses idiomatic Python that transpiles naturally to idiomatic Javascript: f-strings become template literals, ternaries stay ternaries, lambdas become arrow functions. A custom transpiler produces perfectly readable JS: not minified, not obfuscated, not transmogrified, but clean code that looks like a human wrote it.

The Javascript output is then validated the same way as Python. Same tests, same bash AST comparisons, same edge cases. If Python parses it correctly, so does JS. Typescript definitions are auto-generated from the transpiled JS.

## Why Parable?

Bash's grammar is notoriously irregular. Existing tools make tradeoffs:

- **bashlex** — Incomplete. Fails on [heredocs](https://github.com/idank/bashlex/issues/99), [arrays](https://github.com/idank/bashlex/issues/84), [arithmetic](https://github.com/idank/bashlex/issues/68), and [more](https://github.com/idank/bashlex/issues). Fine for simple scripts, breaks on real ones.
- **Oils/OSH** — A whole shell, not an embeddable library. Makes [intentional parsing tradeoffs](https://github.com/oils-for-unix/oils/blob/master/doc/known-differences.md) for a cleaner language—fine for their goals, but won't predict what real bash does.
- **tree-sitter-bash** — Editor-focused, not Python-native. [Many open parsing bugs](https://github.com/tree-sitter/tree-sitter-bash/issues).
- **sh-syntax** — WASM port of mvdan/sh, not pure JS. [Doesn't fully match bash](https://github.com/mvdan/sh#caveats).

Parable is the only Python & JS library that parses bash exactly as bash does—tested against bash's own AST. For security and sandboxing, 95% coverage is 100% inadequate.

**Use cases:**
- **Security auditing** — Analyze scripts for command injection, dangerous patterns, or policy violations. The construct you can't parse is the one that owns you.
- **CI/CD analysis** — Understand what shell scripts actually do before running them.
- **Migration tooling** — Convert bash to other languages with full AST access.
- **Linting and formatting** — Build bash linters in Python & JS without regex hacks.

## What It Handles 😱

The dark corners of bash that break other parsers:

```bash
# Nested everything
echo $(cat <(grep ${pattern:-".*"} "${files[@]}"))

# Heredoc inside command substitution inside heredoc
cat <<OUTER
$(cat <<INNER
$nested
INNER
)
OUTER

# Multiple heredocs on one line
diff <(cat <<A
one
A
) <(cat <<B
two
B
)

# Quoting transforms on array slices
printf '%q\n' "${arr[@]:2:5@Q}"

# Regex with expansions in conditional
[[ ${foo:-$(whoami)} =~ ^(user|${pattern})$ ]]

# Process substitution as redirect target
cmd > >(tee log.txt) 2> >(tee err.txt >&2)

# Extglob patterns that look like syntax
case $x in @(foo|bar|?(baz))) echo match;; esac
```

The full grammar—parameter expansion, heredocs, process substitution, arithmetic, arrays, conditionals, coprocesses, all of it.

## Security

Parable is designed for tools that need to predict what bash will do. Honest caveats:

- **Tested, not mathematically proven.** We validate against bash's AST for thousands of difficult edge cases, but this is not a formal proof, verified by a proof checker. A determined attacker with capable LLMs may find discrepancies.
- **Validated against bash 5.3.** Core parsing is stable across versions, but edge cases may differ. If your target runs ancient bash (macOS ships 3.2) or relies on version-specific quirks, verify independently.
- **Bash wasn't built for this.** Even perfect parsing doesn't guarantee predictable execution. `shopt` settings, aliases, and runtime context all affect behavior. True security means containers or VMs.

Parable strives to be the best available tool for static bash analysis—oracle-tested, not spec-interpreted. But for high-stakes security, nothing replaces defense in depth.

## Test Coverage

Every test validated against real bash 5.3 ASTs.

- **GNU Bash test corpus:** 19,370 lines
- **Oils bash corpus:** 2,495 tests
- **tree-sitter-bash corpus:** 125 tests
- **Parable hand-written tests:** 1,800+ tests

## Usage

### Python

```python
from parable import parse

# Returns an AST, not string manipulation
ast = parse("ps aux | grep python | awk '{print $2}'")

# S-expression output for inspection
print(ast[0].to_sexp())
# (pipe (command (word "ps") (word "aux")) (pipe (command (word "grep") (word "python")) (command (word "awk") (word "'{print $2}'"))))

# Handles the weird stuff
ast = parse("cat <<'EOF'\nheredoc content\nEOF")
print(ast[0].to_sexp())
# (command (word "cat") (redirect "<<" "heredoc content\n"))
```

### Javascript

```javascript
import { parse } from './src/parable.js';

const ast = parse("ps aux | grep python | awk '{print $2}'");
console.log(ast[0].toSexp());
```

## Installation

```bash
git clone https://github.com/ldayton/Parable.git
cd Parable && uv pip install -e .
```

## Tests

```bash
just test      # Python
just test-js   # Javascript
```

See [tests/README.md](tests/README.md) for options and coverage details.

## Project Structure

```
src/
├── parable.py                   # Single-file Python parser
├── parable.js                   # Transpiled Javascript parser
└── parable.d.ts                 # Typescript definitions

tests/
├── bin/                         # Test runners
├── parable/                     # Parable test cases
└── corpus/                      # Validation corpus

tools/
├── bash-oracle/                 # Patched bash + corpus utilities
├── fuzzer/                      # Differential fuzzers
└── transpiler/                  # Python-to-JS transpiler
```

## License

MIT