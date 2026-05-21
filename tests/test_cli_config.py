"""CLI-level tests for the 'config' command.

Tests MCP client configuration generation across clients, transports,
and edge cases like --all and --copy flags.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from click_to_mcp.cli import cli


class TestConfigCli:
    """CLI-level tests for the config command using CliRunner."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_config_valid_cli_defaults(self, runner: CliRunner) -> None:
        """Config for a valid CLI with defaults (stdio, claude-desktop)."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert "mcpServers" in parsed
        assert "click-to-mcp-demo" in parsed["mcpServers"]
        svr = parsed["mcpServers"]["click-to-mcp-demo"]
        assert svr["command"] == "click-to-mcp"
        assert svr["args"] == ["serve", "click-to-mcp-demo"]

    def test_config_no_name_no_all_fails(self, runner: CliRunner) -> None:
        """Config with no CLI name and no --all should fail."""
        result = runner.invoke(cli, ["config"])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_config_invalid_name_fails(self, runner: CliRunner) -> None:
        """Config with a non-existent CLI name should fail."""
        result = runner.invoke(cli, ["config", "nonexistent-cli-xyz"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_config_client_cursor(self, runner: CliRunner) -> None:
        """Config with --client cursor should use cursor format."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "cursor"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert "mcpServers" in parsed

    def test_config_client_vscode(self, runner: CliRunner) -> None:
        """Config with --client vscode should use VS Code format."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "vscode"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert "mcp" in parsed
        assert "servers" in parsed["mcp"]
        assert "click-to-mcp-demo" in parsed["mcp"]["servers"]

    def test_config_transport_http(self, runner: CliRunner) -> None:
        """Config with --transport http should produce URL-based config."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo",
            "--transport", "http",
            "--host", "0.0.0.0",
            "--port", "9000",
        ])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        svr = parsed["mcpServers"]["click-to-mcp-demo"]
        assert "url" in svr
        assert svr["url"] == "http://0.0.0.0:9000/sse"

    def test_config_transport_streamable_http(self, runner: CliRunner) -> None:
        """Config with --transport streamable-http should use /message endpoint."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo",
            "--transport", "streamable-http",
            "--port", "8001",
        ])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        svr = parsed["mcpServers"]["click-to-mcp-demo"]
        assert "url" in svr
        assert svr["url"] == "http://127.0.0.1:8001/message"

    def test_config_client_windsurf(self, runner: CliRunner) -> None:
        """Config with --client windsurf should produce valid config."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "windsurf"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert "mcpServers" in parsed

    def test_config_client_cline(self, runner: CliRunner) -> None:
        """Config with --client cline should produce valid config."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "cline"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert "mcpServers" in parsed

    def test_config_json_is_parseable(self, runner: CliRunner) -> None:
        """Config output's JSON should be valid and parseable."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)
        assert len(parsed) > 0

    def test_config_includes_helpful_stderr(self, runner: CliRunner) -> None:
        """Config should emit helpful instructions on stderr."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo"])
        assert result.exit_code == 0
        assert "Add this to your" in result.stderr

    def test_config_case_insensitive_client(self, runner: CliRunner) -> None:
        """Config's --client option should be case-insensitive."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo",
            "--client", "CLAUDE-DESKTOP",
        ])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert "mcpServers" in parsed

    def test_config_case_insensitive_transport(self, runner: CliRunner) -> None:
        """Config's --transport option should be case-insensitive."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo",
            "--transport", "HTTP",
        ])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        svr = parsed["mcpServers"]["click-to-mcp-demo"]
        assert "url" in svr

    def test_config_copy_falls_back_to_stdout(self, runner: CliRunner) -> None:
        """Config --copy should either copy to clipboard or fall back to stdout."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--copy"])
        assert result.exit_code == 0
        # On Windows, 'clip' succeeds and prints success message.
        # On CI (Linux without xclip), it falls back to JSON on stdout.
        if "copied to clipboard" in result.stdout.lower():
            # Clipboard succeeded — verify stderr has instructions
            assert "Add this to your" in result.stderr
        else:
            # Fallback path — stdout should contain valid JSON
            parsed = json.loads(result.stdout)
            assert "mcpServers" in parsed

    def test_config_http_transport_stderr_note(self, runner: CliRunner) -> None:
        """Config with HTTP transport should include server-start note on stderr."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo",
            "--transport", "http",
        ])
        assert result.exit_code == 0
        assert "serve-http" in result.stderr
