# Differential Parser Fuzzing: Research Summary

Research on fuzz testing approaches for finding differences between bash-oracle and Parable, with neither assumed correct a priori.

## The Problem Space

For Parable vs bash-oracle, we're doing **differential testing** where neither implementation is assumed correct a priori. The goal is to find *any* discrepancy, then investigate which (if either) is wrong. This is distinct from fuzzing against a spec.

## Mutation Levels: Effectiveness Comparison

Research consistently shows a **hierarchy of mutation levels**, each with trade-offs:

| Level | Validity Rate | Bug Types Found | Best For |
|-------|--------------|-----------------|----------|
| **Byte-level** | Very low | Shallow parser bugs, crashes | Memory safety issues |
| **Token-level** | Medium | Parser edge cases, grammar ambiguities | Middle ground |
| **AST-level** | High | Deep semantic issues, interpreter bugs | Valid-but-tricky inputs |
| **Grammar-level** | Very high | Spec compliance, edge cases | Generation from scratch |

**Key finding from [Token-Level Fuzzing (USENIX 2021)](https://www.usenix.org/conference/usenixsecurity21/presentation/salls):** Token-level found 29 bugs in JavaScript engines that *neither* byte-level nor grammar-based fuzzers could find. It hits a sweet spot—structured enough to pass lexing, flexible enough to stress parser edge cases.

**Key finding from [Grammar Mutation (TOSEM 2025)](https://dl.acm.org/doi/10.1145/3708517):** Two approaches—Gmutator (grammar mutation) and G+M (byte-level on grammar-generated inputs)—are complementary. "Both excel in generating edge case inputs, facilitating the detection of disparities between input specifications and parser implementations."

## Most Effective Approaches

### 1. Grammar-Aware Generation + Targeted Mutation

[ShellFuzzer](https://arxiv.org/html/2408.00433) is directly relevant—it's grammar-based fuzzing for shell interpreters (mksh, bash). Found 8 bugs in mksh, 7 confirmed, including 2 memory errors affecting bash 5.0.

Key insight: They use **three generators**:
- **Generator V**: Valid POSIX scripts (tests normal paths)
- **Generator I**: Deliberately invalid scripts (tests error handling)
- **Generator M_I**: Valid scripts with syntax-breaking mutations (finds edge cases)

The combination matters more than any single approach.

### 2. AST-Based Mutation for Deep Coverage

For JavaScript engines, AST-level mutation has proven most effective for finding deep bugs because it preserves syntactic validity while exploring semantic variations. However, it tends to cause semantic errors that get rejected early.

For bash specifically, AST mutation would let you:
- Swap command types (pipeline ↔ list)
- Mutate redirect targets
- Nest constructs in unusual ways
- Vary quoting contexts

### 3. LLM-Guided Semantic Mutation (2025)

[Semantic-Aware Fuzzing](https://arxiv.org/html/2509.19533) integrates LLMs with AFL++. Results are mixed—"no single reasoning LLM consistently outperforms traditional fuzzers"—but shows promise for generating semantically diverse inputs that traditional mutation misses.

Trade-off: Increasing prompt examples improved syntactic correctness but reduced diversity, ultimately limiting coverage gains.

## Recommendations for Parable

Given the setup (bash-oracle with `--dump-ast` and Parable producing comparable ASTs):

1. **Start with grammar-based generation** using bash's grammar. Generate thousands of valid scripts covering all constructs.

2. **Layer token-level mutations** on grammar-generated seeds. This finds cases where bash and Parable disagree on tokenization boundaries.

3. **Focus on ambiguous constructs**:
   - Heredoc edge cases
   - Nested expansions: `${var:-$(cmd)}`
   - Quoting interactions with special characters
   - Extglob patterns that look like syntax

4. **Compare AST structure, not just parse/no-parse**. Two parsers can both "succeed" but produce structurally different trees.

5. **Prioritize edge cases from other bash parsers' bug trackers**—bashlex, tree-sitter-bash, mvdan/sh all have open issues documenting parsing discrepancies.

## Practical Plan for Parable

### Existing Infrastructure

The differential testing infrastructure already exists:

- **bash-oracle** at `~/source/bash-oracle/bash-oracle` with `-e <input>` flag dumps S-expression AST
- **Parable** via `parse(input)[0].to_sexp()` produces matching S-expression format
- **Comparison**: whitespace-normalized string equality (see `tools/fuzzer/src/fuzzer/common.py`)
- **Corpus**: ~20k lines across `.tests` files in `tests/parable/` and `tests/corpus/`

The test format is simple:
```
=== test name
bash input here
---
(expected s-expression)
---
```

### Phase 1: Corpus Mutation (Implemented)

The character mutation fuzzer is implemented in `tools/fuzzer`:

```bash
cd tools/fuzzer
uv run fuzzer --character --both-succeed --stop-after 5 -v
```

It extracts inputs from `.tests` files, applies random character mutations, and compares Parable vs bash-oracle.

### Phase 2: Targeted Edge Case Generation

Focus on constructs known to cause parser divergence:

**Heredoc boundaries:**
```bash
cat <<EOF$(cmd)
cat <<-'EOF'
cat << \EOF
```

**Nested expansions:**
```bash
${arr[@]:${start}:$((end-start))}
${x:-${y:-${z:-default}}}
echo "${foo:-"bar"}"
```

**Quoting interactions:**
```bash
$'escape\nsequences'
$"locale strings"
"mixed $var 'quotes'"
```

**Extglob ambiguity:**
```bash
case $x in @(a|b)) ;; esac   # )) looks like arithmetic
+(x)|?(y)                     # looks like subshell
```

**Arithmetic edge cases:**
```bash
$((x+++y))    # pre-increment or post-increment + y?
$((a?b:c?d:e))
```

### Phase 2.5: Structural Fuzzing (Implemented)

The structural fuzzer wraps corpus inputs in structural contexts that character mutation can't easily generate:

```bash
cd tools/fuzzer
uv run fuzzer --structural --list-transforms
uv run fuzzer --structural --both-succeed --stop-after 5 -v
```

Transforms include wrapping in `$()`, `<()`, `{ }`, subshells, pipelines, etc.

### Phase 3: Token-Level Mutation (Harder)

Requires tokenizing bash first. Options:

1. **Use Parable as tokenizer**: Parse successfully, mutate the token stream, serialize back. But Parable has no printer—you'd need to write one.

2. **Simple lexer**: Write a minimal bash lexer that splits on metacharacters without full parsing. Mutate token boundaries. Cheaper than a full printer.

3. **Steal from ShellFuzzer**: Their grammar is public; adapt their token categories.

### Phase 4: Grammar-Based Generation (Scaffolded)

The generator fuzzer scaffolding is in place:

```bash
cd tools/fuzzer
uv run fuzzer --generator -n 1000 -v
```

Currently uses trivial templates. To expand: invert Parable's grammar so `generate()` walks the same rules making random choices at each branch.

### The Hard Part

The fuzzing loop is easy. Triaging discrepancies is hard:

- When parsers disagree, which is wrong?
- Some discrepancies are known limitations (e.g., `$(!)` handling)
- Some are bash bugs, not Parable bugs
- Manual investigation required for each unique discrepancy

Consider bucketing discrepancies by:
- Construct type (heredoc, expansion, arithmetic, etc.)
- Error vs different-AST
- Minimal reproducer (shrink the input)

## Tools Worth Investigating

- **[Grammarinator](https://github.com/renatahodovan/grammarinator)** - Grammar-based fuzzer, found 100+ JS engine bugs
- **[ShellFuzzer](https://github.com/user09021250/shellfuzzer)** - Directly targets shell interpreters
- **AFL++ with custom mutators** - Token-level fuzzing merged into mainline

## Sources

- [ShellFuzzer: Grammar-based Fuzzing of Shell Interpreters](https://arxiv.org/html/2408.00433)
- [Token-Level Fuzzing (USENIX Security 2021)](https://www.usenix.org/conference/usenixsecurity21/presentation/salls)
- [Grammar Mutation for Testing Input Parsers (TOSEM 2025)](https://dl.acm.org/doi/10.1145/3708517)
- [Semantic-Aware Fuzzing with LLMs](https://arxiv.org/html/2509.19533)
- [Awesome-Grammar-Fuzzing](https://github.com/Microsvuln/Awesome-Grammar-Fuzzing) - Curated paper list
- [The Fuzzing Book](https://www.fuzzingbook.org/html/Grammars.html) - Comprehensive reference
