# Generator Proposal: Layered Bash Generation

A grammar-guided generator with configurable complexity layers, designed for incremental testing.

---

## Design Goals

1. **Layered complexity** — Start with simple words, progressively enable more constructs
2. **Probability tables** — Csmith-style tunable weights for each production choice
3. **Depth limits** — Prevent runaway recursion; target optimal ~8-16K token range
4. **Differential testing** — Compare Parable vs bash-oracle at each layer
5. **Reproducibility** — Seed-based generation for debugging

---

## Layers (Derived from bash-parse.y)

Each layer enables all constructs from previous layers plus new ones.

### Layer 0: Literals
The foundation. No expansions, no special syntax.
```bash
hello                   # bare word
"hello world"           # double-quoted string
'literal $string'       # single-quoted string
$'escape\nsequence'     # ANSI-C quoting
123                     # numbers
```

**Grammar rules**: `WORD` (literal only)

### Layer 1: Simple Expansions
Variable references without nesting.
```bash
$var                    # simple variable
${var}                  # braced variable
$1 $@ $* $# $? $$       # special parameters
${#var}                 # string length
```

**Grammar rules**: `WORD` with parameter expansion

### Layer 2: Complex Expansions
Nested and transformed expansions.
```bash
${var:-default}         # default value
${var:=value}           # assign default
${var:+alternate}       # alternate value
${var:?error}           # error if unset
${var:offset:length}    # substring
${var#pattern}          # prefix removal
${var%pattern}          # suffix removal
${var/pat/rep}          # substitution
${var@Q}                # transformations
${arr[0]} ${arr[@]}     # array indexing
```

**Grammar rules**: `WORD` with full parameter expansion operators

### Layer 3: Command Substitution
```bash
$(cmd)                  # modern form
`cmd`                   # legacy form (backticks)
$(cat <<EOF             # heredoc inside command sub
nested
EOF
)
```

**Grammar rules**: `WORD` with command substitution (recursive!)

### Layer 4: Arithmetic
```bash
$((1 + 2))              # arithmetic expansion
$((x++))                # with side effects
((expr))                # arithmetic command
```

**Grammar rules**: `ARITH_CMD`, `ARITH_FOR_EXPRS`, arithmetic expansion in `WORD`

### Layer 5: Simple Commands
Commands with arguments and assignments.
```bash
cmd arg1 arg2           # basic command
VAR=value cmd           # prefix assignment
cmd arg1 arg2 arg3      # multiple arguments
```

**Grammar rules**: `simple_command`, `simple_command_element`

### Layer 6: Redirections
```bash
cmd > file              # output
cmd < file              # input
cmd >> file             # append
cmd 2>&1                # fd duplication
cmd <<EOF               # heredoc
body
EOF
cmd <<< "string"        # herestring
cmd <(other)            # process substitution (input)
cmd >(other)            # process substitution (output)
```

**Grammar rules**: `redirection` (32 production rules!)

### Layer 7: Pipelines
```bash
cmd1 | cmd2             # pipe
cmd1 |& cmd2            # pipe stderr too
! cmd                   # negation
time cmd                # time prefix
```

**Grammar rules**: `pipeline`, `timespec`

### Layer 8: Lists
```bash
cmd1 && cmd2            # AND list
cmd1 || cmd2            # OR list
cmd1 ; cmd2             # sequential
cmd1 & cmd2             # background first
cmd1 && cmd2 || cmd3    # chained
```

**Grammar rules**: `list0`, `list1`, `simple_list`, `simple_list1`

### Layer 9: Compound Commands (Basic)
```bash
{ cmd; }                # group
( cmd )                 # subshell
if cond; then cmd; fi   # if
if c; then x; else y; fi
```

**Grammar rules**: `shell_command` (partial), `group_command`, `subshell`, `if_command`

### Layer 10: Compound Commands (Loops)
```bash
for x in a b c; do cmd; done
for ((i=0; i<10; i++)); do cmd; done
while cond; do cmd; done
until cond; do cmd; done
select x in a b c; do cmd; done
```

**Grammar rules**: `for_command`, `arith_for_command`, `select_command`

### Layer 11: Case and Conditionals
```bash
case $x in              # case
  pat1) cmd1;;
  pat2|pat3) cmd2;;
esac
[[ $x == y ]]           # conditional expression
[[ $x =~ regex ]]       # regex match
```

**Grammar rules**: `case_command`, `pattern_list`, `COND_CMD`

### Layer 12: Functions and Coproc
```bash
f() { cmd; }            # function definition
function f { cmd; }     # alternative syntax
coproc name { cmd; }    # coprocess
```

**Grammar rules**: `function_def`, `COPROC`

---

## CLI Interface

```bash
# Basic usage - generate at specific layer
uv run fuzzer --generator --layer 5        # up to simple commands
uv run fuzzer --generator --layer 0-3      # range: literals through command sub

# Named layer presets
uv run fuzzer --generator --layer words    # alias for layer 2
uv run fuzzer --generator --layer commands # alias for layer 5
uv run fuzzer --generator --layer control  # alias for layer 10

# Probability tuning
uv run fuzzer --generator --bias-depth 0.3 # favor deeper nesting (default 0.5)
uv run fuzzer --generator --bias-quotes 0.7 # more quoted strings

# Size control
uv run fuzzer --generator --max-depth 10   # recursion limit
uv run fuzzer --generator --target-tokens 1000  # approximate output size

# Standard fuzzer options (already exist)
uv run fuzzer --generator -n 5000 -v --stop-after 10
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Generator                            │
├─────────────────────────────────────────────────────────────┤
│  Layer Config                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ enabled_layers: set[int]                                ││
│  │ max_depth: int                                          ││
│  │ probabilities: dict[str, float]  # Csmith-style weights ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│  Production Rules (one method per grammar rule)              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ gen_word() -> str                                       ││
│  │ gen_simple_command() -> str                             ││
│  │ gen_pipeline() -> str                                   ││
│  │ gen_list() -> str                                       ││
│  │ gen_compound() -> str                                   ││
│  │ ...                                                     ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│  State Tracking (safety mechanisms)                          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ depth: int          # current recursion depth           ││
│  │ quote_state: str    # none, single, double, ansi        ││
│  │ heredoc_stack: list # pending heredocs                  ││
│  │ in_arith: bool      # inside $(()) or (())              ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Foundation
- [ ] Create `Generator` class with layer configuration
- [ ] Implement `gen_word()` for layers 0-2 (literals, simple expansions, complex expansions)
- [ ] Add depth tracking and recursion limits
- [ ] Wire into existing `generator.py` CLI

### Phase 2: Commands
- [ ] Implement `gen_simple_command()` (layer 5)
- [ ] Implement `gen_redirection()` (layer 6)
- [ ] Implement `gen_pipeline()` (layer 7)
- [ ] Implement `gen_list()` (layer 8)

### Phase 3: Compound Commands
- [ ] Implement `gen_group()`, `gen_subshell()` (layer 9)
- [ ] Implement `gen_if()` (layer 9)
- [ ] Implement `gen_for()`, `gen_while()`, `gen_until()`, `gen_select()` (layer 10)
- [ ] Implement `gen_case()`, `gen_cond()` (layer 11)

### Phase 4: Advanced
- [ ] Implement `gen_function()`, `gen_coproc()` (layer 12)
- [ ] Add command substitution recursion (layer 3)
- [ ] Add arithmetic (layer 4)
- [ ] Heredoc generation with proper body handling

### Phase 5: Polish
- [ ] Probability table tuning
- [ ] Named layer presets
- [ ] Coverage-guided feedback (optional, GRIMOIRE-style)

---

## Key Design Decisions

### 1. Layer granularity
Layers are designed around conceptual boundaries, not grammar rules directly. Layer 2 (complex expansions) groups many grammar productions that all relate to parameter expansion.

### 2. Recursion handling
Command substitution (`$(...)`) creates recursion: a word can contain a command, which contains words. Depth limits prevent infinite recursion. When depth exceeded, fall back to simpler constructs.

### 3. Heredoc deferred generation
Heredocs require body text after the command. Generator tracks pending heredocs and emits bodies at statement boundaries:
```python
# During generation
self.heredoc_stack.append(("EOF", "quoted"))
# After statement complete
for delim, _ in self.heredoc_stack:
    output += f"\n{gen_heredoc_body()}\n{delim}"
```

### 4. Quote state tracking
What characters are special depends on quote context. Generator tracks state:
- Unquoted: all expansions active
- Double-quoted: `$`, `` ` ``, `\` are special
- Single-quoted: nothing special
- ANSI-C quoted: escape sequences

### 5. Probability weights (Csmith-inspired)
Every choice point has a configurable probability:
```python
PROBS = {
    "word_quoted": 0.3,        # chance word is quoted
    "word_has_expansion": 0.4, # chance word contains $...
    "cmd_has_redirect": 0.2,   # chance command has redirections
    "list_continues": 0.3,     # chance list adds another && or ||
    ...
}
```

---

## Testing Strategy

1. **Layer isolation** — Run each layer independently, verify no constructs from higher layers appear
2. **Oracle comparison** — Every generated script compared against bash-oracle
3. **Corpus integration** — Generated scripts can seed the structural fuzzer
4. **Coverage tracking** — Optional: track which grammar rules exercised

---

## Example Generated Output by Layer

**Layer 0:**
```bash
hello
"world"
'literal'
```

**Layer 3:**
```bash
$(echo ${var:-default})
`pwd`
```

**Layer 7:**
```bash
echo ${name} | grep "pattern" | wc -l
```

**Layer 10:**
```bash
for f in "${files[@]}"; do
  if [[ -f "$f" ]]; then
    cat "$f" | grep "${pattern:-.*}" >> output
  fi
done
```

---

## Files to Create/Modify

```
tools/fuzzer/src/fuzzer/
├── generator.py          # Modify: integrate Generator class
├── generate/             # New: generator module
│   ├── __init__.py
│   ├── generator.py      # Generator class
│   ├── layers.py         # Layer definitions
│   ├── words.py          # Word generation (layers 0-4)
│   ├── commands.py       # Command generation (layers 5-8)
│   ├── compound.py       # Compound commands (layers 9-12)
│   └── probabilities.py  # Probability tables
```

Or simpler single-file approach:
```
tools/fuzzer/src/fuzzer/
├── generator.py          # Modify: expand with Generator class inline
```

Recommend single file until complexity warrants splitting.
