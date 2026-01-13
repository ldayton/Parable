# Fuzzer

Differential fuzzer: mutates test corpus, compares Parable vs bash-oracle.

```bash
./fuzz.py -n 5000              # 5000 iterations
./fuzz.py -n 5000 --both-succeed   # only cases where both parse but differ
./fuzz.py -n 5000 -s 42 -o out.txt # reproducible, save results
```

Requires bash-oracle at `~/source/bash-oracle/bash-oracle`.
