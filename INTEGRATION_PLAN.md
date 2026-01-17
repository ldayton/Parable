# Integration Plan: Delimiter Tracking

## Current State (Dead Code)

- `_open_brace_count` / `_open_cond_count`: Tracked but never used for decisions
- `_reserved_word_acceptable()`: Exists but never called
- `_special_case_tokens()`: Exists but never called
- `DelimiterStack`: Actually used for better error messages ✓

## Legacy Code to Replace

```python
# In parse_simple_command() at line 9208:
if len(words) == 0:
    reserved = self._lex_peek_reserved_word()
    if reserved == "}" or reserved == "]]":
        break
```

This scattered check should be centralized in `_lex_peek_reserved_word()`.

---

## Integration Steps

### Step 1: Integrate `_reserved_word_acceptable()` into `_lex_peek_reserved_word()`

**Change:**
```python
def _lex_peek_reserved_word(self) -> str | None:
    tok = self._lex_peek_token()
    if tok.type != TokenType.WORD:
        return None
    word = tok.value
    if word.endswith("\\\n"):
        word = word[:-2]
    # Gate reserved word recognition by context
    if not self._reserved_word_acceptable():
        return None
    if word in RESERVED_WORDS or word in ("{", "}", "[[", "]]", "!", "time"):
        return word
    return None
```

**Why this works:**
- `_reserved_word_acceptable()` checks token history
- Returns True after `;`, `|`, `\n`, start of input, etc.
- Returns False after regular WORD tokens
- This replaces the `len(words) == 0` check with proper token-based context

### Step 2: Remove legacy check in `parse_simple_command()`

**Delete:**
```python
if len(words) == 0:
    reserved = self._lex_peek_reserved_word()
    if reserved == "}" or reserved == "]]":
        break
```

**Why safe:** The check is now inside `_lex_peek_reserved_word()`. When `_reserved_word_acceptable()` is False (not at command position), `_lex_peek_reserved_word()` returns None, so callers don't see `}` or `]]` as reserved.

### Step 3: Remove redundant `_open_brace_count` / `_open_cond_count`

**Analysis:** These counts were intended for bash-style lexer decisions, but:
- Parable's architecture is different - parser structure handles this
- `}` at command position always breaks the loop
- Whether `}` is consumed depends on parser context (inside brace group or not)
- `DelimiterStack` provides the same depth info plus positions

**Change:**
- Remove `_open_brace_count` and `_open_cond_count` from Parser
- Remove from `SavedParserState`
- Keep `DelimiterStack` (provides positions for error messages)
- For depth checks, use `_delimiter_stack.depth()`

### Step 4: Verify `_special_case_tokens()` is needed

**Current handling:**
- Function names: `parse_function()` uses `peek_word()` bypassing tokenization
- Case values: `parse_case()` uses `parse_word()`

**Question:** Does `_reserved_word_acceptable()` integration break these?

Test: `function if { echo test; }` - function named `if`
- After `function`, history[0] = WORD("function")
- `_reserved_word_acceptable()` returns False (after WORD)
- `_lex_peek_reserved_word()` returns None
- `if` is not recognized as reserved word ✓

Actually this might break things! Let me check... After consuming `function`:
- `parse_function()` calls `self._lex_consume_word("function")`
- Then calls `peek_word()` which bypasses tokenization entirely

So `_special_case_tokens()` may not be needed since `parse_function()` doesn't go through `_lex_peek_reserved_word()` for the function name.

**Decision:** Remove `_special_case_tokens()` - it's documenting cases that are handled differently.

---

## Summary of Changes

| Item | Action |
|------|--------|
| `_reserved_word_acceptable()` | **Integrate** into `_lex_peek_reserved_word()` |
| `_special_case_tokens()` | **Remove** - cases handled by different parse paths |
| `_open_brace_count` | **Remove** - redundant with DelimiterStack |
| `_open_cond_count` | **Remove** - not needed |
| `DelimiterStack` | **Keep** - used for error messages |
| `len(words) == 0` check | **Remove** - replaced by `_reserved_word_acceptable()` |

---

## Verification

After each step:
1. `just test` - all 4535 tests pass
2. `just transpile && just test-js` - JS tests pass
3. Manual test edge cases:
   - `}` at top level → error
   - `{ echo; }` → parses correctly
   - `echo }` → `}` is argument
   - `function if { echo; }` → function named `if`
   - `case if in if) echo ;; esac` → case value `if`
