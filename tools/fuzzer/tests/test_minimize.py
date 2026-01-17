"""Tests for the minimizer module."""

from unittest.mock import patch

from fuzzer.minimize import ddmin, is_interesting, minimize


class TestIsInteresting:
    """Tests for is_interesting discrepancy detection."""

    def test_both_error_not_interesting(self):
        """Both parsers error -> no discrepancy."""
        with (
            patch("fuzzer.minimize.run_parable", return_value=None),
            patch("fuzzer.minimize.run_oracle", return_value=None),
        ):
            assert is_interesting("test") is False

    def test_parable_errors_oracle_succeeds(self):
        """Parable errors, oracle succeeds -> discrepancy."""
        with (
            patch("fuzzer.minimize.run_parable", return_value=None),
            patch("fuzzer.minimize.run_oracle", return_value="(command)"),
        ):
            assert is_interesting("test") is True

    def test_parable_succeeds_oracle_errors(self):
        """Parable succeeds, oracle errors -> discrepancy."""
        with (
            patch("fuzzer.minimize.run_parable", return_value="(command)"),
            patch("fuzzer.minimize.run_oracle", return_value=None),
        ):
            assert is_interesting("test") is True

    def test_both_succeed_same_output(self):
        """Both succeed with same output -> no discrepancy."""
        with (
            patch("fuzzer.minimize.run_parable", return_value='(command (word "x"))'),
            patch("fuzzer.minimize.run_oracle", return_value='(command (word "x"))'),
        ):
            assert is_interesting("test") is False

    def test_both_succeed_different_output(self):
        """Both succeed with different output -> discrepancy."""
        with (
            patch("fuzzer.minimize.run_parable", return_value='(command (word "x"))'),
            patch("fuzzer.minimize.run_oracle", return_value='(command (word "y"))'),
        ):
            assert is_interesting("test") is True


class TestDdmin:
    """Tests for the delta debugging algorithm."""

    def test_ddmin_reduces_to_minimum(self):
        """ddmin should find the minimal failing input."""

        # Test function that fails if 'x' is in the input
        def has_x(chars):
            return "x" in chars

        result = ddmin(list("abcxdef"), has_x)
        assert "".join(result) == "x"

    def test_ddmin_multiple_required_chars(self):
        """ddmin finds minimal set when multiple chars required."""

        # Test function that fails if both 'a' AND 'b' are present
        def has_a_and_b(chars):
            return "a" in chars and "b" in chars

        result = ddmin(list("xxaxxbxx"), has_a_and_b)
        assert "a" in result and "b" in result
        assert len(result) == 2

    def test_ddmin_preserves_order(self):
        """ddmin preserves character order."""

        def check(chars):
            s = "".join(chars)
            return "ab" in s  # Must have 'ab' in order

        result = ddmin(list("xxabxx"), check)
        assert "".join(result) == "ab"

    def test_ddmin_single_char_input(self):
        """ddmin handles single character input."""

        def always_true(chars):
            return len(chars) > 0

        result = ddmin(list("x"), always_true)
        assert "".join(result) == "x"

    def test_ddmin_empty_result_not_possible(self):
        """ddmin never returns empty if test passes for non-empty."""

        def always_true(chars):
            return len(chars) > 0

        result = ddmin(list("abc"), always_true)
        assert len(result) >= 1


class TestMinimize:
    """Tests for the minimize function."""

    def test_minimize_not_interesting_returns_none(self):
        """minimize returns None if input isn't interesting."""
        with (
            patch("fuzzer.minimize.run_parable", return_value=None),
            patch("fuzzer.minimize.run_oracle", return_value=None),
        ):
            assert minimize("test") is None

    def test_minimize_reduces_input(self):
        """minimize reduces input to minimal discrepancy."""

        # Simulate: parable succeeds on anything with 'x', oracle always errors
        def mock_parable(text):
            return "(cmd)" if "x" in text else None

        def mock_oracle(text):
            return None  # Always errors

        with (
            patch("fuzzer.minimize.run_parable", side_effect=mock_parable),
            patch("fuzzer.minimize.run_oracle", side_effect=mock_oracle),
        ):
            result = minimize("abcxdef")
            assert result == "x"

    def test_minimize_timeout(self):
        """minimize respects timeout and returns None."""
        import time

        call_count = 0

        def slow_parable(text):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # Slow
            return "(cmd)" if "x" in text else None

        def slow_oracle(text):
            time.sleep(0.1)
            return None

        with (
            patch("fuzzer.minimize.run_parable", side_effect=slow_parable),
            patch("fuzzer.minimize.run_oracle", side_effect=slow_oracle),
        ):
            # Very short timeout
            result = minimize("a" * 100 + "x" + "b" * 100, timeout=0.3)
            # Should timeout and return None
            assert result is None

    def test_minimize_no_timeout(self):
        """minimize with timeout=None doesn't timeout."""

        def mock_parable(text):
            return "(cmd)" if "x" in text else None

        def mock_oracle(text):
            return None

        with (
            patch("fuzzer.minimize.run_parable", side_effect=mock_parable),
            patch("fuzzer.minimize.run_oracle", side_effect=mock_oracle),
        ):
            result = minimize("abcxdef", timeout=None)
            assert result == "x"

    def test_minimize_preserves_discrepancy_type(self):
        """minimize preserves the type of discrepancy."""

        # Both succeed but different output when 'xy' present
        def mock_parable(text):
            if "x" in text and "y" in text:
                return "(different)"
            return "(same)"

        def mock_oracle(text):
            return "(same)"

        with (
            patch("fuzzer.minimize.run_parable", side_effect=mock_parable),
            patch("fuzzer.minimize.run_oracle", side_effect=mock_oracle),
        ):
            result = minimize("aaxbbycc")
            assert result is not None
            assert "x" in result and "y" in result
