<div align="center">
<pre>
((((        ))))                              The wind blows where it will--
 ((((              ))))                          you hear its sound, but you
         ((((  <strong>P A R A B L E</strong>  ))))                don't know where it's from
   ))))         ((((                                    or where it's going.
))))        ((((                                                  — John 3:8
</pre>
</div>

Parse bash exactly as bash does. One file, zero dependencies, in your language. This is the only complete bash parser for most languages. Extensively validated against bash itself.

---

## Philosophy

**LLM-driven development.** This project is an exercise in maximizing what LLMs can do. An 11,000-line recursive descent parser for one of the gnarliest grammars in computing, plus a custom multi-target transpiler, built and maintained almost entirely through AI assistance—it wouldn't exist without them.

**Match bash exactly.** Bash is the oracle. We [patched](https://github.com/ldayton/bash-oracle) GNU Bash 5.3 so it reveals its internal parse tree, then test against it. No spec interpretation, no "close enough"—if bash parses it one way, so do we. Bash always tells the truth, even when it's lying.

**Portable performance.** Hand-written recursive descent—no generators, no native extensions, no imports. Pure Python transpiles to other target languages. All run the same tests.

## Transpiler

The transpiler supports these target languages:

| Language   | Reference    | Released | Homebrew      | GitHub Actions    | Status |
| ---------- | ------------ | -------- | ------------- | ----------------- | ------ |
| Go         | Go 1.21      | Aug 2023 | `go@1.21`     | `setup-go@v5`     | Done   |
| Java       | Temurin 21   | Sep 2023 | `temurin@21`  | `setup-java@v4`   | Done   |
| Javascript | Node.js 21   | Oct 2023 | `node@21`     | `setup-node@v4`   | Done   |
| Lua        | Lua 5.4      | May 2023 | `lua`         | `gh-actions-lua`  | Done   |
| Python     | CPython 3.12 | Oct 2023 | `python@3.12` | `setup-uv@v4`     | Done   |
| Ruby       | Ruby 3.3     | Dec 2023 | `ruby@3.3`    | `setup-ruby@v1`   | Done   |
| Typescript | tsc 5.3      | Nov 2023 | `node@21`     | `setup-node@v4`   | Done   |
| C#         | .NET 8       | Nov 2023 | `dotnet@8`    | `setup-dotnet@v4` | WIP    |
| Perl       | Perl 5.38    | Jul 2023 | `perl`        | `setup-perl@v1`   | WIP    |
| PHP        | PHP 8.3      | Nov 2023 | `php@8.3`     | `setup-php@v2`    | WIP    |
| C          | GCC 13       | Jul 2023 | `gcc@13`      | `setup-gcc@v1`    | Future |
| Dart       | Dart 3.2     | Nov 2023 | `dart`        | `setup-dart@v1`   | Future |
| Rust       | Rust 1.75    | Dec 2023 | `rust`        | `setup-rust@v1`   | Future |
| Swift      | Swift 5.9    | Sep 2023 | `swift`       | `setup-swift@v2`  | Future |
| Zig        | Zig 0.11     | Aug 2023 | `zig`         | `setup-zig@v2`    | Future |

Output code quality is a work in progress. Currently the transpiler prioritizes correctness over readability; generated code may not yet match hand-written idioms.

## Why Parable?

Bash's grammar is notoriously irregular. Existing tools make tradeoffs:

- **bashlex** — Incomplete. Fails on [heredocs](https://github.com/idank/bashlex/issues/99), [arrays](https://github.com/idank/bashlex/issues/84), [arithmetic](https://github.com/idank/bashlex/issues/68), and [more](https://github.com/idank/bashlex/issues). Fine for simple scripts, breaks on real ones.
- **Oils/OSH** — A whole shell, not an embeddable library. Makes [intentional parsing tradeoffs](https://github.com/oils-for-unix/oils/blob/master/doc/known-differences.md) for a cleaner language—fine for their goals, but won't predict what real bash does.
- **tree-sitter-bash** — Editor-focused, not Python-native. [Many open parsing bugs](https://github.com/tree-sitter/tree-sitter-bash/issues).
- **mvdan/sh** — Go-native, but [doesn't fully match bash](https://github.com/mvdan/sh#caveats). Targets POSIX with bash extensions.
- **sh-syntax** — WASM port of mvdan/sh, not pure JS. Inherits the same limitations.

Parable is the only library in these languages that parses bash exactly as bash does—tested against bash's own AST. For security and sandboxing, 95% coverage is 100% inadequate.

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
- **Parable hand-written tests:** 1,900+ tests

## Usage

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

## Project Structure

```
src/
└── parable.py                   # Single-file Python parser

tests/
├── bin/                         # Test runners + corpus utilities
├── parable/                     # Parable test cases
└── corpus/                      # Validation corpus

tools/
└── fuzzer/                      # Differential fuzzers

transpiler/                      # Python → multi-language transpiler
├── src/frontend/                # Parser and type inference
├── src/middleend/               # Analysis passes
└── src/backend/                 # Code generators

dist/                            # Transpiled outputs
├── csharp/Parable.cs
├── go/parable.go
├── java/Parable.java
├── perl/parable.pl
├── php/parable.php
├── python/parable.py
├── ruby/parable.rb
└── ts/parable.ts
```

## License

MIT
