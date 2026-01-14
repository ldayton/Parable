## Summary
- Fix command substitution formatting to treat even backslashes as non-escaping
- Add a fuzzer regression test for quoted command substitutions after backslashes

## Test plan
- [x] New test added to `tests/parable/36_fuzzer.tests`
- [x] `just check` passes
