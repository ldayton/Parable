# Go Transpiler Comparison: py2many vs pytago

Analysis of two Python-to-Go transpilers to identify patterns worth adopting for Parable's Go transpiler.

## Overview

| Aspect        | py2many                           | pytago                                 | Parable                      |
| ------------- | --------------------------------- | -------------------------------------- | ---------------------------- |
| Architecture  | Plugin-based with dispatch tables | AST-to-AST with 57 transformers        | Monolithic with symbol table |
| Size          | 644 lines                         | ~3000 lines                            | 4,686 lines                  |
| Type System   | Lightweight inference             | Deferred resolution with InterfaceType | Full semantic analysis       |
| Test Coverage | 85 small examples                 | 50+ example pairs                      | One large real-world parser  |

---

## Worth Borrowing from py2many

| Feature                              | What It Does                                                                     | Why It's Useful                                 |
| ------------------------------------ | -------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Dispatch tables**                  | `{"len": visit_len, "range": visit_range, "print": visit_print}`                 | Replaces giant if/elif chains, easier to extend |
| **Width-rank auto-casting**          | `int8(1) < int16(3) < int32(5) < int64(7) < float64(10)` - auto-promote in BinOp | Handles mixed-type arithmetic correctly         |
| **Rewriter pipeline**                | Pre-rewriters → type inference → post-rewriters as separate passes               | Clean separation of concerns                    |
| **`go-cmp` for container equality**  | `cmp.Equal(left, right)` for deep comparison                                     | Correct slice/map equality semantics            |
| **`refutil` for membership**         | `refutil.Contains(slice, elem)` / `refutil.ContainsKey(map, key)`                | Clean `in` operator translation                 |
| **Set as `map[T]bool`**              | `map[string]bool{"a": true, "b": true}`                                          | Standard Go idiom for sets                      |
| **Common vars in if/else**           | Pre-declares vars assigned in both branches: `var x int` before if block         | Avoids Go scoping issues                        |
| **IntEnum with `iota`**              | Auto-incrementing enum values                                                    | Idiomatic Go enums                              |
| **IntFlag with `1 << iota`**         | Bit flags with auto bit-shift                                                    | Proper flag enums                               |
| **Unused var silencing**             | `_ = varName` after declaration for `_prefixed` vars                             | Avoids compiler errors                          |
| **`iter` library for range**         | `iter.NewIntSeq(iter.Start(0), iter.Stop(n)).All()`                              | Proper Python range() semantics                 |
| **Struct literal with named fields** | `Foo{field1: val1, field2: val2}` from positional args                           | Clean struct initialization                     |
| **Method append → assignment**       | Rewriter converts `lst.append(x)` to `lst = append(lst, x)`                      | Go's append semantics                           |
| **IfExp → If statement**             | Ternary `a if test else b` → imperative if/else                                  | Go has no ternary                               |
| **Visibility rewriter**              | Auto-converts `snake_case` → `CamelCase` for exports                             | Go naming conventions                           |
| **`defined_before()` analysis**      | Distinguishes first assignment (`:=`) from reassignment (`=`)                    | Correct variable declarations                   |

---

## Worth Borrowing from pytago

| Feature                                 | What It Does                                                | Why It's Useful                   |
| --------------------------------------- | ----------------------------------------------------------- | --------------------------------- |
| **IIFE for comprehensions**             | `[x*2 for x in items]` → `func() []int { ... }()`           | Proper scoping for comprehensions |
| **`text/template` for f-strings**       | Nested interpolation via Go templates                       | Handles complex f-strings         |
| **57-stage transformer pipeline**       | Staged passes with repeatable transformers                  | Better separation of concerns     |
| **InterfaceType with context**          | Placeholder type with `_py_context["elts"]` for candidates  | Deferred type resolution          |
| **Bindable system**                     | Pattern-matched code snippets with `@Bindable.add(pattern)` | 170+ pre-implemented bindings     |
| **Dunder → method calls**               | `__add__` → `obj.Add(other)` for user types                 | Operator overloading support      |
| **Exception → defer/recover/panic**     | try/except with condition matching via error prefixes       | Proper error handling             |
| **Yield → channels**                    | Generator functions become goroutines with channel sends    | Generator support                 |
| **Async → goroutines**                  | async/await to goroutine + channel patterns                 | Async support                     |
| **Scope transformer with callbacks**    | Missing type resolution deferred via callbacks              | Late-binding type inference       |
| **For-else → bool tracking**            | Loop completion tracked, else runs if no break              | Python for-else support           |
| **Negative index rewriting**            | `list[-1]` → `list[len(list)-1]`                            | Python negative index semantics   |
| **String index stringification**        | `"hello"[0]` returns `"h"` not `byte`                       | Python string indexing semantics  |
| **Set as `map[T]struct{}`**             | Empty struct values (zero memory)                           | More efficient than `map[T]bool`  |
| **`reflect.DeepEqual` for `.remove()`** | Generic equality in list operations                         | Correct list.remove() semantics   |
| **Slice multiply helper**               | `[1,2] * 3` → custom helper function                        | List repetition operator          |
| **HTTP requests → net/http**            | Converts `requests` library calls                           | Library translation               |
| **Scanner pattern for file loops**      | `for line in file` → bufio.Scanner                          | Idiomatic file reading            |
| **`goimports`/`gofumpt`/`golines`**     | Post-processing with Go tools                               | Guaranteed correct formatting     |
| **Expression chaining API**             | `expr.sel("method").call(arg).ref()`                        | Clean AST construction            |
| **Type dominance scoring**              | Mixed numeric ops use highest-ranked type                   | Correct type coercion             |
| **Context managers → defer**            | `with open(f) as x` → `defer x.Close()`                     | Resource management               |

---

## Combined Priority List

### Quick Wins (Low effort, High value)

| Source  | Feature                        |
| ------- | ------------------------------ |
| py2many | Dispatch tables for builtins   |
| py2many | Width-rank auto-casting        |
| py2many | Set as `map[T]bool`            |
| py2many | Unused var silencing (`_ = x`) |
| pytago  | Negative index rewriting       |
| pytago  | String index stringification   |
| pytago  | `goimports` post-processing    |

### Medium Effort

| Source  | Feature                                  |
| ------- | ---------------------------------------- |
| py2many | Common vars pre-declaration in if/else   |
| py2many | `defined_before()` for `:=` vs `=`       |
| py2many | IntEnum/IntFlag with iota                |
| pytago  | IIFE for comprehensions                  |
| pytago  | Bindable snippet system                  |
| pytago  | For-else bool tracking                   |
| pytago  | Set as `map[T]struct{}` (more efficient) |

### Longer Term (High effort, High value)

| Source  | Feature                                |
| ------- | -------------------------------------- |
| py2many | Full rewriter pipeline architecture    |
| pytago  | Multi-stage transformer system         |
| pytago  | InterfaceType with deferred resolution |
| pytago  | Exception → defer/recover/panic        |
| pytago  | Yield → channel generators             |
| pytago  | Async → goroutine patterns             |
| pytago  | `text/template` f-strings              |

---

## What Parable Already Does Better

- **Scale** - proven on 10k+ LOC real parser vs small examples
- **Three-pass semantic analysis** - full symbol table with type tracking
- **Node interface polymorphism** - concrete vs interface type handling
- **Type overrides system** - handles domain-specific edge cases
- **Union field discrimination** - `Node | string` patterns with discriminators
- **Pointer-to-slice `*[]T`** - for mutable slice parameters
- **Tuple return type tracking** - per-function element type mapping

---

## Related: Variable Scoping

Parable currently pre-declares ALL variables at function top with `var x T` plus 802 `_ = x` suppressions. Both py2many and pytago solve this more elegantly:

| Technique | py2many | pytago |
|-----------|---------|--------|
| `:=` vs `=` | `defined_before()` tracking | Scope transformer |
| Hoisting | Common vars in if/else branches | `ScopeFunctionVars` |

See [variable-scoping-plan-v2.md](variable-scoping-plan-v2.md) for Parable's implementation plan based on these patterns.

---

## Source Locations

- py2many: `/Users/lily/source/py2many/pygo/`
- pytago: `/Users/lily/source/pytago/pytago/go_ast/`
- Parable: `/Users/lily/source/Parable/tools/transpiler/src/transpiler/transpile_go.py`
