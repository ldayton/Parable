# Plan: Phase 6 - Unify Scanning and Parsing

## Status: BLOCKED (same as EOF_TOKEN_PLAN.md)

This plan depends on the same prerequisite as EOF_TOKEN_PLAN.md: **the Parser must be token-based**.

The goal of parsing "inline without pre-scanning" requires the parser to stop when it hits a terminator like `)`. In bash, this works because the tokenizer returns EOF when `shell_eof_token` is set. In Parable, the Parser bypasses the Lexer for operators/terminators, so there's no way to signal "stop here" to `parse_list()`.

See EOF_TOKEN_PLAN.md for the full analysis and prerequisites.

---

## Overview

Remove pre-scanning functions (`_find_cmdsub_end`, etc.) and parse nested constructs inline using save/restore state patterns. This eliminates duplicated logic between scanning and parsing.

## Current Architecture

### Pre-Scanning Functions

| Function | Line | Purpose | Callers |
|----------|------|---------|---------|
| `_find_cmdsub_end` | 4354 | Find end of `$(...)` | Formatting + `_is_valid_arithmetic_start` |
| `_find_heredoc_content_end` | 4638 | Find end of heredoc body | `_parse_command_substitution` |
| `_skip_backtick` | 4312 | Skip backtick command sub | Various |
| `_skip_heredoc` | 4511 | Skip heredoc declaration | Various |

### Usage Categories

**1. Formatting Functions (Keep)**
- Lines 1876, 1890, 1960, 1969, 2013, 2037, 2119
- Used in `_format_word_parts` for output generation
- These operate on already-parsed strings, pre-scanning is acceptable

**2. Parsing Functions (Replace)**
- `_parse_command_substitution` (line 6030+) - has its own inline logic but references `_find_cmdsub_end`
- `_is_valid_arithmetic_start` (line 4338) - uses `_find_cmdsub_end` to skip nested `$(...)`

### Current Parser State Infrastructure

Already implemented:
- `ParserStateFlags` with PST_* flags
- `DolbraceState` for `${...}` parsing
- `ContextStack` for nested scope tracking
- `_token_history` for token context

## Target Architecture

### Bash's Approach (parse.y)

```c
// In parse_comsub():
save_parser_state(&ps);
parser_state |= PST_CMDSUBST;
// ... recursive parsing ...
restore_parser_state(&ps);
```

### Parable Target

```python
def _parse_command_substitution(self) -> ...:
    saved = self._save_parser_state()
    self._set_state(ParserStateFlags.PST_CMDSUBST)
    try:
        # Parse content directly without pre-scanning
        content = self._parse_list_until_close_paren()
        ...
    finally:
        self._restore_parser_state(saved)
```

---

## Implementation Plan

### Step 1: Add Parser State Save/Restore

Create infrastructure for saving and restoring full parser state.

```python
@dataclass
class ParserState:
    """Saved parser state for nested parsing."""
    pos: int
    parser_state: int
    dolbrace_state: int
    pending_heredocs: list
    ctx_depth: int
    # ... other state ...

def _save_parser_state(self) -> ParserState:
    """Save current parser state for nested parsing."""
    return ParserState(
        pos=self.pos,
        parser_state=self._parser_state,
        dolbrace_state=self._dolbrace_state,
        pending_heredocs=list(self._pending_heredocs),
        ctx_depth=self._ctx.get_depth(),
    )

def _restore_parser_state(self, state: ParserState) -> None:
    """Restore parser state after nested parsing."""
    self._parser_state = state.parser_state
    self._dolbrace_state = state.dolbrace_state
    # Don't restore pos - we've advanced through the content
    # Don't restore heredocs - they were consumed
```

**Verification:** `just test` passes (no behavior change)

---

### Step 2: Refactor `_parse_command_substitution` to Use Save/Restore

The function already parses inline but creates a sub-parser for content:

```python
# Current (line 6375):
sub_parser = Parser(content, in_process_sub=True)
cmd = sub_parser.parse_list()
```

Change to parse in-place with state management:

```python
# Target:
saved = self._save_parser_state()
self._set_state(ParserStateFlags.PST_CMDSUBST)
cmd = self.parse_list()  # Parse directly, not via sub-parser
self._restore_parser_state(saved)
```

**Challenge:** The current approach extracts content first, then parses. We need to parse while determining where content ends.

**Solution:** Parse until we see unbalanced `)` at depth 0, using parser state to track context.

**Verification:** `just test && just transpile && just test-js`

---

### Step 3: Create `_parse_list_until` Helper

Add a method that parses a command list until a terminator is reached:

```python
def _parse_list_until_close(self, close_char: str) -> Node | None:
    """Parse command list until close_char at depth 0."""
    # Uses parser state flags to handle:
    # - case patterns (where ) isn't a closer)
    # - nested $() (where ) isn't a closer)
    # - quotes (where ) is literal)
    ...
```

This replaces the logic currently duplicated in:
- `_find_cmdsub_end`
- `_parse_command_substitution`'s while loop

**Verification:** `just test && just transpile && just test-js`

---

### Step 4: Refactor `_is_valid_arithmetic_start`

This function (line 4320) uses `_find_cmdsub_end` to skip over `$(...)` inside `$((...))`

Current:
```python
if scan_c == "$" and value[scan_i + 1] == "(":
    scan_i = _find_cmdsub_end(value, scan_i + 2)
```

Change to use a simpler skip that counts parens:
```python
if scan_c == "$" and value[scan_i + 1] == "(":
    scan_i = self._skip_nested_parens(value, scan_i + 2)
```

Or eliminate this function entirely by parsing arithmetic expressions properly.

**Verification:** `just test && just transpile && just test-js`

---

### Step 5: Handle Heredocs in Command Substitutions

The current `_parse_command_substitution` uses `_find_heredoc_content_end` (line 6362).

Heredoc handling is complex because:
- Declaration is on command line: `cat <<EOF`
- Body follows the newline

Options:
1. **Keep separate:** Heredoc body finding is fundamentally different (line-based)
2. **Defer bodies:** Parse command, note heredoc declarations, gather bodies after

Current approach uses option 2, which is reasonable. May keep `_find_heredoc_content_end` for now.

**Verification:** `just test && just transpile && just test-js`

---

### Step 6: Refactor Process Substitution Parsing

Process substitutions `<(...)` and `>(...)` have similar structure to command substitutions.

Check if they also use pre-scanning and apply similar refactoring.

**Verification:** `just test && just transpile && just test-js`

---

### Step 7: Clean Up Unused Functions

After refactoring, identify and remove:
- Unused branches in `_find_cmdsub_end`
- Dead code paths
- Redundant helper functions

Keep:
- `_find_cmdsub_end` if still needed by formatting functions
- `_find_heredoc_content_end` for heredoc body gathering

**Verification:** `just test && just transpile && just test-js`

---

### Step 8: Add Regression Tests

Create tests for edge cases that the unified parsing handles correctly:
- Nested `$($(...))`
- Command subs inside arithmetic `$((1+$(echo 2)))`
- Case patterns with `)` inside command subs
- Heredocs inside command subs

**Verification:** Full test suite + fuzzer

---

## Detailed Analysis: `_parse_command_substitution`

Current flow (lines 6030-6385):

```
1. Consume $(
2. Set PST_CMDSUBST flag
3. While loop to find matching ):
   - Track depth, quotes, case statements, heredocs
   - Handle special cases (comments, heredocs, case patterns)
4. Extract content string
5. Create sub-parser for content
6. Parse content to AST
7. Handle heredoc bodies that follow )
8. Return CommandSubstitution node
```

The while loop (lines 6064-6347) duplicates much of `_find_cmdsub_end`.

### Proposed New Flow

```
1. Consume $(
2. Save parser state
3. Set PST_CMDSUBST flag
4. Call parse_list() directly (modified to stop at unbalanced ))
5. Consume )
6. Restore parser state (keeping new position)
7. Handle heredoc bodies
8. Return CommandSubstitution node
```

### Key Challenges

1. **Knowing when to stop:** `parse_list()` doesn't know about the `)` terminator
   - Solution: Add `until_token` parameter or check depth in pipeline parsing

2. **Heredoc handling:** Bodies follow the `)`, not inline
   - Solution: Keep current deferred body gathering

3. **Error recovery:** If content is malformed, need to recover
   - Solution: Use try/except with position restoration

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Behavioral changes | Extensive test suite (4515 tests) |
| Performance regression | Pre-scanning is already O(n), inline parsing same |
| Complex interactions | Incremental refactoring with tests at each step |
| Heredoc edge cases | Keep `_find_heredoc_content_end` initially |

---

## Success Criteria

1. All 4515 tests pass (Python + JS)
2. Fuzzer finds no new regressions
3. `_find_cmdsub_end` only used by formatting functions
4. No duplicated quote/depth tracking logic between scanning and parsing
5. Clear save/restore pattern for nested constructs

---

## Files to Modify

1. `src/parable.py`:
   - Add `ParserState` dataclass
   - Add `_save_parser_state()` / `_restore_parser_state()`
   - Refactor `_parse_command_substitution()`
   - Potentially refactor `_is_valid_arithmetic_start()`
   - Potentially refactor process substitution parsing

---

## References

- `bash-oracle/parse.y` lines 4451-4678: `parse_comsub()`
- `bash-oracle/parse.y` lines 7221-7330: `save_parser_state()` / `restore_parser_state()`
- `bash-oracle/parse.y` lines 3877-4200: `parse_matched_pair()`
