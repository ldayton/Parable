# Corpus Origin

Test corpus files from [GNU Bash](https://github.com/bminor/bash) (GitHub mirror).

## Source

- **Repository**: https://github.com/bminor/bash
- **Path**: `tests/*.tests`
- **Commit**: 637f5c8696a6adc9b4519f1cd74aa78492266b7f (Bash-5.3 patch 9)
- **Retrieved**: 2026-01-09

## Files

| File      | Description                           | Tests |
| --------- | ------------------------------------- | ----- |
| tests.txt | GNU Bash test suite (complete files)  | 78    |

**Total: 78 tests**

## Conversion Process

1. Collected all `*.tests` files from bash source `tests/` directory
2. Validated each file with `bash -O extglob -n`
3. Converted passing files to tree-sitter corpus format

## Excluded Files

5 test files excluded because they contain intentional syntax errors for error handling tests:

- `arith-for.tests` - syntax error tests in arithmetic for loops
- `array.tests` - intentional unquoted metacharacter errors
- `comsub2.tests` - command substitution error cases
- `posixexp.tests` - POSIX expansion error tests
- `posixexp2.tests` - POSIX expansion error tests

## License

GNU General Public License v3.0

```
Copyright (C) Free Software Foundation, Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
