# Corpus Origin

Test corpus files from [Oils](https://github.com/oilshell/oil) (formerly Oil Shell).

## Source

- **Repository**: https://github.com/oilshell/oil
- **Path**: `spec/*.test.sh`
- **Commit**: d279e061efc741f298eea7aa18aa847e9ed5105c
- **Retrieved**: 2026-01-09

## Files

| File           | Description                                      | Tests |
| -------------- | ------------------------------------------------ | ----- |
| parsing.txt    | Arithmetic, arrays, assignments, heredocs, etc.  | 530   |
| expansion.txt  | Variable expansion, brace expansion, globbing    | 486   |
| builtin.txt    | Builtin command tests                            | 683   |
| control.txt    | Control flow (if, case, loops)                   | 67    |
| misc.txt       | Other tests (quoting, pipelines, etc.)           | 729   |

**Total: 2,495 tests**

## Conversion Process

1. Extracted bash code from `#### Test Name` sections in `*.test.sh` files
2. Skipped YSH-specific tests (files prefixed with `ysh-`, `hay`, `expr-`, etc.)
3. Validated each snippet with `bash -O extglob -n`
4. Filtered out 72 tests that bash rejects (alias edge cases, etc.)
5. Converted to tree-sitter corpus format

## Modifications

Excluded 94 test files that are YSH-specific or test runtime behavior not relevant to parsing:
- All `ysh-*` files (YSH language features)
- `hay*`, `expr-*`, `func-*`, `proc-*` (YSH constructs)
- `interactive*`, `history*`, `completion*` (interactive mode)
- `errexit*`, `strict-*`, `fatal-errors*` (runtime error handling)
- `signal*`, `job-control*` (runtime behavior)

Excluded 72 individual tests that bash -n rejects (mostly alias expansion edge cases that require runtime evaluation).

## License

Apache License 2.0

```
Copyright 2016 Andy Chu. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
