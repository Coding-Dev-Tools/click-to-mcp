"""Tests for the click-to-mcp list-tools feature (adapter-based)."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from click_to_mcp.adapter import cli_to_mcp_tools
from click_to_mcp.cli import cli
from click_to_mcp.demo import cli as demo_cli


class TestListToolsAdapter:
    """Test the adapter's tool introspection — the core of the list-tools feature."""

    def test_demo_cli_has_calculate(self):
        tools = cli_to_mcp_tools(demo_cli)
        tool_names = [t.name for t in tools]
        assert any("calculate" in n for n in tool_names)

    def test_demo_cli_has_greet(self):
        tools = cli_to_mcp_tools(demo_cli)
        tool_names = [t.name for t in tools]
        assert any("greet" in n for n in tool_names)

    def test_tool_input_schema_has_type_object(self):
        tools = cli_to_mcp_tools(demo_cli)
        for tool in tools:
            assert tool.input_schema["type"] == "object"

    def test_required_params_marked(self):
        tools = cli_to_mcp_tools(demo_cli)
        # The calculate command should have required params (x, y)
        calc_tool = next((t for t in tools if "calculate" in t.name), None)
        assert calc_tool is not None
        assert len(calc_tool.input_schema.get("required", [])) >= 2

    def test_tool_names_are_valid_identifiers(self):
        """Tool names should be valid MCP tool names (no spaces)."""
        tools = cli_to_mcp_tools(demo_cli)
        for tool in tools:
            assert " " not in tool.name, f"Tool name '{tool.name}' contains spaces"

    def test_tool_descriptions_are_nonempty(self):
        tools = cli_to_mcp_tools(demo_cli)
        for tool in tools:
            assert tool.description.strip(), f"Tool '{tool.name}' has no description"

    def test_json_serializable_output(self):
        """Test that tool definitions can be serialized to JSON (for --json-output)."""
        tools = cli_to_mcp_tools(demo_cli, prefix="demo")
        output = []
        for tool in tools:
            output.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            })
        json_str = json.dumps(output, indent=2)
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        assert "name" in parsed[0]
        assert "input_schema" in parsed[0]

    def test_prefix_is_applied(self):
        """Prefixed tools should include the prefix in their name."""
        tools = cli_to_mcp_tools(demo_cli, prefix="myprefix")
        for tool in tools:
            assert tool.name.startswith("myprefix_"), f"Tool '{tool.name}' missing prefix"


class TestListToolsCli:
    """CLI-level tests for the list-tools command using CliRunner."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_list_tools_with_valid_name(self, runner: CliRunner) -> None:
        """list-tools with a known CLI name should exit 0 and show tool info."""
        result = runner.invoke(cli, ["list-tools", "click-to-mcp-demo"])
        assert result.exit_code == 0
        assert "Found 4 MCP tool(s)" in result.output
        assert "click_to_mcp_demo_greet" in result.output
        assert "click_to_mcp_demo_calculate" in result.output

    def test_list_tools_no_name_fails(self, runner: CliRunner) -> None:
        """list-tools with no CLI name or --all should exit with error."""
        result = runner.invoke(cli, ["list-tools"])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_list_tools_invalid_name_fails(self, runner: CliRunner) -> None:
        """list-tools with a non-existent CLI name should exit with error."""
        result = runner.invoke(cli, ["list-tools", "nonexistent-cli-xyz"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_list_tools_json_output(self, runner: CliRunner) -> None:
        """list-tools with --json-output should produce valid JSON."""
        result = runner.invoke(cli, ["list-tools", "click-to-mcp-demo", "--json-output"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 4
        assert parsed[0]["name"] == "click_to_mcp_demo_greet"
        assert "input_schema" in parsed[0]

    def test_list_tools_json_output_invalid_name(self, runner: CliRunner) -> None:
        """list-tools --json-output with invalid name should still fail gracefully."""
        result = runner.invoke(cli, ["list-tools", "nonexistent", "--json-output"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()
