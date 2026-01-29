# Parable Transpiler

Python → {Go, TypeScript, Rust, Zig, Java, C#, Swift, Ruby, C, Python} transpiler for parable.py.

See [docs/ir.md](docs/ir.md) for the IR specification.

## Dependencies

### Required

```bash
brew install uv
```

### Target Language Compilers

For compilation-based backend tests, install the compilers for languages you want to test:

| Language   | Brew Package       | Compiler Command       |
| ---------- | ------------------ | ---------------------- |
| Go         | `go`               | `go build`             |
| Rust       | `rust`             | `rustc`                |
| Zig        | `zig`              | `zig build`            |
| Java       | `openjdk`          | `javac`                |
| TypeScript | `node`             | `npx tsc`              |
| C          | (Xcode CLT)        | `clang`                |
| Swift      | (Xcode CLT)        | `swiftc`               |
| C#         | `dotnet`           | `dotnet build`         |
| Ruby       | `ruby`             | `ruby -c`              |
| Python     | `python@3.14`      | `python -m py_compile` |

Install all:

```bash
brew install go rust zig openjdk node dotnet ruby python@3.14
```

C and Swift compilers come with Xcode Command Line Tools:

```bash
xcode-select --install
```

TypeScript requires the compiler:

```bash
npm install -g typescript
```

## Usage

```bash
just emit          # transpile to stdout
just go            # transpile and write to ../src/parable.go
just check         # transpile and verify Go compiles
just test          # transpile, write, run Go tests
just test-all      # run all backend compilation tests
just errors        # show Go compilation errors
```
