# Parable Development

## Working on a Feature

1. **Consult reference materials** - read `reference/` docs before starting
2. **Write failing tests first** - define expected behavior before implementation
3. **Implement until tests pass** - minimal code to make it work
4. **Research edge cases** - tree-sitter-bash corpus, real scripts, resources below
5. **Add edge case tests** - fix any failures
6. **Commit** - one logical change per commit

## Testing

```bash
just test                               # run tests (Python 3.14)
just test -k "heredoc"                  # by name pattern
just test tests/01_words.tests          # single module
just test-all                           # all Python versions (required before committing)
```

Tests are validated against `bash -n` to ensure we only accept valid bash.

## Reference

- `reference/` - source materials: bash-parse.y, posix-shell.html, bash-manpage.txt
- `docs/roadmap.md` - planned features and priorities

## Edge Case Resources

- [Greg's Wiki](https://mywiki.wooledge.org) - BashFAQ, BashPitfalls, BashGuide
- [Bash Hackers Wiki](https://wiki.bash-hackers.org) - detailed edge cases and undocumented behavior
- [POSIX Shell spec](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html) - what's specified vs bash extensions
- [ShellCheck wiki](https://github.com/koalaman/shellcheck/wiki) - real-world edge cases from linting
- [tree-sitter-bash corpus](https://github.com/tree-sitter/tree-sitter-bash/tree/master/corpus) - parser test cases
- [Bash CHANGES](https://git.savannah.gnu.org/cgit/bash.git/tree/CHANGES) - version-specific behavior changes
- GitHub code search (`language:bash`) - what people actually write
- [bug-bash mailing list](https://lists.gnu.org/archive/html/bug-bash/) - bug reports with minimal repros
