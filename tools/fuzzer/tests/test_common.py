"""Tests for common utilities."""

from fuzzer.common import normalize, run_oracle, run_parable


class TestRunOracle:
    """Tests for run_oracle function."""

    def test_simple_command(self):
        """run_oracle parses a simple command."""
        result = run_oracle("echo hello")
        assert result is not None
        assert "simple-command" in result or "command" in result

    def test_parse_error_returns_none(self):
        """run_oracle returns None on parse error."""
        result = run_oracle("echo 'unterminated")
        assert result is None

    def test_empty_input(self):
        """run_oracle handles empty input."""
        result = run_oracle("")
        # Empty input may return empty output or None depending on oracle
        # Just verify it doesn't crash
        assert result is None or isinstance(result, str)

    def test_multiline_input(self):
        """run_oracle handles multiline input."""
        result = run_oracle("echo one\necho two")
        assert result is not None

    def test_special_characters(self):
        """run_oracle handles special characters in input."""
        result = run_oracle("echo 'hello world'")
        assert result is not None

    def test_quotes_and_escapes(self):
        """run_oracle handles various quoting."""
        result = run_oracle('echo "hello $world"')
        assert result is not None

    def test_extglob_flag(self):
        """run_oracle passes extglob flag."""
        # Without extglob, @() is not special
        result_without = run_oracle("echo @(a|b)")
        # With extglob, @() is an extglob pattern
        result_with = run_oracle("echo @(a|b)", extglob=True)
        # Both should parse, but may produce different ASTs
        assert result_without is not None or result_with is not None

    def test_newlines_in_strings(self):
        """run_oracle handles newlines inside quoted strings."""
        result = run_oracle('echo "line1\nline2"')
        assert result is not None

    def test_null_bytes_in_input(self):
        """run_oracle handles input with null bytes gracefully."""
        result = run_oracle("echo \x00")
        # Should not crash, may return None or result
        assert result is None or isinstance(result, str)


class TestRunParable:
    """Tests for run_parable function."""

    def test_simple_command(self):
        """run_parable parses a simple command."""
        result = run_parable("echo hello")
        assert result is not None
        assert "simple-command" in result or "command" in result

    def test_parse_error_returns_none(self):
        """run_parable returns None on parse error."""
        result = run_parable("echo 'unterminated")
        assert result is None


class TestNormalize:
    """Tests for normalize function."""

    def test_collapses_whitespace(self):
        """normalize collapses multiple spaces."""
        assert normalize("a  b   c") == "a b c"

    def test_normalizes_redirects(self):
        """normalize removes explicit fd 1 from redirects."""
        assert normalize("1>") == ">"
        assert normalize("1>&") == ">&"

    def test_preserves_other_fds(self):
        """normalize preserves non-1 file descriptors."""
        assert "2>" in normalize("2>")
