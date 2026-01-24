#!/usr/bin/env python3
"""Regression tests for command substitution inside arithmetic commands.

Issue #358: _arith_parse_cmdsub doesn't work with new Lexer architecture.
The parser was swapping source/pos/length but the Lexer still pointed to the
original source, causing CommandSubstitution.command to be None.
"""

import sys

sys.path.insert(0, "src")

from parable import parse


def test_dollar_paren_cmdsub_in_arith_command():
    """$(...) inside (( )) should have a parsed command."""
    result = parse("(( x = $(echo 1) ))")
    assert len(result) == 1
    arith = result[0]
    assert arith.kind == "arith-cmd"
    # Navigate to the CommandSubstitution node
    # expression is ArithAssign, value is CommandSubstitution
    assign = arith.expression
    assert assign.kind == "assign", f"Expected assign, got {assign.kind}"
    cmdsub = assign.value
    assert cmdsub.kind == "cmdsub", f"Expected cmdsub, got {cmdsub.kind}"
    assert cmdsub.command is not None, "CommandSubstitution.command should not be None"
    assert cmdsub.command.kind == "command", f"Expected command, got {cmdsub.command.kind}"


def test_backtick_cmdsub_in_arith_command():
    """`...` inside (( )) should have a parsed command."""
    result = parse("(( x = `echo 1` ))")
    assert len(result) == 1
    arith = result[0]
    assert arith.kind == "arith-cmd"
    assign = arith.expression
    assert assign.kind == "assign", f"Expected assign, got {assign.kind}"
    cmdsub = assign.value
    assert cmdsub.kind == "cmdsub", f"Expected cmdsub, got {cmdsub.kind}"
    assert cmdsub.command is not None, "CommandSubstitution.command should not be None"
    assert cmdsub.command.kind == "command", f"Expected command, got {cmdsub.command.kind}"


def test_nested_cmdsub_in_arith():
    """Nested command substitution in arithmetic."""
    result = parse("(( x = $(echo $(cat file)) ))")
    assert len(result) == 1
    arith = result[0]
    assign = arith.expression
    cmdsub = assign.value
    assert cmdsub.command is not None, "Outer cmdsub.command should not be None"
    # The inner command substitution is inside a word in the outer command
    outer_cmd = cmdsub.command
    assert outer_cmd.kind == "command"


def test_cmdsub_in_arith_expansion():
    """$(...) inside $((...)) arithmetic expansion should also work."""
    result = parse("echo $((1 + $(cat count)))")
    assert len(result) == 1
    cmd = result[0]
    # Find the arithmetic expansion in the word
    word = cmd.words[1]
    arith_part = None
    for part in word.parts:
        if part.kind == "arith":
            arith_part = part
            break
    assert arith_part is not None, "Should have arithmetic expansion part"
    # The expression is a binary-op, right side is cmdsub
    expr = arith_part.expression
    assert expr.kind == "binary-op", f"Expected binary-op, got {expr.kind}"
    cmdsub = expr.right
    assert cmdsub.kind == "cmdsub", f"Expected cmdsub, got {cmdsub.kind}"
    assert cmdsub.command is not None, "CommandSubstitution.command should not be None"
    # Verify the command content is correct (not parsed from wrong source)
    words = [w.value for w in cmdsub.command.words]
    assert words == ["cat", "count"], f"Expected ['cat', 'count'], got {words}"


def test_backtick_in_arith_expansion():
    """`...` inside $((...)) arithmetic expansion should also work."""
    result = parse("echo $((1 + `cat count`))")
    assert len(result) == 1
    cmd = result[0]
    word = cmd.words[1]
    arith_part = None
    for part in word.parts:
        if part.kind == "arith":
            arith_part = part
            break
    assert arith_part is not None
    expr = arith_part.expression
    assert expr.kind == "binary-op"
    cmdsub = expr.right
    assert cmdsub.kind == "cmdsub"
    assert cmdsub.command is not None, "CommandSubstitution.command should not be None"
    # Verify the command content is correct
    words = [w.value for w in cmdsub.command.words]
    assert words == ["cat", "count"], f"Expected ['cat', 'count'], got {words}"


if __name__ == "__main__":
    tests = [
        test_dollar_paren_cmdsub_in_arith_command,
        test_backtick_cmdsub_in_arith_command,
        test_nested_cmdsub_in_arith,
        test_cmdsub_in_arith_expansion,
        test_backtick_in_arith_expansion,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
    sys.exit(1 if failed else 0)
