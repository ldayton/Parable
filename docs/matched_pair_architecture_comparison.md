# Matched Pair Architecture: Bash vs Parable

A detailed comparison of bracket/quote matching in bash (C/yacc) vs Parable (Python).

---

## Executive Summary

Bash uses a **delegation architecture** with specialized functions for each context. Parable uses a **flat state machine** with inline conditionals. The function names and top-level call graph are aligned, but the implementations diverge significantly.

| Aspect | Bash | Parable |
|--------|------|---------|
| Quote handling | Delegate to `skip_single_quoted()`, `skip_double_quoted()` | Inline `in_single`/`in_double` toggles |
| `${...}` parsing | `dolbrace_state` machine (5 states) | Simple depth counter |
| Parser/expander split | `parse.y` and `subst.c` have parallel implementations | Single implementation |
| Multibyte | `ADVANCE_CHAR` macro throughout | Not handled |

---

## Function Call Graph

### Bash

```
parse.y:                              subst.c:
─────────                             ────────
parse_matched_pair()                  skip_matched_pair()
  ├─ parse_matched_pair() [recursive]   ├─ skip_single_quoted()
  ├─ parse_comsub()                     ├─ skip_double_quoted()
  └─ xparse_dolparen()                  │    ├─ extract_command_subst()
                                        │    └─ extract_dollar_brace_string()
                                        ├─ extract_delimited_string()
                                        └─ extract_dollar_brace_string()
                                             ├─ skip_single_quoted()
                                             ├─ skip_double_quoted()
                                             ├─ extract_command_subst()
                                             └─ skipsubscript()

skipsubscript() → skip_matched_pair()
```

### Parable

```
parable.py:
───────────
_skip_matched_pair()
  ├─ _find_cmdsub_end()
  │    ├─ _find_cmdsub_end() [recursive]
  │    ├─ _skip_backtick()
  │    └─ _skip_heredoc()
  └─ _find_braced_param_end()
       ├─ _find_cmdsub_end()
       └─ _find_braced_param_end() [recursive]

_skip_subscript() → _skip_matched_pair()
```

---

## Detailed Function Comparison

### 1. `skip_matched_pair()` / `_skip_matched_pair()`

**Purpose:** Skip from `[` to matching `]` (or other bracket pairs), handling nested constructs.

#### Bash (`subst.c:2086-2177`, 91 lines)

```c
skip_matched_pair (const char *string, int start, int open, int close, int flags)
{
  int pass_next, backq, c, count;
  // ...
  while (c = string[i])
    {
      if (pass_next) { pass_next = 0; ADVANCE_CHAR(...); continue; }
      else if ((flags & 1) == 0 && c == '\\') { pass_next = 1; i++; continue; }
      else if (backq) { if (c == '`') backq = 0; ADVANCE_CHAR(...); continue; }
      else if ((flags & 1) == 0 && c == '`') { backq = 1; i++; continue; }
      else if ((flags & 1) == 0 && c == open) { count++; i++; continue; }
      else if (c == close) { count--; if (count == 0) break; i++; continue; }
      // DELEGATION to quote handlers:
      else if ((flags & 1) == 0 && (c == '\'' || c == '"'))
        {
          i = (c == '\'') ? skip_single_quoted(string, slen, ++i, 0)
                          : skip_double_quoted(string, slen, ++i, 0);
        }
      // DELEGATION to extraction functions:
      else if ((flags & 1) == 0 && c == '$' && (string[i+1] == LPAREN || string[i+1] == LBRACE))
        {
          si = i + 2;
          if (string[i+1] == LPAREN)
            temp = extract_delimited_string(string, &si, "$(", "(", ")", SX_NOALLOC|SX_COMMAND);
          else
            temp = extract_dollar_brace_string(string, &si, 0, SX_NOALLOC);
          i = si;
        }
      else
        ADVANCE_CHAR(string, slen, i);
    }
}
```

**Key characteristics:**
- Delegates quote handling to separate functions
- Each delegated function handles its own escapes/expansions
- `ADVANCE_CHAR` macro for multibyte safety
- Returns position after examining all characters

#### Parable (`parable.py:6296-6380`, 84 lines)

```python
def _skip_matched_pair(s: str, start: int, open: str, close: str, flags: int = 0) -> int:
    # State variables instead of delegation
    pass_next = False
    in_single = False
    in_double = False
    backq = False

    while i < n and depth > 0:
        c = s[i]
        if pass_next: pass_next = False; i += 1; continue
        if not literal and c == "\\": pass_next = True; i += 1; continue
        if backq:
            if c == "`": backq = False
            i += 1; continue
        if not literal and c == "`": backq = True; i += 1; continue
        # INLINE quote handling (not delegated):
        if not literal and c == "'" and not in_double:
            in_single = not in_single; i += 1; continue
        if not literal and c == '"' and not in_single:
            in_double = not in_double; i += 1; continue
        # Expansion handling inside double quotes:
        if in_double:
            if c == "$" and i + 1 < n:
                if s[i + 1] == "(": i = _find_cmdsub_end(s, i + 2); continue
                if s[i + 1] == "{": i = _find_braced_param_end(s, i + 2); continue
        # Expansion handling outside quotes:
        if not literal and not in_single and not in_double and c == "$" and i + 1 < n:
            if s[i + 1] == "(": i = _find_cmdsub_end(s, i + 2); continue
            if s[i + 1] == "{": i = _find_braced_param_end(s, i + 2); continue
        # Bracket counting:
        in_quotes = in_single or in_double
        if not literal and not in_quotes and c == open: depth += 1
        elif not in_quotes and c == close: depth -= 1
        i += 1
```

**Key differences:**
- **Inline quote state** vs delegation to specialized functions
- **No multibyte handling** (assumes single-byte characters)
- **Separate code paths** for `in_double` vs unquoted expansions
- Boolean toggles can't handle edge cases that bash's delegated functions do

---

### 2. `skip_double_quoted()` (Bash only)

**Purpose:** Skip from opening `"` to closing `"`, handling expansions within.

#### Bash (`subst.c:1014-1080`, 66 lines)

```c
skip_double_quoted (const char *string, size_t slen, size_t sind, int flags)
{
  int pass_next, backquote;
  // ...
  while (c = string[i])
    {
      if (pass_next) { pass_next = 0; ADVANCE_CHAR(...); continue; }
      else if (c == '\\') { pass_next++; i++; continue; }
      else if (backquote) { if (c == '`') backquote = 0; ADVANCE_CHAR(...); continue; }
      else if (c == '`') { backquote++; i++; continue; }
      else if (c == '$' && ((string[i+1] == LPAREN) || (string[i+1] == LBRACE)))
        {
          si = i + 2;
          if (string[i+1] == LPAREN)
            ret = extract_command_subst(string, &si, SX_NOALLOC|(flags&SX_COMPLETE));
          else if (string[i+1] == LBRACE && FUNSUB_CHAR(string[si]))
            ret = extract_function_subst(string, &si, Q_DOUBLE_QUOTES, ...);
          else
            ret = extract_dollar_brace_string(string, &si, Q_DOUBLE_QUOTES, ...);
          i = si + 1;
          continue;
        }
      else if (c != '"')
        { ADVANCE_CHAR(...); continue; }
      else
        break;  // found closing quote
    }
  if (c) i++;
  return (i);
}
```

**This function is self-contained:** it handles its own escapes, backticks, and delegates to extraction functions for `$()` and `${}`. When bash's `skip_matched_pair` delegates to this, it gets complete double-quote handling.

#### Parable equivalent

**None.** Parable handles double quotes inline in `_skip_matched_pair` with:
```python
if not literal and c == '"' and not in_single:
    in_double = not in_double
```

This is a toggle, not a context-aware parser. The expansion handling is separate:
```python
if in_double:
    if c == "$" and i + 1 < n:
        if s[i + 1] == "(": i = _find_cmdsub_end(s, i + 2); continue
```

---

### 3. `extract_dollar_brace_string()` / `_find_braced_param_end()`

**Purpose:** Find the end of `${...}`, handling the complex parameter expansion syntax.

#### Bash (`subst.c:1825-2017`, 192 lines)

The critical feature is the **`dolbrace_state` state machine**:

```c
// parser.h:73-78
#define DOLBRACE_PARAM   0x01  // In parameter name: ${foo
#define DOLBRACE_OP      0x02  // In operator: ${foo:
#define DOLBRACE_WORD    0x04  // In word after operator: ${foo:-bar
#define DOLBRACE_QUOTE   0x40  // Single quotes are special: ${foo%...}
#define DOLBRACE_QUOTE2  0x80  // Single quotes are semi-special: ${foo/...}
```

State transitions:
```c
// After seeing parameter name, transition on operators:
if (dolbrace_state == DOLBRACE_PARAM && ch == '%' && retind > 1)
  dolbrace_state = DOLBRACE_QUOTE;      // ${param%word} - quotes special in word
else if (dolbrace_state == DOLBRACE_PARAM && ch == '#' && retind > 1)
  dolbrace_state = DOLBRACE_QUOTE;      // ${param#word}
else if (dolbrace_state == DOLBRACE_PARAM && ch == '/' && retind > 1)
  dolbrace_state = DOLBRACE_QUOTE2;     // ${param/pat/rep} - slightly different
else if (dolbrace_state == DOLBRACE_PARAM && strchr("#%^,~:-=?+/", ch) != 0)
  dolbrace_state = DOLBRACE_OP;         // Generic operator
else if (dolbrace_state == DOLBRACE_OP && strchr("#%^,~:-=?+/", ch) == 0)
  dolbrace_state = DOLBRACE_WORD;       // Word after operator
```

This affects single-quote handling:
```c
if (c == '\'')
  {
    // POSIX: single quotes in ${...} inside double quotes depend on context
    if (posixly_correct && shell_compatibility_level > 42 &&
        dolbrace_state != DOLBRACE_QUOTE &&
        (quoted & (Q_HERE_DOCUMENT|Q_DOUBLE_QUOTES)))
      ADVANCE_CHAR(string, slen, i);  // Treat as literal
    else
      i = skip_single_quoted(string, slen, si, 0);  // Skip quoted region
  }
```

Also handles:
- Nested `${...}` with state stack `dbstate[]`
- Process substitution `<(...)` and `>(...)`
- Function substitution `${|...}`
- Array subscripts via `skipsubscript()`
- Heredoc special cases

#### Parable (`parable.py:5798-5832`, 34 lines)

```python
def _find_braced_param_end(value: str, start: int) -> int:
    depth = 1
    i = start
    quote = QuoteState()
    while i < len(value) and depth > 0:
        c = value[i]
        if c == "\\" and i + 1 < len(value) and not quote.single:
            i += 2; continue
        if c == "'" and not quote.double:
            quote.single = not quote.single; i += 1; continue
        if c == '"' and not quote.single:
            quote.double = not quote.double; i += 1; continue
        if quote.single or quote.double:
            i += 1; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return i + 1
        if c == "$" and i + 1 < len(value) and value[i + 1] == "(":
            i = _find_cmdsub_end(value, i + 2); continue
        if c == "$" and i + 1 < len(value) and value[i + 1] == "{":
            i = _find_braced_param_end(value, i + 2); continue
        i += 1
    return i
```

**Missing:**
- `dolbrace_state` machine (all 5 states)
- State stack for nested `${...}`
- Context-dependent single-quote handling
- Process substitution
- Function substitution
- Array subscript handling inside `${...}`
- `posixly_correct` / `shell_compatibility_level` interactions

---

### 4. `extract_delimited_string()` / `_find_cmdsub_end()`

**Purpose:** Find the end of `$(...)`, handling command syntax within.

#### Bash (`subst.c:1361-1527`, 166 lines)

```c
extract_delimited_string(const char *string, size_t *sindex,
                         char *opener, char *alt_opener, char *closer, int flags)
{
  int pass_character, nesting_level, in_comment;
  // ...
  while (nesting_level)
    {
      // Comment handling
      if (in_comment) { if (c == '\n') in_comment = 0; ADVANCE_CHAR(...); continue; }
      if ((flags & SX_COMMAND) && c == '#' &&
          (i == 0 || string[i-1] == '\n' || shellblank(string[i-1])))
        { in_comment = 1; ADVANCE_CHAR(...); continue; }

      if (pass_character) { pass_character = 0; ADVANCE_CHAR(...); continue; }
      if (c == CTLESC || c == '\\') { pass_character++; i++; continue; }

      // Nested command substitution
      if ((flags & SX_COMMAND) && string[i] == '$' && string[i+1] == LPAREN)
        { si = i + 2; t = extract_command_subst(string, &si, flags|SX_NOALLOC); i = si + 1; continue; }

      // Nested function substitution
      if ((flags & SX_COMMAND) && string[i] == '$' && string[i+1] == LBRACE && FUNSUB_CHAR(string[i+2]))
        { si = i + 2; t = extract_function_subst(string, &si, 0, flags|SX_NOALLOC); i = si + 1; continue; }

      // Nested opener
      if (STREQN(string + i, opener, len_opener))
        { si = i + len_opener; t = extract_delimited_string(string, &si, opener, alt_opener, closer, flags|SX_NOALLOC); i = si + 1; continue; }

      // Closer
      if (STREQN(string + i, closer, len_closer))
        { i += len_closer - 1; nesting_level--; if (nesting_level == 0) break; }

      // Backticks
      if (c == '`')
        { si = i + 1; t = string_extract(string, &si, "`", flags|SX_NOALLOC); i = si + 1; continue; }

      // DELEGATION to quote handlers
      if (c == '\'' || c == '"')
        {
          si = i + 1;
          i = (c == '\'') ? skip_single_quoted(string, slen, si, flags)
                          : skip_double_quoted(string, slen, si, flags);
          continue;
        }

      ADVANCE_CHAR(string, slen, i);
    }
}
```

#### Parable (`parable.py:5641-5795`, 154 lines)

Parable's `_find_cmdsub_end` is the most complete of its extraction functions:

```python
def _find_cmdsub_end(value: str, start: int) -> int:
    depth = 1
    quote = QuoteState()
    case_depth = 0
    in_case_patterns = False
    arith_depth = 0
    arith_paren_depth = 0

    while i < len(value) and depth > 0:
        # Escapes
        if c == "\\" and i + 1 < len(value) and not quote.single:
            i += 2; continue
        # Quote toggles (inline, not delegated)
        if c == "'" and not quote.double:
            quote.single = not quote.single; i += 1; continue
        if c == '"' and not quote.single:
            quote.double = not quote.double; i += 1; continue
        if quote.single: i += 1; continue
        if quote.double:
            # Handle $() inside double quotes
            if _starts_with_at(value, i, "$(") and not _starts_with_at(value, i, "$(("):
                j = _find_cmdsub_end(value, i + 2); i = j; continue
            i += 1; continue
        # Comments
        if c == "#" and arith_depth == 0 and (i == start or value[i-1] in " \t\n;|&()"):
            while i < len(value) and value[i] != "\n": i += 1
            continue
        # Here-strings
        if _starts_with_at(value, i, "<<<"):
            # ... skip here-string word ...
            continue
        # Arithmetic $((...))
        if _starts_with_at(value, i, "$(("):
            if _is_valid_arithmetic_start(value, i):
                arith_depth += 1; i += 3; continue
            j = _find_cmdsub_end(value, i + 2); i = j; continue
        # Backticks
        if c == "`":
            i = _skip_backtick(value, i); continue
        # Heredocs
        if arith_depth == 0 and _starts_with_at(value, i, "<<"):
            i = _skip_heredoc(value, i); continue
        # Case statement tracking
        if _starts_with_at(value, i, "case") and _is_word_boundary(value, i, 4):
            case_depth += 1; i += 4; continue
        # ... esac, in, ;; handling ...
        # Paren counting with case/arith awareness
        if c == "(":
            if not (in_case_patterns and case_depth > 0):
                if arith_depth > 0: arith_paren_depth += 1
                else: depth += 1
        elif c == ")":
            # Complex logic for case patterns vs grouping
            ...
        i += 1
```

**Parable handles more here than in other functions:**
- Comments
- Here-strings and heredocs
- Arithmetic expressions `$((...))` with inner paren tracking
- Case statements (keyword tracking, pattern `)` disambiguation)
- Backticks (delegated to `_skip_backtick`)

**Still missing vs bash:**
- Delegation to `skip_single_quoted`/`skip_double_quoted`
- `CTLESC` handling (bash internal quoting)
- Multibyte characters
- `SX_COMMAND` and other flag variations

---

### 5. `parse_matched_pair()` (parse.y)

**Purpose:** Parser-level bracket matching, used during lexical analysis.

#### Bash (`parse.y:3877-4208`, 331 lines)

This is the **parser's version** of the same logic, with important differences:

```c
parse_matched_pair (int qc, int open, int close, size_t *lenp, int flags)
{
  int count, dolbrace_state;
  // ...
  dolbrace_state = (flags & P_DOLBRACE) ? DOLBRACE_PARAM : 0;

  while (count)
    {
      ch = shell_getc(...);  // Read from input stream, not string

      // Comment handling
      if (tflags & LEX_INCOMMENT) { ... }
      if ((tflags & LEX_CKCOMMENT) && ch == '#' && ...) tflags |= LEX_INCOMMENT;

      // Backslash
      if (tflags & LEX_PASSNEXT) { ... }
      if (ch == '\\') tflags |= LEX_PASSNEXT;

      // dolbrace_state transitions (same as subst.c)
      if (flags & P_DOLBRACE)
        {
          if (dolbrace_state == DOLBRACE_PARAM && ch == '%' && retind > 1)
            dolbrace_state = DOLBRACE_QUOTE;
          // ... same state machine as extract_dollar_brace_string ...
        }

      // Single quote handling depends on dolbrace_state
      if (posixly_correct && shell_compatibility_level > 41 &&
          dolbrace_state != DOLBRACE_QUOTE && dolbrace_state != DOLBRACE_QUOTE2 &&
          (flags & P_DQUOTE) && (flags & P_DOLBRACE) && ch == '\'')
        // Treat single quote as literal

      // Recursive calls for nested constructs
      if (ch == '\'') nestret = parse_matched_pair(ch, ch, ch, &nestlen, rflags);
      if (ch == '"') nestret = parse_matched_pair(ch, ch, ch, &nestlen, rflags);
      if (ch == '`') nestret = parse_matched_pair(0, '`', '`', &nestlen, rflags);
      if (ch == '$' && peek == '(') nestret = parse_comsub(...);
      if (ch == '$' && peek == '{') nestret = parse_matched_pair(0, '{', '}', &nestlen, P_FIRSTCLOSE|P_DOLBRACE|rflags);
    }
}
```

**Key point:** Bash has **two parallel implementations** of the same logic:
1. `parse.y:parse_matched_pair()` - used during parsing (reads from input stream)
2. `subst.c:skip_matched_pair()` - used during expansion (operates on strings)

They share the `dolbrace_state` machine and must stay synchronized (see comments in both files).

#### Parable

**Single implementation** in `parable.py`. The parser doesn't have its own matched-pair logic; it relies on the same functions used elsewhere.

---

## The `dolbrace_state` Machine

This is the most significant architectural difference. Here's the full state machine:

```
                    ┌─────────────────────────────────────────────┐
                    │                                             │
                    v                                             │
              ┌──────────┐                                        │
  ${          │  PARAM   │──── #%^,~:-=?+/ ────>┌─────────┐       │
  ──────────>│          │                       │   OP    │       │
              └──────────┘                       └────┬────┘       │
                    │                                 │            │
                    │ % (after param)                 │ non-op     │
                    │ # (after param)                 v            │
                    │ ^ (after param)           ┌─────────┐        │
                    │ , (after param)           │  WORD   │────────┘
                    v                           └─────────┘
              ┌──────────┐
              │  QUOTE   │   Single quotes are special here
              └──────────┘
                    │
                    │ / (after param, for ${param/pat/rep})
                    v
              ┌──────────┐
              │ QUOTE2   │   Single quotes are semi-special
              └──────────┘
```

**Why this matters:**

```bash
# In DOLBRACE_PARAM state (just the name):
"${foo}"      # ' is literal if inside outer double quotes (POSIX)

# In DOLBRACE_QUOTE state (after % # ^ ,):
"${foo%'*'}"  # ' is a quote delimiter, matches pattern '*'

# In DOLBRACE_QUOTE2 state (after /):
"${foo/'x'/'y'}"  # ' is semi-special (complex rules)
```

Parable treats all positions in `${...}` the same, missing these distinctions.

---

## Architectural Implications

### 1. Composability

**Bash:** Each function is self-contained. `skip_double_quoted` handles everything inside double quotes. When `skip_matched_pair` delegates to it, it gets complete behavior.

**Parable:** Logic is spread across conditions in a single function. Adding a new case requires understanding the entire function's state.

### 2. Parser/Expander Consistency

**Bash:** Two implementations that must stay synchronized. Comments in both files reference each other. The `dolbrace_state` defines are shared via `parser.h`.

**Parable:** Single implementation, but may not match bash in all edge cases because it doesn't have the full state machine.

### 3. Testability

**Bash:** Each delegated function can be tested in isolation.

**Parable:** Testing requires constructing full input strings that exercise specific code paths.

### 4. Extension Points

**Bash:** Adding new syntax (like `${|...}` funsub) means adding a new extraction function and calling it from the right places.

**Parable:** Adding new syntax means adding more conditionals to existing functions.

---

## Specific Gaps

| Feature | Bash | Parable |
|---------|------|---------|
| `dolbrace_state` transitions | 5 states, complex rules | None |
| `posixly_correct` interactions | Affects quote handling | Not modeled |
| `shell_compatibility_level` | Affects quote handling | Not modeled |
| `${|...}` function substitution | Supported | Not handled |
| `<(...)` / `>(...)` process substitution | Supported in `${...}` | Not handled |
| Array subscripts in `${arr[i]}` | Via `skipsubscript()` | Not handled |
| `CTLESC` internal quoting | Throughout | Not applicable |
| Multibyte characters | `ADVANCE_CHAR` macro | Not handled |
| Heredoc in `${...}` | Special case function | Not handled |

---

## Recommendations

1. **Document the gaps** - The current implementation handles common cases but not POSIX edge cases around quotes in parameter expansions.

2. **Consider refactoring `_find_braced_param_end`** - Adding even a simplified `dolbrace_state` (just PARAM vs WORD) would catch many edge cases.

3. **Extract quote handling** - Moving to delegated `_skip_single_quoted`/`_skip_double_quoted` functions would:
   - Improve testability
   - Make behavior more predictable
   - Align more closely with bash's architecture

4. **Add targeted tests** - The `bugs.tests` file should include cases that exercise:
   - `${param%'pattern'}` (quotes in removal operators)
   - `${param/pat/rep}` with quotes
   - Nested `${...}` with different quote contexts
