"""Tests for the MCP stdio server (server.py) — the primary transport."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

from click_to_mcp._version import __version__
from click_to_mcp.demo import cli as demo_cli
from click_to_mcp.server import serve_stdio


def _jsonrpc(method: str, params: dict | None = None, req_id: int = 1) -> str:
    """Build a JSON-RPC 2.0 request line."""
    msg: dict = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)


class TestStdioServer:
    """Test the MCP stdio server JSON-RPC protocol handling."""

    def _run(self, messages: list[str]) -> list[dict]:
        """Feed messages to serve_stdio via patched stdin and collect responses."""
        input_data = "\n".join(messages) + "\n"
        with patch("sys.stdin", StringIO(input_data)), \
             patch("sys.stdout", new_callable=StringIO) as out:
            serve_stdio(demo_cli, name="test-cli", description="Test CLI")
            text = out.getvalue()
        return [json.loads(line) for line in text.strip().splitlines() if line.strip()]

    # -- initialize -----------------------------------------------------------

    def test_initialize_returns_server_info(self) -> None:
        responses = self._run([_jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test"},
        })])
        assert len(responses) == 1
        r = responses[0]
        assert r["id"] == 1
        assert r["result"]["protocolVersion"] == "2024-11-05"
        assert "tools" in r["result"]["capabilities"]
        assert r["result"]["serverInfo"]["name"] == "test-cli"

    # -- tools/list -----------------------------------------------------------

    def test_tools_list_returns_definitions(self) -> None:
        responses = self._run([
            _jsonrpc("initialize"),
            _jsonrpc("tools/list", req_id=2),
        ])
        tr = next(r for r in responses if r["id"] == 2)
        names = {t["name"] for t in tr["result"]["tools"]}
        assert "greet" in names
        assert "calculate" in names

    # -- tools/call -----------------------------------------------------------

    def test_tools_call_executes_handler(self) -> None:
        responses = self._run([
            _jsonrpc("initialize"),
            _jsonrpc("tools/call", {"name": "greet", "arguments": {"name": "World"}}, req_id=2),
        ])
        cr = next(r for r in responses if r["id"] == 2)
        assert cr["result"]["isError"] is False
        assert "World" in cr["result"]["content"][0]["text"]

    def test_tools_call_unknown_tool_returns_error(self) -> None:
        responses = self._run([
            _jsonrpc("initialize"),
            _jsonrpc("tools/call", {"name": "nonexistent"}, req_id=2),
        ])
        cr = next(r for r in responses if r["id"] == 2)
        assert cr["error"]["code"] == -32602

    def test_tools_call_handler_exception_returns_is_error(self) -> None:
        """Calling greet without required --name triggers handler RuntimeError."""
        responses = self._run([
            _jsonrpc("initialize"),
            _jsonrpc("tools/call", {"name": "greet", "arguments": {}}, req_id=2),
        ])
        cr = next(r for r in responses if r["id"] == 2)
        assert cr["result"]["isError"] is True
        assert "Error" in cr["result"]["content"][0]["text"]

    # -- error handling -------------------------------------------------------

    def test_unknown_method_returns_method_not_found(self) -> None:
        responses = self._run([_jsonrpc("foo/bar")])
        assert responses[0]["error"]["code"] == -32601

    def test_invalid_json_lines_ignored(self) -> None:
        responses = self._run([
            "not valid json{{{",
            _jsonrpc("initialize"),
        ])
        assert len(responses) == 1
        assert responses[0]["result"]["protocolVersion"] == "2024-11-05"

    def test_notification_initialized_no_response(self) -> None:
        responses = self._run([
            _jsonrpc("initialize"),
            '{"jsonrpc":"2.0","method":"notifications/initialized"}',
        ])
        # Only initialize should produce a response
        assert len(responses) == 1
        assert responses[0]["id"] == 1

    # -- multiple requests in sequence ----------------------------------------

    def test_full_mcp_handshake_and_tool_call(self) -> None:
        """Simulate a complete MCP client session."""
        responses = self._run([
            _jsonrpc("initialize"),
            '{"jsonrpc":"2.0","method":"notifications/initialized"}',
            _jsonrpc("tools/list", req_id=2),
            _jsonrpc("tools/call", {"name": "calculate", "arguments": {"a": 2, "b": 3, "operation": "add"}}, req_id=3),
        ])
        init = next(r for r in responses if r["id"] == 1)
        assert init["result"]["serverInfo"]["name"] == "test-cli"

        tools = next(r for r in responses if r["id"] == 2)
        assert len(tools["result"]["tools"]) >= 4

        call = next(r for r in responses if r["id"] == 3)
        assert call["result"]["isError"] is False
        assert "5" in call["result"]["content"][0]["text"]

    # -- version consistency -------------------------------------------------

    def test_initialize_reports_package_version(self) -> None:
        """The stdio server must report the actual package version, not a hardcoded string."""
        responses = self._run([_jsonrpc("initialize")])
        server_version = responses[0]["result"]["serverInfo"]["version"]
        assert server_version == __version__, (
            f"stdio server reports version {server_version!r}, "
            f"but package version is {__version__!r}"
        )
