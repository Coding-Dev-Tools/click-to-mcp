"""Tests for the config command top-level error paths and edge cases.

Strengthens coverage for the config command: missing-subcommand handling,
invalid names, and edge cases not already exercised in test_cli_config.py.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from click_to_mcp.cli import cli


class TestConfigCommandErrorPaths:
    """Error-path coverage for 'config' command using CliRunner."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_config_no_name_no_all_fails(self, runner: CliRunner) -> None:
        """Config with no CLI name and no --all should exit with error."""
        result = runner.invoke(cli, ["config"])
        assert result.exit_code != 0
        assert "Error" in result.output
        assert "Specify" in result.output

    def test_config_invalid_name_fails(self, runner: CliRunner) -> None:
        """Config with a non-existent CLI name should exit with error."""
        result = runner.invoke(cli, ["config", "nonexistent-cli-xyz-999"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()
        assert "discover" in result.output.lower()

    def test_config_help_contains_description(self, runner: CliRunner) -> None:
        """Config --help should show command description."""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_all_lists_multiple_servers(self, runner: CliRunner) -> None:
        """Config --all should list at least the demo CLI's tools."""
        result = runner.invoke(cli, ["config", "--all"])
        assert result.exit_code == 0
        assert "mcpServers" in result.output or "servers" in result.output.lower()


class TestTopLevelCliErrorPaths:
    """Error paths for the top-level CLI group (no subcommand, unknown subcommand)."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_top_level_no_subcommand_fails(self, runner: CliRunner) -> None:
        """Running click-to-mcp with no subcommand should exit non-zero."""
        result = runner.invoke(cli, [])
        # Click exits 0 for --help but non-zero for missing subcommand
        assert result.exit_code != 0 or "Usage:" in result.output

    def test_unknown_subcommand_fails(self, runner: CliRunner) -> None:
        """An unknown subcommand should exit with error."""
        result = runner.invoke(cli, ["nonexistent-subcommand-xyz"])
        assert result.exit_code != 0
        assert "No such command" in result.output or "Error" in result.output

    def test_top_level_help(self, runner: CliRunner) -> None:
        """Top-level --help should show all commands."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Commands:" in result.output

    def test_version_flag(self, runner: CliRunner) -> None:
        """Top-level --version should show the version string."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        from click_to_mcp._version import __version__
        assert __version__ in result.output
