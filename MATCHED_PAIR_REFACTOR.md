# Matched Pair Parsing Refactor

## Problem Statement

Parable has 35+ scattered depth-tracking loops for parsing matched pairs (braces, brackets, quotes, parens). Each loop independently handles (or fails to handle):
- Quote tracking
- Backslash escapes
- Nested constructs
- EOF detection

Bash has ONE function: `parse_matched_pair()`. When it encounters a quote inside a construct, it recursively calls itself with the quote as both `open` and `close`. This is cleaner and more correct.

## Bash Architecture (from parse.y lines 3877-4210)

```c
parse_matched_pair(int qc, int open, int close, size_t *lenp, int flags)
{
    count = 1;
    while (count) {
        ch = shell_getc(...);

        // 1. EOF = immediate error
        if (ch == EOF) {
            parser_error("unexpected EOF while looking for matching `%c'", close);
            return &matched_pair_error;
        }

        // 2. Closing delimiter decrements count
        if (ch == close) count--;

        // 3. Opening delimiter increments count (when open != close)
        if (ch == open && open != close) count++;

        // 4. Inside single quotes, almost everything is literal
        if (open == '\'') {
            if (ch == '\\') tflags |= LEX_PASSNEXT;
            continue;
        }

        // 5. Backslash sets "pass next" flag
        if (ch == '\\') tflags |= LEX_PASSNEXT;

        // 6. Quotes trigger recursion
        if (shellquote(ch)) {
            push_delimiter(dstack, ch);
            nestret = parse_matched_pair(ch, ch, ch, &nestlen, rflags);
            pop_delimiter(dstack);
            // append nestret to result
        }

        // 7. ${ $( $[ trigger nested parsing
        if (wasdol && ch in '({[') {
            // recursive calls for each construct
        }
    }
    return result;
}
```

Key insights:
- **One function** handles all matched pairs
- **Recursion** for quotes (quote is both open AND close)
- **Flags** control behavior (P_DQUOTE, P_DOLBRACE, P_COMMAND, etc.)
- **EOF is always an error** - returns sentinel, not None

## Current Parable Scattered Loops

### Lexer Level (`_read_word_internal` and helpers)

| Line | Construct | Quote Handling | EOF Check |
|------|-----------|----------------|-----------|
| 981 | Extglob `@(...)` | None | No error |
| 1174 | Nested extglob | None | No error |
| 1214 | `$(())` in extglob | None | No error |
| 1659 | Array subscript `[...]` | QuoteState | No error |

### Parameter Expansion (`_read_braced_param`)

| Line | Construct | Quote Handling | EOF Check |
|------|-----------|----------------|-----------|
| 1800 | `${!prefix@}` trailing | None | Partial |
| 1839 | `${!prefix@}` trailing | None | Partial |
| 1892 | Indirect op arg | QuoteState | Partial |
| 2016 | Unknown `${...}` syntax | QuoteState | Raises |

### Parser Level

| Line | Construct | Quote Handling | EOF Check |
|------|-----------|----------------|-----------|
| 7596 | Process substitution | None | Returns None |
| 7700 | Arithmetic `$((...))` | None | Returns None |
| 8494 | Deprecated `$[...]` | None | Raises |
| 8823 | Here-doc delimiter | None | No error |
| 9154 | Arithmetic command `((...))` | QuoteState | Returns None |

### Utility Functions

| Line | Construct | Quote Handling | EOF Check |
|------|-----------|----------------|-----------|
| 5833 | `_track_extglob_nesting` | QuoteState | N/A |
| 6306-6351 | Various depth helpers | QuoteState | N/A |

## Refactor Plan

### Prerequisites

```bash
git fetch origin
git checkout -b refactor-matched-pair origin/main
```

After each step: `just quick-check && git add -A && git commit -m "..."`

---

### Phase 1: Create Unified Infrastructure

#### Step 1.1: Add MatchedPairResult type

Create a result type that distinguishes success from error:

```python
class MatchedPairError(Exception):
    """Raised when a matched pair construct is unclosed at EOF."""
    pass

# Or use a sentinel pattern like bash:
# MATCHED_PAIR_ERROR = object()
```

Commit: `feat: add MatchedPairError exception class`

#### Step 1.2: Add MatchedPairFlags enum

```python
class MatchedPairFlags(IntFlag):
    NONE = 0
    DQUOTE = 1       # Inside double quotes
    DOLBRACE = 2     # Inside ${...}
    COMMAND = 4      # Inside command substitution
    ARITH = 8        # Inside arithmetic
    ALLOWESC = 16    # Allow backslash escapes (for $'...')
```

Commit: `feat: add MatchedPairFlags for matched pair parsing`

#### Step 1.3: Create `_parse_matched_pair()` method

Add to Lexer class:

```python
def _parse_matched_pair(
    self,
    qc: str,           # Quote context (or empty)
    open_char: str,    # Opening delimiter
    close_char: str,   # Closing delimiter
    flags: MatchedPairFlags = MatchedPairFlags.NONE
) -> tuple[str, int]:  # (content, end_position)
    """
    Parse a matched pair construct, handling quotes via recursion.

    Raises MatchedPairError on unclosed construct at EOF.
    """
    start = self.pos
    count = 1
    chars: list[str] = []
    pass_next = False

    while count > 0:
        if self.at_end():
            raise MatchedPairError(
                f"unexpected EOF while looking for matching `{close_char}'",
                pos=start
            )

        ch = self.advance()

        # Backslash escape handling
        if pass_next:
            pass_next = False
            chars.append(ch)
            continue

        # Inside single quotes, almost everything is literal
        if open_char == "'" and qc != "'":
            if ch == "\\" and (flags & MatchedPairFlags.ALLOWESC):
                pass_next = True
            chars.append(ch)
            if ch == close_char:
                count -= 1
            continue

        # Backslash
        if ch == "\\":
            pass_next = True
            chars.append(ch)
            continue

        # Closing delimiter
        if ch == close_char:
            count -= 1
            if count > 0:
                chars.append(ch)
            continue

        # Opening delimiter (only when open != close)
        if ch == open_char and open_char != close_char:
            count += 1
            chars.append(ch)
            continue

        # Quote characters trigger recursion
        if ch in "'\"`" and open_char != close_char:
            chars.append(ch)
            nested, _ = self._parse_matched_pair(ch, ch, ch, flags)
            chars.append(nested)
            chars.append(ch)
            continue

        # ${ $( $[ trigger nested parsing
        if ch == "$" and not self.at_end():
            next_ch = self.peek()
            if next_ch == "{":
                chars.append(ch)
                chars.append(self.advance())
                nested, _ = self._parse_matched_pair("", "{", "}", flags | MatchedPairFlags.DOLBRACE)
                chars.append(nested)
                chars.append("}")
                continue
            elif next_ch == "(":
                chars.append(ch)
                chars.append(self.advance())
                if not self.at_end() and self.peek() == "(":
                    # $(( ... ))
                    chars.append(self.advance())
                    nested, _ = self._parse_matched_pair("", "(", ")", flags | MatchedPairFlags.ARITH)
                    chars.append(nested)
                    chars.append(")")
                else:
                    # $( ... )
                    nested, _ = self._parse_matched_pair("", "(", ")", flags | MatchedPairFlags.COMMAND)
                    chars.append(nested)
                chars.append(")")
                continue
            elif next_ch == "[":
                chars.append(ch)
                chars.append(self.advance())
                nested, _ = self._parse_matched_pair("", "[", "]", flags | MatchedPairFlags.ARITH)
                chars.append(nested)
                chars.append("]")
                continue

        chars.append(ch)

    return "".join(chars), self.pos
```

Commit: `feat: add unified _parse_matched_pair method`

---

### Phase 2: Migrate Lexer Loops (One at a Time)

#### Step 2.1: Migrate extglob parsing (line 981)

Replace the depth loop in `_read_word_internal` for `@(...)` etc with a call to `_parse_matched_pair("", "(", ")")`.

Commit: `refactor: use _parse_matched_pair for extglob parsing`

#### Step 2.2: Migrate nested extglob (line 1174)

Commit: `refactor: use _parse_matched_pair for nested extglob`

#### Step 2.3: Migrate `$(())` in extglob (line 1214)

Commit: `refactor: use _parse_matched_pair for arithmetic in extglob`

#### Step 2.4: Migrate array subscript (line 1659)

Commit: `refactor: use _parse_matched_pair for array subscripts`

---

### Phase 3: Migrate Parameter Expansion Loops

#### Step 3.1: Migrate `${!prefix@}` loops (lines 1800, 1839)

Commit: `refactor: use _parse_matched_pair for indirect param expansion`

#### Step 3.2: Migrate indirect op arg loop (line 1892)

Commit: `refactor: use _parse_matched_pair for indirect op arguments`

#### Step 3.3: Migrate unknown `${...}` syntax (line 2016)

Commit: `refactor: use _parse_matched_pair for unknown param syntax`

---

### Phase 4: Migrate Parser Level Loops

#### Step 4.1: Migrate process substitution (line 7596)

Commit: `refactor: use _parse_matched_pair for process substitution`

#### Step 4.2: Migrate arithmetic expansion (line 7700)

Commit: `refactor: use _parse_matched_pair for arithmetic expansion`

#### Step 4.3: Migrate deprecated `$[...]` (line 8494)

Commit: `refactor: use _parse_matched_pair for deprecated arithmetic`

#### Step 4.4: Migrate arithmetic command (line 9154)

Commit: `refactor: use _parse_matched_pair for arithmetic command`

---

### Phase 5: Cleanup

#### Step 5.1: Remove dead QuoteState usage

After migration, many `QuoteState` instances in depth loops become unused. Remove them.

Commit: `refactor: remove unused QuoteState in migrated loops`

#### Step 5.2: Remove redundant helper functions

Functions like `_track_extglob_nesting` may become unnecessary.

Commit: `refactor: remove redundant depth-tracking helpers`

#### Step 5.3: Final cleanup

Remove any remaining special cases that were only needed due to scattered loops.

Commit: `refactor: final cleanup of matched pair special cases`

---

## Acceptance Criteria

1. `just quick-check` passes after every commit
2. All 35+ scattered depth loops replaced with calls to `_parse_matched_pair`
3. Quote handling is via recursion, not inline flags
4. EOF always raises `MatchedPairError`, never returns None silently
5. No regression in test suite (4535 tests)

## Risks and Mitigations

### Risk: Behavior changes break tests

**Mitigation**: Each step is one loop migration. If tests fail, the change is small enough to debug or revert.

### Risk: Performance regression from recursion

**Mitigation**: Bash uses this pattern and is fast. Profile if needed, but unlikely to matter.

### Risk: Edge cases in quote nesting

**Mitigation**: The fuzzer will catch these. Run `just fuzz` after Phase 4.

## Notes

- The `_parse_matched_pair` signature may need adjustment as we discover edge cases
- Some loops have special handling for specific constructs (heredoc delimiters, etc.) that may need flags
- The JS transpiler will need to handle the new function

## Commands

```bash
# Start
git fetch origin
git checkout -b refactor-matched-pair origin/main

# After each step
just quick-check && git add -A && git commit -m "..."

# Final verification
just test
just transpile && just test-js
```
