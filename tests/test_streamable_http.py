"""Tests for click-to-mcp Streamable HTTP transport (no SSE)."""

from __future__ import annotations

import threading
import time
from collections.abc import Generator

import httpx
import pytest

from click_to_mcp._version import __version__
from click_to_mcp.demo import cli as demo_cli

# ---------------------------------------------------------------------------
# TestStreamableHTTP — integration tests via HTTP client
# ---------------------------------------------------------------------------


def _start_server(port: int = 9877) -> Generator[None, None, None]:
    """Start the demo Streamable HTTP server in a background thread for testing."""
    from click_to_mcp.streamable_http import serve_http_streamable

    thread = threading.Thread(
        target=serve_http_streamable,
        args=(demo_cli,),
        kwargs={"name": "test-server", "host": "127.0.0.1", "port": port},
        daemon=True,
    )
    thread.start()
    # Wait for server to be ready
    for _ in range(20):
        try:
            resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1)
            if resp.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.25)
    else:
        pytest.fail("Streamable HTTP server did not start within 5 seconds")
    yield
    # Thread is daemon, will be cleaned up


@pytest.fixture(scope="module")
def streamable_server():
    """Module-scoped fixture that starts the server once."""
    yield from _start_server(port=9877)


@pytest.fixture()
def base_url() -> str:
    return "http://127.0.0.1:9877"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    """Test the health check endpoint."""

    def test_health_returns_ok(self, streamable_server, base_url: str) -> None:
        resp = httpx.get(f"{base_url}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["name"] == "test-server"
        assert data["tools"] >= 4
        assert data["transport"] == "streamable-http"


# ---------------------------------------------------------------------------
# Initialize
# ---------------------------------------------------------------------------


class TestInitialize:
    """Test MCP initialize handshake."""

    def test_initialize(self, streamable_server, base_url: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        result = data["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "test-server"
        assert "tools" in result["capabilities"]
        assert "streamableHttp" in result["capabilities"]

    def test_initialize_reports_package_version(self, streamable_server, base_url: str) -> None:
        """The streamable HTTP server must report the actual package version."""
        msg = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "initialize",
            "params": {},
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        server_version = resp.json()["result"]["serverInfo"]["version"]
        assert server_version == __version__, (
            f"streamable HTTP reports version {server_version!r}, "
            f"but package version is {__version__!r}"
        )


# ---------------------------------------------------------------------------
# Tools List
# ---------------------------------------------------------------------------


class TestToolsList:
    """Test tools/list."""

    def test_tools_list(self, streamable_server, base_url: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        data = resp.json()
        tools = data["result"]["tools"]
        assert len(tools) >= 4
        tool_names = {t["name"] for t in tools}
        assert "greet" in tool_names
        assert "calculate" in tool_names


# ---------------------------------------------------------------------------
# Tools Call
# ---------------------------------------------------------------------------


class TestToolsCall:
    """Test tools/call."""

    def test_call_greet(self, streamable_server, base_url: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "greet",
                "arguments": {"name": "World", "greeting": "Hi", "repeat": 1},
            },
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        data = resp.json()
        result = data["result"]
        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "Hi, World!" in text

    def test_call_calculate(self, streamable_server, base_url: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "calculate",
                "arguments": {"a": 10, "b": 3, "operation": "mul"},
            },
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        data = resp.json()
        result = data["result"]
        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert "30.0" in text

    def test_unknown_tool_returns_error(self, streamable_server, base_url: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "nonexistent",
                "arguments": {},
            },
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32602

    def test_unknown_method_returns_error(self, streamable_server, base_url: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "nonexistent/method",
            "params": {},
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32601

    def test_invalid_json_returns_parse_error(self, streamable_server, base_url: str) -> None:
        resp = httpx.post(
            f"{base_url}/message",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == -32700


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


class TestNotification:
    """Test that notifications return 204."""

    def test_notification_initialized(self, streamable_server, base_url: str) -> None:
        msg = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 204


class TestPing:
    """Test the MCP ping method over Streamable HTTP."""

    def test_ping_returns_empty_result(self, streamable_server, base_url: str) -> None:
        """MCP ping must return an empty result object."""
        msg = {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "ping",
            "params": {},
        }
        resp = httpx.post(f"{base_url}/message", json=msg)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 99
        assert data["result"] == {}
        assert "error" not in data

    def test_ping_in_batch(self, streamable_server, base_url: str) -> None:
        """Ping should work correctly in a batch request."""
        msgs = [
            {"jsonrpc": "2.0", "id": 50, "method": "ping", "params": {}},
            {"jsonrpc": "2.0", "id": 51, "method": "tools/list", "params": {}},
        ]
        resp = httpx.post(f"{base_url}/message", json=msgs)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        ping_resp = next(r for r in data if r["id"] == 50)
        assert ping_resp["result"] == {}


# ---------------------------------------------------------------------------
# Batch messages
# ---------------------------------------------------------------------------


class TestBatch:
    """Test batch message support."""

    def test_batch_messages(self, streamable_server, base_url: str) -> None:
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
        resp = httpx.post(f"{base_url}/message", json=msgs)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2


# ---------------------------------------------------------------------------
# Dep check
# ---------------------------------------------------------------------------


class TestDepCheck:
    """Test the dependency checker."""

    def test_check_deps_succeeds(self) -> None:
        from click_to_mcp.streamable_http import _check_http_deps
        # Should not raise since we installed deps
        _check_http_deps()
