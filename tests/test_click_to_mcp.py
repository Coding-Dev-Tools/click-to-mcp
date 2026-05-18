"""Proper pytest tests for click-to-mcp: adapter, server, and discover modules."""

from __future__ import annotations

import contextlib
import dataclasses
import json
import pytest
import subprocess
import sys
from click_to_mcp.adapter import CliToolDef, cli_to_mcp_tools
from click_to_mcp.demo import cli as demo_cli
from click_to_mcp.discover import DiscoveredCLI, find_our_clis, import_cli, scan_entry_points

# ---------------------------------------------------------------------------
# TestAdapter — unit tests for cli_to_mcp_tools with the demo CLI
# ---------------------------------------------------------------------------


class TestAdapter:
    """Test the adapter that converts Click commands to MCP tool definitions."""

    @pytest.fixture()
    def tools(self) -> list[CliToolDef]:
        """Build tool definitions from the demo CLI (no prefix)."""
        return cli_to_mcp_tools(demo_cli)

    @pytest.fixture()
    def prefixed_tools(self) -> list[CliToolDef]:
        """Build tool definitions from the demo CLI with prefix='demo'."""
        return cli_to_mcp_tools(demo_cli, prefix="demo")

    # -- tool count and names ------------------------------------------------

    def test_demo_cli_has_4_tools(self, tools: list[CliToolDef]) -> None:
        expected_names = {"greet", "calculate", "config_show", "config_set"}
        actual_names = {t.name for t in tools}
        assert actual_names == expected_names

    def test_tool_names_prefixed(self, prefixed_tools: list[CliToolDef]) -> None:
        expected_names = {"demo_greet", "demo_calculate", "demo_config_show", "demo_config_set"}
        actual_names = {t.name for t in prefixed_tools}
        assert actual_names == expected_names

    # -- schema details -------------------------------------------------------

    def test_greet_schema_has_required_name(self, tools: list[CliToolDef]) -> None:
        greet = next(t for t in tools if t.name == "greet")
        assert "name" in greet.input_schema.get("required", [])
        # 'name' is a positional argument so it must be required
        assert "name" in greet.input_schema["properties"]

    def test_calculate_has_choice_enum_for_operation(self, tools: list[CliToolDef]) -> None:
        calc = next(t for t in tools if t.name == "calculate")
        op_prop = calc.input_schema["properties"].get("operation")
        assert op_prop is not None, "calculate tool should have an 'operation' property"
        assert "enum" in op_prop, "operation property should have enum from click.Choice"
        assert set(op_prop["enum"]) == {"add", "sub", "mul", "div"}

    # -- handler invocation ---------------------------------------------------

    def test_handler_invocation_greet(self, tools: list[CliToolDef]) -> None:
        greet = next(t for t in tools if t.name == "greet")
        output = greet.handler(name="World", greeting="Hi", repeat=1)
        assert "Hi, World!" in output

    def test_handler_invocation_calculate(self, tools: list[CliToolDef]) -> None:
        calc = next(t for t in tools if t.name == "calculate")
        output = calc.handler(a=2, b=3, operation="add")
        assert "5.0" in output


# ---------------------------------------------------------------------------
# TestServer — integration tests via subprocess (JSON-RPC over stdio)
# ---------------------------------------------------------------------------


def _run_server(messages: list[dict], timeout: int = 15) -> list[dict]:
    """Send a sequence of JSON-RPC messages to the demo MCP server and return responses."""
    stdin_text = "\n".join(json.dumps(m) for m in messages)

    proc = subprocess.run(
        [
            sys.executable, "-c",
            "from click_to_mcp import serve_stdio; "
            "from click_to_mcp.demo import cli; "
            "serve_stdio(cli, name='click-to-mcp-demo')",
        ],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if proc.returncode != 0 and proc.stderr:
        pytest.fail(f"Server process failed (rc={proc.returncode}): {proc.stderr[:500]}")

    responses: list[dict] = []
    for line in proc.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        with contextlib.suppress(json.JSONDecodeError):
            responses.append(json.loads(line))
    return responses


class TestServer:
    """Test MCP server protocol end-to-end via subprocess stdio."""

    def test_initialize_response(self) -> None:
        responses = _run_server([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        ])
        assert len(responses) >= 1, "Expected at least one response"
        resp = responses[0]
        assert resp["id"] == 1
        result = resp["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "click-to-mcp-demo"

    def test_tools_list(self) -> None:
        responses = _run_server([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ])
        # Find the tools/list response (id=2)
        tools_resp = next((r for r in responses if r.get("id") == 2), None)
        assert tools_resp is not None, "No response for tools/list"
        tools = tools_resp["result"]["tools"]
        assert len(tools) >= 4, f"Expected >= 4 tools, got {len(tools)}"

    def test_tools_call_greet(self) -> None:
        responses = _run_server([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {
                    "name": "greet",
                    "arguments": {"name": "World", "greeting": "Hi", "repeat": 1},
                },
            },
        ])
        call_resp = next((r for r in responses if r.get("id") == 3), None)
        assert call_resp is not None, "No response for tools/call greet"
        result = call_resp["result"]
        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Hi, World!" in text

    def test_unknown_tool_returns_error(self) -> None:
        responses = _run_server([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "nonexistent", "arguments": {}},
            },
        ])
        call_resp = next((r for r in responses if r.get("id") == 2), None)
        assert call_resp is not None, "No response for tools/call nonexistent"
        assert "error" in call_resp, "Expected an error response for unknown tool"
        assert call_resp["error"]["code"] == -32602

    def test_notifications_initialized_returns_no_response(self) -> None:
        """The 'notifications/initialized' notification should produce no output."""
        responses = _run_server([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ])
        # Should have exactly 2 responses (initialize + tools/list, no response for notification)
        assert len(responses) == 2
        # First response should be initialize
        assert responses[0]["id"] == 1
        # Second response should be tools/list
        assert responses[1]["id"] == 2


# ---------------------------------------------------------------------------
# TestDiscover — tests for the discovery module
# ---------------------------------------------------------------------------


class TestDiscover:
    """Test the CLI discovery module."""

    def test_scan_entry_points_returns_list(self) -> None:
        result = scan_entry_points()
        # Should return a list without raising, even if no CLIs are installed
        assert isinstance(result, list)

    def test_discovered_cli_dataclass_fields(self) -> None:
        expected_fields = {
            "name", "module_path", "attr_name",
            "package_name", "package_version", "summary", "is_typer",
        }
        actual_fields = {f.name for f in dataclasses.fields(DiscoveredCLI)}
        assert actual_fields == expected_fields

    def test_import_cli_known_module(self) -> None:
        """import_cli should load a known module and return the correct object."""
        result = import_cli("click_to_mcp.demo", "cli")
        assert result is not None
        assert hasattr(result, "commands")
        assert "greet" in result.commands

    def test_import_cli_no_attr_falls_back(self) -> None:
        """import_cli with empty attr should try common conventions."""
        result = import_cli("click_to_mcp.demo", "")
        assert result is not None
        assert hasattr(result, "commands")

    def test_import_cli_nonexistent_module(self) -> None:
        """import_cli should return None for non-existent paths."""
        result = import_cli("nonexistent.module.xyz", "cli")
        assert result is None

    def test_import_cli_nonexistent_attr(self) -> None:
        """import_cli should return None for non-existent attributes."""
        result = import_cli("click_to_mcp.demo", "does_not_exist_12345")
        assert result is None

    def test_find_our_clis_returns_dict(self) -> None:
        """find_our_clis should return a dict (possibly empty)."""
        result = find_our_clis()
        assert isinstance(result, dict)
        # Should have at minimum click-to-mcp's own demo if nothing else
        # But more importantly it shouldn't crash

    def test_find_our_clis_values_are_callable_clis(self) -> None:
        """Values returned by find_our_clis should be valid CLI objects."""
        result = find_our_clis()
        # If we have any results, they should be click groups or typer apps
        for name, cli_obj in result.items():
            assert cli_obj is not None, f"CLI '{name}' resolved to None"
            # Should be a click.Group or have registered_commands (typer)
            assert hasattr(cli_obj, "commands") or hasattr(cli_obj, "registered_commands")
