# EOF Validation Test Plan

## Problem
Parable accepts unclosed constructs that bash rejects. 78 fuzzer cases.

## The Fix Pattern
```python
# BEFORE (broken):
while not self.at_end() and depth > 0:
    ...
# Loop exits, no validation

# AFTER (fixed):
while not self.at_end() and depth > 0:
    ...
if depth > 0:
    raise ParseError("unexpected EOF while looking for `X`", pos=start_pos)
```

---

## GUARDS (Read before each fix)

### Guard 1: No New Classes
- [ ] Am I about to create a new class? **STOP. Don't.**

### Guard 2: No New Methods
- [ ] Am I about to create a new method? **STOP.**
- [ ] If truly necessary: Will it be called in this same commit? If no, **don't create it.**

### Guard 3: No Special Cases
- [ ] Am I adding an `if` that handles one specific input? **STOP. Find the general fix.**

### Guard 4: Verify Before/After
- [ ] Before writing code: Does the input currently parse? (It should, incorrectly)
- [ ] After writing code: Does the input now error? (It must)
- [ ] If either check fails: **STOP. Understand why before proceeding.**

### Guard 5: Measurable Progress
- [ ] Run fuzzer before fix, count discrepancies
- [ ] Run fuzzer after fix, count discrepancies
- [ ] If count didn't decrease: **Revert. The fix didn't work.**

---

## Execution Process (Repeat for each fix)

### Step 1: Pick ONE Target
```bash
# Get a failing case
echo '@(' > /tmp/test.sh && parable /tmp/test.sh
# Expected: error
# Actual: (currently parses)
```

### Step 2: Find the Loop
```bash
# Search for the parsing code
rg "extglob" src/parable.py  # or whatever construct
```
- Identify the exact `while` loop
- Note the line number

### Step 3: Verify Current Behavior
```bash
echo '@(' | uv run python -c "
from parable import Parser
p = Parser('@(')
try:
    result = p.parse()
    print('PARSED:', result)  # Bad - should error
except Exception as e:
    print('ERROR:', e)  # Good
"
```
- If it already errors: **Wrong target. Pick another.**

### Step 4: Add ONE Validation
- Add `if depth > 0: raise ParseError(...)` after the loop
- **Nothing else. No refactoring. No cleanup.**

### Step 5: Verify Fix Works
```bash
# Same test as Step 3 - must now error
echo '@(' | uv run python -c "..."
```
- If still parses: **Fix is wrong. Debug before proceeding.**

### Step 6: Run Tests
```bash
just test
```
- All tests must pass
- If failures: **Revert and understand why**

### Step 7: Commit
```bash
git add src/parable.py && git commit -m "fix: error on unclosed X at EOF"
```

### Step 8: Measure
```bash
# Run fuzzer, compare discrepancy count to before
```

---

## Target List

From fuzzer analysis, these loops need EOF validation:

| Line | Construct | Test Input | Status |
|------|-----------|------------|--------|
| ~968 | Extglob `@(...)` | `@(` | [ ] |
| ~1149 | Nested extglob | `@(@(` | [ ] |
| ~1187 | `$(())` in extglob | `@($((` | [ ] |
| ~1796 | `${!prefix@}` | `${!x` | [ ] |
| ~1833 | `${var op}` | `${x#` | [ ] |
| ~2097 | Param arg | `${x/` | [ ] |
| ~7547 | Process sub | `<(` | [ ] |
| ~7648 | Arithmetic | `$((` | [ ] |
| ~9076 | Arith command | `((` | [ ] |

---

## Success Criteria

1. Each fix: exactly ONE `if depth > 0: raise` added
2. No new classes
3. No new methods
4. All 4535 tests pass after each fix
5. Fuzzer discrepancy count decreases after each fix
6. Final discrepancy count < 10 (down from 78)

---

## Abort Conditions

**Stop and ask for help if:**
- A fix breaks > 5 tests
- Can't find the right loop after 10 minutes
- The "fix" requires more than 5 lines of code
- Tempted to add a new class or method
