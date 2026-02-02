.PHONY: transpile check-syntax check

transpile:
	uv run --directory "$(TRANSPILER_DIR)" python -m src.tongues --target python < "$(SOURCE_FILE)" > src/parable/parable.py

check-syntax:
	python3 -m py_compile src/parable/parable.py

check:
	uv run parable-test "$(TESTS_DIR)"
