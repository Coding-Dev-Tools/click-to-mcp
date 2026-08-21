"""Non-object JSON-RPC payloads must not crash any transport (regression tests).

Previously a JSON body like ``[1, 2]``, ``"hello"`` or ``5`` reached
``msg.get(...)`` outside the per-request try/except, raising AttributeError:
the stdio server loop died entirely and the HTTP transports returned 500.
"""

from __future__ import annotations

import json
import threading
import time
from io import StringIO
from unittest.mock import patch

import httpx
import pytest

from click_to_mcp.demo import cli as demo_cli
from click_to_mcp.server import serve_stdio

INVALID_BODIES = ['[1, 2, 3]', '"hello"', "5", "null"]


class TestStdioInvalidPayloads:
    def _run(self, messages: list[str]) -> list[dict]:
        input_data = "\n".join(messages) + "\n"
        with patch("sys.stdin", StringIO(input_data)), patch(
            "sys.stdout", new_callable=StringIO
        ) as out:
            serve_stdio(demo_cli, name="test-cli", description="Test CLI")
            text = out.getvalue()
        return [json.loads(line) for line in text.strip().splitlines() if line.strip()]

    @pytest.mark.parametrize("body", INVALID_BODIES)
    def test_non_object_payload_gets_invalid_request_error(self, body: str) -> None:
        responses = self._run([body])
        assert len(responses) == 1
        assert responses[0]["error"]["code"] == -32600

    def test_server_survives_invalid_payload(self) -> None:
        """The loop must keep serving after a malformed payload."""
        valid = json.dumps({"jsonrpc": "2.0", "method": "ping", "id": 7})
        responses = self._run(["[1, 2]", valid])
        assert len(responses) == 2
        assert responses[1]["id"] == 7
        assert responses[1]["result"] == {}


def _start_server(target, port: int):
    thread = threading.Thread(
        target=target,
        args=(demo_cli,),
        kwargs={"name": "test-server", "host": "127.0.0.1", "port": port},
        daemon=True,
    )
    thread.start()
    client = httpx.Client(trust_env=False)
    for _ in range(20):
        try:
            if client.get(f"http://127.0.0.1:{port}/health", timeout=1).status_code == 200:
                return client
        except Exception:
            pass
        time.sleep(0.25)
    client.close()
    pytest.fail("server did not start")


class TestHttpInvalidPayloads:
    def test_http_sse_non_object_body(self) -> None:
        from click_to_mcp.http_server import serve_http

        client = _start_server(serve_http, 9931)
        try:
            for body in INVALID_BODIES:
                r = client.post("http://127.0.0.1:9931/messages", content=body)
                assert r.status_code == 400
                assert r.json()["error"]["code"] == -32600
        finally:
            client.close()

    def test_streamable_non_object_body(self) -> None:
        from click_to_mcp.streamable_http import serve_http_streamable

        client = _start_server(serve_http_streamable, 9932)
        try:
            for body in INVALID_BODIES + ['["a", 1]']:
                r = client.post("http://127.0.0.1:9932/message", content=body)
                assert r.status_code == 400
                assert r.json()["error"]["code"] == -32600
            # valid request still works afterwards
            r = client.post(
                "http://127.0.0.1:9932/message",
                json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            )
            assert r.status_code == 200
            assert r.json()["result"] == {}
        finally:
            client.close()
