.PHONY: transpile check-syntax check

transpile:
	mkdir -p lib
	uv run --directory "$(TRANSPILER_DIR)" python -m src.tongues --target lua < "$(SOURCE_FILE)" > lib/parable.lua

check-syntax:
	luac -p lib/parable.lua

check:
	lua -e "package.path='lib/?.lua;'..package.path" bin/run_tests "$(TESTS_DIR)"
