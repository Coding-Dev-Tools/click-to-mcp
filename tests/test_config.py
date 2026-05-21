"""Tests for the click-to-mcp config command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from click_to_mcp.cli import cli


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from text that may contain extra content."""
    decoder = json.JSONDecoder()
    start = text.index("{")
    obj, _ = decoder.raw_decode(text, start)
    return obj


class TestConfigCommand:
    """Test the config command that generates MCP client configuration."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_config_stdio_claude_desktop(self, runner: CliRunner) -> None:
        """Config with stdio transport generates correct Claude Desktop JSON."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo"])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        assert "mcpServers" in data
        assert "click-to-mcp-demo" in data["mcpServers"]
        server = data["mcpServers"]["click-to-mcp-demo"]
        assert server["command"] == "click-to-mcp"
        assert server["args"] == ["serve", "click-to-mcp-demo"]

    def test_config_cursor_client(self, runner: CliRunner) -> None:
        """Config with --client cursor generates correct format."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "cursor"])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        assert "mcpServers" in data
        assert "click-to-mcp-demo" in data["mcpServers"]

    def test_config_vscode_client(self, runner: CliRunner) -> None:
        """Config with --client vscode uses nested 'mcp.servers' format."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "vscode"])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        assert "mcp" in data
        assert "servers" in data["mcp"]
        assert "click-to-mcp-demo" in data["mcp"]["servers"]

    def test_config_http_transport(self, runner: CliRunner) -> None:
        """Config with --transport http uses URL instead of command."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo", "--transport", "http", "--port", "9000"
        ])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        server = data["mcpServers"]["click-to-mcp-demo"]
        assert "url" in server
        assert server["url"] == "http://127.0.0.1:9000/sse"
        assert "command" not in server

    def test_config_streamable_http_transport(self, runner: CliRunner) -> None:
        """Config with --transport streamable-http uses /message endpoint."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo", "--transport", "streamable-http", "--port", "8001"
        ])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        server = data["mcpServers"]["click-to-mcp-demo"]
        assert server["url"] == "http://127.0.0.1:8001/message"

    def test_config_custom_host(self, runner: CliRunner) -> None:
        """Config with --host uses custom host in URL."""
        result = runner.invoke(cli, [
            "config", "click-to-mcp-demo", "--transport", "http",
            "--host", "0.0.0.0", "--port", "3000"
        ])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        server = data["mcpServers"]["click-to-mcp-demo"]
        assert server["url"] == "http://0.0.0.0:3000/sse"

    def test_config_no_name_no_all_fails(self, runner: CliRunner) -> None:
        """Config without name or --all should fail."""
        result = runner.invoke(cli, ["config"])
        assert result.exit_code != 0

    def test_config_invalid_name_fails(self, runner: CliRunner) -> None:
        """Config with a non-existent CLI name should fail."""
        result = runner.invoke(cli, ["config", "nonexistent-cli-xyz123"])
        assert result.exit_code != 0

    def test_config_windsurf_client(self, runner: CliRunner) -> None:
        """Config with --client windsurf generates mcpServers format."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "windsurf"])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        assert "mcpServers" in data

    def test_config_cline_client(self, runner: CliRunner) -> None:
        """Config with --client cline generates mcpServers format."""
        result = runner.invoke(cli, ["config", "click-to-mcp-demo", "--client", "cline"])
        assert result.exit_code == 0
        data = _extract_json(result.output)
        assert "mcpServers" in data
