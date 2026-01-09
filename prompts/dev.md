# Parable Development

## Working on a Feature

1. **Write failing tests first** - define expected behavior before implementation
2. **Implement until tests pass** - minimal code to make it work
3. **Research edge cases** - tree-sitter-bash corpus, real scripts, Stack Overflow
4. **Add edge case tests** - fix any failures
5. **Commit** - one logical change per commit

## Testing

```bash
uv run pytest tests/                    # all tests
uv run pytest tests/01_words.tests      # single module
uv run pytest -k "heredoc"              # by name pattern
```

Tests are validated against `bash -n` to ensure we only accept valid bash.

## Reference

- `reference/` - source materials (gitignored): bash-parse.y, posix-shell.html, bash-manpage.txt
- `docs/roadmap.md` - planned features and priorities
