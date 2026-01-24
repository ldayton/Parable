---
name: verify-counts
description: Verify numerical claims in documentation are still accurate
---

Verify all count assertions in documentation against actual values.

## Claims to Verify

| Location | Claim | Verification |
|----------|-------|--------------|
| `README.md:17` | 11,000-line parser | Line count of parser source |
| `README.md:103` | 1,800+ hand-written tests | tests/parable/ test count |

## Verification Commands

**Parser line count:**
```bash
wc -l src/parable.py
```

**Hand-written test count:**
```bash
rg -c '^=== ' tests/parable/ | awk -F: '{sum += $2} END {print sum}'
```

## Output

Report each claim with:
- Documented value
- Actual value
- Status (PASS/FAIL/STALE)

### Status Criteria

- **PASS**: Actual value is within ~10% of documented value
- **STALE**: Claim is technically true but significantly outdated (e.g., "1,500" when actual is 1,849)
- **FAIL**: Claim is false

If any claim is STALE or FAIL, note which file(s) need updating.
