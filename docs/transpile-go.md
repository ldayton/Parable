# Transpiling Parable to Go

## Task

Transpile `src/parable.py` (a recursive descent bash parser) to idiomatic Go via `bin/transpile-go.py`. The Python source is ~7,600 lines. A working JS transpiler (`bin/transpile-js.py`) already exists as reference.

The goal is **not** a general-purpose Python-to-Go transpiler—it's a bespoke tool for this specific codebase's restricted Python subset.

## Iterative Workflow

```
1. Edit bin/transpile-go.py
2. Run: just transpile-go
3. Run: just test-go
4. See failures, go to 1
```

The test runner (`bin/run-go-tests.go`) uses the same `.tests` files as Python/JS. It expects:
- `src.Parse(input string) ([]Node, error)`
- `src.ParseError` type
- `Node.ToSexp() string` method

## Key Python → Go Mappings

| Python | Go |
|--------|-----|
| `class Foo:` | `type Foo struct { ... }` |
| `class Foo(Bar):` | Embed `Bar` in struct, or interface |
| `self.x` | `p.x` (receiver name) |
| `def method(self):` | `func (p *Parser) Method()` |
| `None` | `nil` |
| `True`/`False` | `true`/`false` |
| `list.append(x)` | `slice = append(slice, x)` |
| `len(x)` | `len(x)` (same!) |
| `str(x)` | `fmt.Sprintf("%v", x)` or `strconv.Itoa` |
| `x[1:3]` | `x[1:3]` (same for slices!) |
| `for x in items:` | `for _, x := range items` |
| `range(n)` | `for i := 0; i < n; i++` |
| `range(a, b)` | `for i := a; i < b; i++` |
| `isinstance(x, Foo)` | Type switch or `x, ok := val.(Foo)` |
| `raise ParseError(msg)` | `return nil, &ParseError{msg}` |
| `try: ... except:` | `if err != nil { ... }` |
| `f"hello {x}"` | `fmt.Sprintf("hello %v", x)` |
| `"".join(items)` | `strings.Join(items, "")` |
| `s.startswith(x)` | `strings.HasPrefix(s, x)` |
| `s.endswith(x)` | `strings.HasSuffix(s, x)` |
| `s.find(x)` | `strings.Index(s, x)` |
| `s.replace(a, b)` | `strings.ReplaceAll(s, a, b)` |
| `x in set` | `_, ok := set[x]; ok` |

## Go-Specific Challenges

### 1. Error Handling
Python uses exceptions; Go uses return values. Every function that can fail needs `(result, error)` return type. Callers must check `if err != nil`.

### 2. No Inheritance
Go has no class inheritance. Options:
- Struct embedding (composition)
- Interfaces for polymorphism
- The `Node` hierarchy will likely need an interface with `ToSexp() string`

### 3. Sum Types / Variant Nodes
Python: `isinstance(node, Command)`. Go options:
- Interface + type switch
- Tagged union with type field
- Each node type implements `Node` interface

### 4. String Handling
Go strings are immutable, UTF-8 byte sequences. Indexing gives bytes, not runes. Use `[]rune` for character-level access or be careful with byte indexing.

### 5. No Default Arguments
Go has no default parameter values. Use variadic, option structs, or multiple function variants.

## Reference: JS Transpiler Approach

The JS transpiler (`bin/transpile-js.py`) walks Python's AST via `ast.NodeVisitor`:
- `visit_Module`, `visit_ClassDef`, `visit_FunctionDef` for structure
- `visit_expr_*` methods return strings for expressions
- `emit()` outputs indented lines
- Tracks context: `in_class_body`, `in_method`, `declared_vars`
- Preserves standalone comments via `tokenize`

The Go transpiler can follow similar structure but emit Go syntax.

## Files

- `bin/transpile-go.py` — The transpiler (edit this)
- `src/parable.go` — Generated output (don't edit)
- `bin/run-go-tests.go` — Test runner
- `tests/**/*.tests` — Shared test cases

## Commands

```bash
just transpile-go   # Regenerate src/parable.go
just test-go        # Run tests against Go parser
just fmt-go         # Check/fix Go formatting
just test-go -f heredoc  # Filter to specific tests
```
