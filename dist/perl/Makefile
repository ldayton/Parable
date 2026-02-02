.PHONY: transpile check-syntax check

transpile:
	uv run --directory "$(TRANSPILER_DIR)" python -m src.tongues --target perl < "$(SOURCE_FILE)" > lib/parable.pl

check-syntax:
	perl -c lib/parable.pl

check:
	perl -Ilib bin/run_tests "$(TESTS_DIR)"
