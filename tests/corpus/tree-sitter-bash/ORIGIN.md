# Corpus Origin

Test corpus files from [tree-sitter-bash](https://github.com/tree-sitter/tree-sitter-bash).

## Source

- **Repository**: https://github.com/tree-sitter/tree-sitter-bash
- **Path**: `test/corpus/`
- **Commit**: a06c2e4415e9bc0346c6b86d401879ffb44058f7
- **Retrieved**: 2026-01-08

## Files

| File           | Source                     |
| -------------- | -------------------------- |
| commands.txt   | test/corpus/commands.txt   |
| literals.txt   | test/corpus/literals.txt   |
| statements.txt | test/corpus/statements.txt |

## Modifications

Removed tests containing invalid bash syntax (tree-sitter bugs):

1. **literals.txt** - "Variable assignments immediately followed by a terminator"
   - Input: `loop=; variables=& here=;;`
   - Rejected by bash 5.3.9: `syntax error near unexpected token ';;'`

2. **statements.txt** - Case in "Case statements" test
   - Input: `case "$arg" in *([0-9])([0-9])) echo "$arg" esac`
   - Rejected by bash 5.3.9: `syntax error near unexpected token '('`
   - (consecutive extglob patterns without operator prefix)

## License

MIT License

```
The MIT License (MIT)

Copyright (c) 2017 Max Brunsfeld

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
