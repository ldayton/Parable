# Architectural Comparison: `skip_matched_pair` and Bracket Matching

This document compares bash's bracket-matching infrastructure in `subst.c` with Parable's implementation in `parable.py`, identifying gaps and alignment.

## Overview

Bash uses a layered extraction architecture in `subst.c` (13,279 lines) for parsing nested constructs. The key functions form a delegation hierarchy:

```
skipsubscript()           → skip_matched_pair()
extract_command_subst()   → extract_delimited_string() or xparse_dolparen()
extract_function_subst()  → extract_dollar_brace_string() or xparse_dolparen()
```

Parable's `arith-refactor` branch introduces `_skip_matched_pair()` to mirror this, but with significant behavioral gaps.

---

## Function Comparison

### `skip_matched_pair()` / `_skip_matched_pair()`

| Aspect | Bash (`subst.c:2086-2177`) | Parable (`parable.py:6259-6305`) |
|--------|----------------------------|----------------------------------|
| Lines of code | 91 | 47 |
| Flags | `1` = literal, `2` = past open | `_SMP_LITERAL`, `_SMP_PAST_OPEN` |
| Backslash escape | ✅ `pass_next` | ✅ `pass_next` |
| Single quotes | ✅ delegates to `skip_single_quoted()` | ⚠️ toggles `in_single` boolean |
| Double quotes | ✅ delegates to `skip_double_quoted()` | ⚠️ toggles `in_double` boolean |
| Backticks | ✅ `backq` state machine | ❌ not handled |
| `$(...)` | ✅ `extract_delimited_string()` | ❌ not handled |
| `${...}` | ✅ `extract_dollar_brace_string()` | ❌ not handled |
| Multibyte | ✅ `ADVANCE_CHAR` macro | ❌ assumes single-byte |

### `skipsubscript()` / `_skip_subscript()`

Both are thin wrappers that delegate to their respective `skip_matched_pair`:

**Bash** (`subst.c:2186-2188`):
```c
int skipsubscript (const char *string, int start, int flags)
{
  return (skip_matched_pair (string, start, '[', ']', flags));
}
```

**Parable** (`parable.py:6308-6314`):
```python
def _skip_subscript(s: str, start: int, flags: int = 0) -> int:
    return _skip_matched_pair(s, start, "[", "]", flags)
```

This structural alignment is correct.

### `assignment()` / `_assignment()`

**Bash** (`general.c:480-537`):
- Handles `PST_COMPASSIGN` parser state via flags
- Calls `skipsubscript()` with flag translation: `(flags & 2) ? 1 : 0`
- Returns index of `=`, or `0` for non-assignment

**Parable** (`parable.py:6317-6353`):
- Similar structure, returns `-1` instead of `0` for non-assignment
- Flag translation: `_SMP_LITERAL if (flags & 2) else 0`

---

## Missing Nested Construct Handling

### Bash's Quote Delegation

Bash's `skip_matched_pair()` calls dedicated functions for quotes:

```c
// subst.c:2146-2150
else if ((flags & 1) == 0 && (c == '\'' || c == '"'))
{
  i = (c == '\'') ? skip_single_quoted (string, slen, ++i, 0)
                  : skip_double_quoted (string, slen, ++i, 0);
}
```

These functions (`subst.c:1014-1143`) handle:
- Backticks inside double quotes
- `$(...)` and `${...}` inside double quotes
- `$'...'` ANSI-C quoting with `SX_COMPLETE` flag
- Multibyte character boundaries

**Parable** just toggles booleans:
```python
# parable.py:6291-6298
if not literal and c == "'" and not in_double:
    in_single = not in_single
    i += 1
    continue
if not literal and c == '"' and not in_single:
    in_double = not in_double
    i += 1
    continue
```

### Bash's Command Substitution Handling

```c
// subst.c:2152-2170
else if ((flags & 1) == 0 && c == '$' && (string[i+1] == LPAREN || string[i+1] == LBRACE))
{
  si = i + 2;
  if (string[i+1] == LPAREN)
    temp = extract_delimited_string (string, &si, "$(", "(", ")", SX_NOALLOC|SX_COMMAND);
  else
    temp = extract_dollar_brace_string (string, &si, 0, SX_NOALLOC);
  i = si;
  // ...
}
```

**Parable** has no equivalent—`$(...)` and `${...}` inside subscripts are not recursively parsed.

### Bash's Backtick Handling

```c
// subst.c:2119-2130
else if (backq)
{
  if (c == '`')
    backq = 0;
  ADVANCE_CHAR (string, slen, i);
  continue;
}
else if ((flags & 1) == 0 && c == '`')
{
  backq = 1;
  i++;
  continue;
}
```

**Parable** has no backtick state machine.

---

## Extraction Function Hierarchy (Bash Only)

Parable lacks equivalents to these `subst.c` functions:

| Function | Lines | Purpose |
|----------|-------|---------|
| `extract_delimited_string()` | 1361-1528 | Generic nested delimiter extraction with comment handling |
| `extract_dollar_brace_string()` | 1825-2078 | `${...}` with `dolbrace_state` machine |
| `extract_command_subst()` | 1262-1276 | `$(...)` dispatcher to `extract_delimited_string` or `xparse_dolparen` |
| `extract_function_subst()` | 1281-1295 | `${|...}` funsub dispatcher |
| `skip_single_quoted()` | 1127-1143 | Single quote skipper with `$'...'` support |
| `skip_double_quoted()` | 1014-1080 | Double quote skipper with nested expansion support |

### `extract_delimited_string` Features

From `subst.c:1361-1528`:
- Comment handling (`in_comment` for `#` after whitespace/newline)
- Recursive self-calls for nested openers
- `SX_COMMAND` flag for command context
- Handles `$(...)` and `${|...}` funsub nested inside

### `extract_dollar_brace_string` Features

From `subst.c:1825-2078`:
- `dolbrace_state` state machine (`DOLBRACE_PARAM`, `DOLBRACE_WORD`, `DOLBRACE_QUOTE`)
- State stack `dbstate[]` for nested `${...}`
- Heredoc special case delegation
- Handles backticks, `$(...)`, single/double quotes recursively

---

## Practical Impact

### Inputs That Break Parable

```bash
# Subscript containing command substitution with bracket
arr[$(echo "]")]        # Parable sees ] inside $() as closing bracket

# Subscript with backtick command substitution
arr[`echo "]"`]         # Parable sees ] inside backticks as closing bracket

# Nested parameter expansion
arr[${x[0]}]            # Parable doesn't recurse into ${...}

# Double-quoted bracket in subscript
arr["x]y"]              # Parable's simple quote toggle may fail on edge cases
```

### Where Parable's Version Suffices

The `_SMP_LITERAL` flag (used during compound assignment parsing after expansion) bypasses all quote/escape handling. For post-expansion contexts where bash also uses literal mode, Parable's implementation is adequate:

```python
# parable.py:6369 - compound assignment uses _SMP_LITERAL
end = _skip_subscript(s, i, _SMP_LITERAL)
```

---

## Callers in Each Codebase

### Bash `skipsubscript()` Callers

| File | Line | Context |
|------|------|---------|
| `subst.c` | 816 | During expansion |
| `subst.c` | 1968 | Inside `skip_double_quoted` |
| `general.c` | 514 | `assignment()` function |
| `arrayfunc.c` | 758, 959, 991, 1038, 1313, 1317 | Array operations |
| `expr.c` | 376, 1359 | Arithmetic evaluation |

### Parable `_skip_subscript()` Callers

| File | Line | Context |
|------|------|---------|
| `parable.py` | 6337 | `_assignment()` |
| `parable.py` | 6369 | `_is_array_assignment_prefix()` |

---

## Grammar Integration

### Bash (`parse.y`)

The lexer distinguishes `WORD` vs `ASSIGNMENT_WORD` tokens:

```yacc
// parse.y:5847
? ASSIGNMENT_WORD : WORD;
```

The `assignment()` function in `general.c` is called during tokenization to make this determination, using `skipsubscript()` for array subscripts.

### Parable (`parable.py`)

Uses `_is_assignment_word()` (`parable.py:7167-7169`) which delegates to `_assignment()`:

```python
def _is_assignment_word(self, word: Word) -> bool:
    return _assignment(word.value) != -1
```

---

## Summary

| Aspect | Architectural Alignment | Behavioral Alignment |
|--------|------------------------|---------------------|
| Function names | ✅ Matches bash naming | — |
| Flag semantics | ✅ `_SMP_LITERAL`, `_SMP_PAST_OPEN` | — |
| Delegation pattern | ✅ `_skip_subscript` → `_skip_matched_pair` | — |
| Quote handling | ⚠️ Structural only | ❌ Missing recursive handling |
| Backticks | ❌ Not present | ❌ |
| `$(...)` recursion | ❌ Not present | ❌ |
| `${...}` recursion | ❌ Not present | ❌ |
| Multibyte support | ❌ Not present | ❌ |

The branch achieves **structural/naming alignment** but not **behavioral parity**. The missing recursive extraction means Parable will mis-parse subscripts containing command substitutions or parameter expansions with embedded brackets.
