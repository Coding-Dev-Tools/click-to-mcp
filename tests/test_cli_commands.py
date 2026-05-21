"""CLI-level tests for discover, serve, serve-http, serve-http-streamable commands.

Tests validation error paths and help output for commands that don't start
long-running servers. The blocking serve commands can only be tested for
their pre-server validation logic.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from click_to_mcp.cli import cli


class TestDiscoverCommand:
    """Tests for the 'discover' command."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_discover_exits_successfully(self, runner: CliRunner) -> None:
        """Discover should exit 0 and list CLIs."""
        result = runner.invoke(cli, ["discover"])
        assert result.exit_code == 0
        # Should mention how many CLIs found or the zero case
        assert "CLI" in result.output

    def test_discover_output_contains_usage_hint(self, runner: CliRunner) -> None:
        """Discover should include usage hints after listing."""
        result = runner.invoke(cli, ["discover"])
        assert result.exit_code == 0
        assert "click-to-mcp serve" in result.output

    def test_discover_help_contains_description(self, runner: CliRunner) -> None:
        """Discover --help should show command description."""
        result = runner.invoke(cli, ["discover", "--help"])
        assert result.exit_code == 0
        assert "List all installed" in result.output


class TestServeCommand:
    """Tests for the 'serve' command error paths (non-blocking validation only)."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_serve_no_name_no_all_fails(self, runner: CliRunner) -> None:
        """Serve with no CLI name and no --all should exit with error."""
        result = runner.invoke(cli, ["serve"])
        assert result.exit_code != 0
        assert "Error" in result.output
        assert "Specify a CLI name" in result.output

    def test_serve_invalid_name_fails(self, runner: CliRunner) -> None:
        """Serve with a non-existent CLI name should exit with error."""
        result = runner.invoke(cli, ["serve", "nonexistent-cli-xyz-999"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()
        assert "click-to-mcp discover" in result.output.lower()

    def test_serve_help_contains_description(self, runner: CliRunner) -> None:
        """Serve --help should show command description."""
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "stdio" in result.output.lower()


class TestServeHttpCommand:
    """Tests for the 'serve-http' command error paths (non-blocking validation only)."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_serve_http_no_name_no_all_fails(self, runner: CliRunner) -> None:
        """Serve-http with no CLI name and no --all should exit with error."""
        result = runner.invoke(cli, ["serve-http"])
        assert result.exit_code != 0
        assert "Error" in result.output
        assert "Specify a CLI name" in result.output

    def test_serve_http_invalid_name_fails(self, runner: CliRunner) -> None:
        """Serve-http with a non-existent CLI name should exit with error."""
        result = runner.invoke(cli, ["serve-http", "nonexistent-cli-xyz-999"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()
        assert "click-to-mcp discover" in result.output.lower()

    def test_serve_http_help_contains_description(self, runner: CliRunner) -> None:
        """Serve-http --help should show command description."""
        result = runner.invoke(cli, ["serve-http", "--help"])
        assert result.exit_code == 0
        assert "HTTP+SSE" in result.output


class TestServeHttpStreamableCommand:
    """Tests for 'serve-http-streamable' error paths (non-blocking validation only)."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_serve_http_streamable_no_name_no_all_fails(self, runner: CliRunner) -> None:
        """Serve-http-streamable with no CLI name and no --all should exit with error."""
        result = runner.invoke(cli, ["serve-http-streamable"])
        assert result.exit_code != 0
        assert "Error" in result.output
        assert "Specify a CLI name" in result.output

    def test_serve_http_streamable_invalid_name_fails(self, runner: CliRunner) -> None:
        """Serve-http-streamable with invalid name should exit with error."""
        result = runner.invoke(cli, ["serve-http-streamable", "nonexistent-cli-xyz-999"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()
        assert "click-to-mcp discover" in result.output.lower()

    def test_serve_http_streamable_help_contains_description(self, runner: CliRunner) -> None:
        """Serve-http-streamable --help should show Streamable HTTP description."""
        result = runner.invoke(cli, ["serve-http-streamable", "--help"])
        assert result.exit_code == 0
        assert "Streamable HTTP" in result.output


class TestDemoCommand:
    """Tests for the 'demo' and 'demo-http' command help text."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_demo_help(self, runner: CliRunner) -> None:
        """Demo --help should show description and no args required."""
        result = runner.invoke(cli, ["demo", "--help"])
        assert result.exit_code == 0
        assert "demo" in result.output.lower()

    def test_demo_http_help(self, runner: CliRunner) -> None:
        """Demo-http --help should show HTTP+SSE description."""
        result = runner.invoke(cli, ["demo-http", "--help"])
        assert result.exit_code == 0
        assert "HTTP+SSE" in result.output

    def test_demo_http_streamable_help(self, runner: CliRunner) -> None:
        """Demo-http-streamable --help should show Streamable HTTP description."""
        result = runner.invoke(cli, ["demo-http-streamable", "--help"])
        assert result.exit_code == 0
        assert "Streamable HTTP" in result.output
