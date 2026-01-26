# IR Design: Research Gaps

Areas requiring investigation before committing to the IR design in `ir.md`. All research should be scoped to Parable's specific use case: transpiling a shell parser from Python to multiple targets.

## 1. Ownership Model for Parser ASTs

**Gap:** The IR proposes `Pointer(owned=bool)` but Rust's ownership model is richer: `&T`, `&mut T`, `Box<T>`, and lifetime relationships.

**Research questions:**
- Audit `parable.py`: How many distinct ownership patterns exist in the AST node graph?
- Do any AST nodes get mutated after construction? (If not, `&T` everywhere may suffice)
- Are there any cross-references between AST nodes, or is it a strict tree?
- Does the parser ever return partial results that outlive intermediate state?

**Experiment:** Manually translate 3-4 representative parser methods to Rust using arena allocation. Document where the type system fights back.

**Success criterion:** Demonstrate that Parable's AST fits one of:
- Pure tree (parent owns children) → arena allocation works
- DAG with shared nodes → need `Rc` or indices
- Graph with cycles → need `unsafe` or different approach

## 2. Error Handling Strategy

**Gap:** Listed as "open question" in ir.md, but affects function signatures throughout.

**Research questions:**
- Inventory all exception types raised in `parable.py`
- Which functions can fail? Which are infallible?
- Are exceptions used for control flow (e.g., backtracking) or only for true errors?
- What error information must propagate to callers?

**Experiment:** Prototype two approaches for a subset of the parser:
1. Go-style: functions return `(result, error)`, callers check
2. Result-style: functions return `Result<T, ParseError>`, use `?` operator

Measure: lines of code, readability, how error context is preserved.

**Deliverable:** Decision document recommending one strategy with IR implications.

## 3. Arena Allocation Feasibility

**Gap:** Rust and C strategies assume arena allocation, but this constrains the runtime model.

**Research questions:**
- What is the lifetime of AST nodes in Parable's actual usage?
- Is the AST consumed immediately after parsing, or passed to later phases?
- Does error recovery require discarding partial ASTs?
- Are there any cases where individual nodes need different lifetimes?

**Experiment:** Instrument `parable.py` to track:
- Peak AST node count during typical parses
- Whether nodes are ever freed before parse completion
- Memory high-water mark

**Constraint check:** If all nodes live until parse completion and are freed together, arena works. If nodes have heterogeneous lifetimes, it doesn't.

## 4. Truthiness and None Semantics

**Gap:** ir.md proposes converting `if items:` to `if len(items) > 0`, but Python's truthiness is more complex.

**Research questions:**
- Grep `parable.py` for all boolean contexts: `if x:`, `while x:`, `x and y`, `x or y`, `not x`
- Categorize: Which are None checks? Which are emptiness checks? Which are both?
- Are there any cases where `if x:` means "x is truthy" rather than "x is not None and not empty"?

**Deliverable:** Table mapping each truthiness pattern in Parable to its intended semantics, informing IR design:

| Pattern | Count | Intended Meaning | IR Representation |
|---------|-------|------------------|-------------------|
| `if node:` | ? | None check | `IsNil(node, negated=true)` |
| `if items:` | ? | Non-empty | `BinaryOp(">", Len(items), 0)` |
| `if token.value:` | ? | Non-empty string | `BinaryOp("!=", token.value, "")` |

## 5. Union/Variant Type Mapping

**Gap:** IR `Union` maps to Go interfaces, Rust enums, C tagged unions—but these have different capabilities.

**Research questions:**
- What union types exist in Parable's AST? (e.g., `Command = SimpleCommand | Pipeline | ...`)
- Are unions closed (fixed set of variants) or open (extensible)?
- How are unions discriminated? (`isinstance`, tag field, method presence?)
- Do any unions need to be extended by user code?

**Experiment:** For each union type in Parable:
1. Write the Go interface version
2. Write the Rust enum version
3. Write the C tagged union version
4. Note where semantics diverge

**Key question:** Can we use closed enums everywhere (Rust-native), or do we need open interfaces (Go-native)?

## 6. Frontend Complexity Estimation

**Gap:** ir.md claims backends will be "~500-800 lines" with complexity absorbed by frontend. This needs validation.

**Research questions:**
- What percentage of `transpile_go.py` is analysis vs emission?
- Which analysis passes are truly language-agnostic?
- What Go-specific decisions are made during "analysis" that would need to move to backend?

**Experiment:** Annotate `transpile_go.py` line-by-line:
- `[A]` = pure analysis (type inference, symbol resolution)
- `[E]` = pure emission (string building)
- `[M]` = mixed (analysis that assumes Go semantics)

**Deliverable:** Percentage breakdown and list of `[M]` cases that need design decisions.

## 7. String Handling Audit

**Gap:** Rust distinguishes `String` vs `&str`; C needs fat pointers vs null-terminated. The IR has `string` and `StringSlice` but the boundary is unclear.

**Research questions:**
- Where does Parable create new strings vs slice existing ones?
- Are string slices ever stored in AST nodes, or only used transiently?
- What string operations are used? (concatenation, slicing, comparison, formatting)

**Experiment:** Categorize all string operations in `parable.py`:
- `s[i:j]` → slice (can be borrowed)
- `s + t` → concatenation (needs allocation)
- `f"..."` → formatting (needs allocation)
- `s == t` → comparison (works on both)

**Deliverable:** Decision on whether AST string fields should be `StringSlice` (borrowed) or `string` (owned), and implications for arena design.

## 8. Missing IR Constructs Audit

**Gap:** ir.md may be missing constructs that Parable actually needs.

**Research questions:**
- Does Parable use `with` statements? (need cleanup/defer)
- Does Parable use tuple unpacking? (need destructuring)
- Does Parable use `*args` or `**kwargs`? (variadic handling)
- Does Parable use generators/iterators beyond simple `for`?
- Does Parable use any generic patterns that would benefit from Go 1.18+ generics?

**Deliverable:** List of Python constructs used in Parable with proposed IR mappings or explicit "not supported" decisions.

## 9. Incremental Migration Path

**Gap:** The plan assumes we can extract analysis passes from the Go transpiler, but they're interleaved with emission.

**Research questions:**
- Can we introduce IR as an intermediate format without breaking the existing Go transpiler?
- What's the smallest useful subset of IR to start with?
- Can we run old and new transpilers in parallel and diff output?

**Proposed approach:**
1. Define IR types (no behavior change)
2. Add IR emission as a side effect of existing Go transpiler
3. Write Go backend that consumes IR
4. Verify: `python_ast → old_transpiler → go_code` == `python_ast → ir → new_backend → go_code`
5. Once verified, delete old transpiler's emission code

**Risk:** If step 4 reveals semantic gaps in the IR, we learn early.

## Research Prioritization

| Priority | Area | Reason |
|----------|------|--------|
| P0 | Error handling strategy | Affects all function signatures; must decide early |
| P0 | Truthiness audit | Small effort, high impact on correctness |
| P1 | Ownership audit | Determines if Rust backend is feasible |
| P1 | Union type mapping | Core to AST representation |
| P1 | Frontend complexity estimation | Validates the entire approach |
| P2 | Arena feasibility | Can defer if we start with Go/JS only |
| P2 | String handling | Important but tractable |
| P3 | Missing constructs | Can add incrementally |
| P3 | Migration path | Execution detail, not design |

## Exit Criteria

Before committing to implementation, we should have:

1. **Error handling decision** with IR implications documented
2. **Ownership patterns** in Parable categorized as tree/DAG/graph
3. **Truthiness table** for all boolean contexts in `parable.py`
4. **Union type inventory** with target-language mappings
5. **Frontend/backend split estimate** with confidence bounds
6. **Go transpiler annotation** showing analysis vs emission breakdown

If any of these reveal fundamental problems (e.g., Parable's AST is a cyclic graph, or error handling requires pervasive signature changes), revisit the IR design before writing code.
