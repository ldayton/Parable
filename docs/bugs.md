# Possible bash-oracle or fuzzer Bugs

Issues encountered during fuzzing that appear to be bash-oracle bugs, not Parable bugs.

All issues below are specific to `-e` mode. Parsing via file works correctly.

## Blank lines stop parsing (general)

When the input contains a blank line (two consecutive newlines), the oracle stops parsing at that point and ignores all subsequent content.

```bash
$ ~/source/bash-oracle/bash-oracle -e $'echo a\n\necho b'
(command (word "echo") (word "a"))
```

Expected: Should also parse `echo b`.

Via file, it works correctly:

```bash
$ echo $'echo a\n\necho b' > /tmp/test.sh && ~/source/bash-oracle/bash-oracle /tmp/test.sh
(command (word "echo") (word "a"))
(command (word "echo") (word "b"))
```

## Comment lines stop parsing

When the input contains a comment line (starting with `#`), the oracle stops parsing at that point.

```bash
$ ~/source/bash-oracle/bash-oracle -e $'file=x\n#comment\necho y'
(command (word "file=x"))
```

Expected: Should also parse `echo y`.

Via file, it works correctly:

```bash
$ echo $'file=x\n#comment\necho y' > /tmp/test.sh && ~/source/bash-oracle/bash-oracle /tmp/test.sh
(command (word "file=x"))
(command (word "echo") (word "y"))
```

## Impact on fuzzing

These bugs cause the fuzzer to report many false positives when using `--both-succeed`. Nearly all "discrepancies" found are actually cases where:

1. The mutated input contains a blank line or comment
2. The oracle stops parsing early
3. Parable correctly parses the full input

Workaround: Filter test inputs to exclude those with blank lines (`\n\n`) or comment lines before fuzzing.
