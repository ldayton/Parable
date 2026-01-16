# QuoteState and ContextStack Rollout Plan

## Current State

**QuoteState** is used in ~10 functions but manual `in_single`/`in_double` tracking still exists in several complex functions.

**ContextStack** is instantiated in `Parser.__init__` (line 4670) but **never used**. Manual `case_depth`, `arith_depth`, `arith_paren_depth` tracking exists in 4 functions.

## Goal

Incrementally convert remaining manual tracking to use QuoteState and ContextStack, with each step passing all tests.

---

## Phase 1: Convert Simple Quote Tracking in Word Methods

### Step 1.1: `Word._double_ctlesc_smart` (~line 1191)

**Current:** Uses `in_double` variable
**Change:** Use `QuoteState()`
**Complexity:** Low - single quote variable

```
Verify: just test && just transpile && just test-js
Commit: refactor: use QuoteState in Word._double_ctlesc_smart
```

### Step 1.2: `Word._find_matching_paren` (~line 932)

**Current:** Inline quote handling (lines 940-954)
**Change:** Use `QuoteState()` for quote tracking
**Complexity:** Low - basic quote skip logic

```
Verify: just test && just transpile && just test-js
Commit: refactor: use QuoteState in Word._find_matching_paren
```

---

## Phase 2: Convert Complex Quote Tracking in Word Methods

### Step 2.1: `Word._strip_locale_string_dollars` (lines 768-887)

**Current:** 7 variables:
- `in_single_quote`, `in_double_quote`
- `brace_depth`, `bracket_depth`
- `brace_in_double_quote`, `brace_in_single_quote`
- `bracket_in_double_quote`

**Change:** Use nested QuoteState with push/pop for brace/bracket contexts:
```python
quote = QuoteState()  # Main context
# On entering ${:
quote.push()  # Save state, reset for brace content
# On entering [:
quote.push()  # Save state for bracket content
# On exiting:
quote.pop()
```

**Complexity:** High - requires careful testing of nested quote contexts

```
Verify: just test && just transpile && just test-js
Commit: refactor: use QuoteState with push/pop in Word._strip_locale_string_dollars
```

### Step 2.2: `Word._normalize_array_inner` (~lines 973-1152)

**Current:** `brace_depth`, `bracket_depth`, `dq_brace_depth`
**Change:** Use QuoteState for quote tracking within braces
**Complexity:** Medium

```
Verify: just test && just transpile && just test-js
Commit: refactor: use QuoteState in Word._normalize_array_inner
```

---

## Phase 3: Convert Module-Level Functions

### Step 3.1: `_lookahead_for_esac` (lines 3816-3852)

**Current:** Simple inline quote skip (lines 3826-3834)
**Change:** Use QuoteState for quote handling
**Complexity:** Low

```
Verify: just test && just transpile && just test-js
Commit: refactor: use QuoteState in _lookahead_for_esac
```

### Step 3.2: `_skip_heredoc` (~lines 4054-4150)

**Current:** Uses `paren_depth` and inline quote handling
**Change:** Use QuoteState for quote tracking
**Complexity:** Low-Medium

```
Verify: just test && just transpile && just test-js
Commit: refactor: use QuoteState in _skip_heredoc
```

---

## Phase 4: Wire Up ContextStack for Depth Tracking

### Step 4.1: Add depth tracking methods to ContextStack

Add helper methods to ParseContext/ContextStack:
```python
class ParseContext:
    # ... existing ...
    def inc_arith_paren(self) -> None:
        self.arith_paren_depth += 1
    def dec_arith_paren(self) -> None:
        if self.arith_paren_depth > 0:
            self.arith_paren_depth -= 1

class ContextStack:
    # ... existing ...
    def enter_case(self) -> None:
        self.get_current().case_depth += 1
    def exit_case(self) -> None:
        ctx = self.get_current()
        if ctx.case_depth > 0:
            ctx.case_depth -= 1
    def in_case(self) -> bool:
        return self.get_current().case_depth > 0
    # Similar for arithmetic...
```

**Complexity:** Low - just adding methods

```
Verify: just test && just transpile && just test-js
Commit: refactor: add depth tracking helpers to ContextStack
```

### Step 4.2: Use ContextStack in `Parser._parse_command_substitution` (lines 5436-5720)

**Current:** Manual `case_depth`, `arith_depth` tracking
**Change:** Use `self._ctx` methods

```
Verify: just test && just transpile && just test-js
Commit: refactor: use ContextStack in Parser._parse_command_substitution
```

### Step 4.3: Use ContextStack in `Parser._parse_word_internal` (~lines 5103-5400)

**Current:** Manual `bracket_depth`, `paren_depth`
**Change:** Use ContextStack for depth tracking

```
Verify: just test && just transpile && just test-js
Commit: refactor: use ContextStack in Parser._parse_word_internal
```

---

## Phase 5: Convert Remaining Parser Methods

### Step 5.1: `Parser._parse_for_arith` (lines 9217-9271)

**Current:** Manual `paren_depth`
**Change:** Use ContextStack
**Complexity:** Low

```
Verify: just test && just transpile && just test-js
Commit: refactor: use ContextStack in Parser._parse_for_arith
```

### Step 5.2: `Parser.parse_function` (~lines 9700-9784)

**Current:** Manual `brace_depth`
**Change:** Use ContextStack
**Complexity:** Low

```
Verify: just test && just transpile && just test-js
Commit: refactor: use ContextStack in Parser.parse_function
```

---

## Phase 6: Convert Word Method Depth Tracking

Note: Word methods don't have access to Parser's `self._ctx`. Options:
1. Pass ContextStack as parameter
2. Create local ContextStack instances
3. Keep local depth variables (simpler)

### Step 6.1: Evaluate approach for Word methods

Review which Word methods would benefit from ContextStack vs local variables.

Word methods with depth tracking:
- `_format_command_substitutions` - has `arith_depth`, `deprecated_arith_depth`, `arith_paren_depth`
- `_normalize_extglob_whitespace` - has `deprecated_arith_depth`
- `_strip_arith_line_continuations` - has `depth` for paren tracking

**Decision point:** These are string-processing methods, not parsing methods. Local depth variables may be more appropriate than ContextStack.

```
Verify: just test && just transpile && just test-js
Commit: docs: document Word method depth tracking approach
```

---

## Phase 7: Cleanup and Documentation

### Step 7.1: Remove unused ParseContext fields

After all conversions, check if any ParseContext fields are unused and remove them.

```
Verify: just test && just transpile && just test-js
Commit: cleanup: remove unused ParseContext fields
```

### Step 7.2: Add docstrings explaining the architecture

Document QuoteState and ContextStack usage patterns.

```
Verify: just test && just transpile && just test-js
Commit: docs: document QuoteState and ContextStack architecture
```

---

## Summary

| Phase | Steps | Focus |
|-------|-------|-------|
| 1 | 2 | Simple quote tracking in Word methods |
| 2 | 2 | Complex quote tracking (nested contexts) |
| 3 | 2 | Module-level functions |
| 4 | 3 | Wire up ContextStack |
| 5 | 2 | Parser method depth tracking |
| 6 | 1 | Evaluate Word method approach |
| 7 | 2 | Cleanup and docs |

**Total: 14 incremental commits**

## Test Commands

After each change:
```bash
just test && just transpile && just test-js
```

## Key Test Files

- `tests/parable/11_parameter_expansion.tests` - Quote handling in ${...}
- `tests/parable/14_arithmetic.tests` - Arithmetic expressions
- `tests/parable/09_case.tests` - Case statements
- `tests/parable/08_cmdsub.tests` - Command substitution
- `tests/parable/24_ansi_c_quoting.tests` - ANSI-C quotes in various contexts
