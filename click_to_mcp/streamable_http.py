"""
MCP Server: Streamable HTTP transport for Click-based CLI tools.

A simpler HTTP transport without SSE (Server-Sent Events). Uses a single POST
/message endpoint for all MCP communication. No long-lived connections needed.

This is the "Streamable HTTP" transport pattern from the MCP spec — simpler
than the HTTP+SSE transport, compatible with more clients, and requires fewer
dependencies (only starlette + uvicorn, no sse-starlette).

Optional dependency — install with: pip install "click-to-mcp[http]"
"""

from __future__ import annotations

import json
import traceback
from typing import Any

from ._version import __version__
from .adapter import CliToolDef, cli_to_mcp_tools


def _check_http_deps() -> None:
    """Raise ImportError with helpful message if HTTP deps are missing."""
    missing = []
    try:
        import starlette  # noqa: F401
    except ImportError:
        missing.append("starlette")
    try:
        import uvicorn  # noqa: F401
    except ImportError:
        missing.append("uvicorn")
    if missing:
        raise ImportError(
            f"Streamable HTTP transport requires additional packages. "
            f"Install with: pip install 'click-to-mcp[http]' "
            f"(missing: {', '.join(missing)})"
        )


def serve_http_streamable(
    cli_group,
    name: str = "cli",
    description: str = "",
    prefix: str = "",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Start an MCP Streamable HTTP server that exposes a Click CLI as MCP tools.

    Unlike the HTTP+SSE transport, this uses a single POST endpoint with no
    SSE connection, making it simpler and compatible with more clients.

    Args:
        cli_group: A click.Group instance.
        name: Server name (used in initialize response).
        description: Server description.
        prefix: Optional prefix for tool names.
        host: Bind host address.
        port: Bind port number.
    """
    _check_http_deps()

    import uvicorn
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Route

    tools: list[CliToolDef] = cli_to_mcp_tools(cli_group, prefix=prefix)
    tool_map = {t.name: t for t in tools}

    mcp_tool_list = [
        {
            "name": t.name,
            "description": t.description,
            "inputSchema": t.input_schema,
        }
        for t in tools
    ]

    server_info = {
        "name": name,
        "version": __version__,
        "description": description or f"MCP server for {name}",
    }

    initialized = False

    def _make_jsonrpc_response(request_id: Any, result: Any = None, error: dict | None = None) -> dict:
        resp: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
        if error:
            resp["error"] = error
        else:
            resp["result"] = result
        return resp

    async def handle_message(request: Request) -> Response:
        """Single POST endpoint for all MCP messages."""
        nonlocal initialized

        body = await request.body()
        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            return JSONResponse(
                _make_jsonrpc_response(None, error={"code": -32700, "message": "Parse error"}),
                status_code=400,
            )

        # Support both single message and batch (array)
        messages = msg if isinstance(msg, list) else [msg]
        responses: list[dict] = []

        for single_msg in messages:
            req_id = single_msg.get("id")
            method = single_msg.get("method", "")
            params = single_msg.get("params", {})

            try:
                if method == "initialize":
                    initialized = True
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "streamableHttp": {},
                        },
                        "serverInfo": server_info,
                    }
                    responses.append(_make_jsonrpc_response(req_id, result))

                elif method == "ping":
                    # MCP spec: respond with empty result
                    responses.append(_make_jsonrpc_response(req_id, {}))

                elif method == "notifications/initialized":
                    # No response needed for notifications
                    pass

                elif method == "tools/list":
                    result = {"tools": mcp_tool_list}  # type: ignore[dict-item, list-item]
                    responses.append(_make_jsonrpc_response(req_id, result))

                elif method == "tools/call":
                    tool_name = params.get("name", "")
                    arguments = params.get("arguments", {})

                    if tool_name not in tool_map:
                        error = {
                            "code": -32602,
                            "message": f"Unknown tool: {tool_name}",
                        }
                        responses.append(_make_jsonrpc_response(req_id, error=error))
                        continue

                    tool = tool_map[tool_name]
                    try:
                        output = tool.handler(**arguments)
                        result = {
                            "content": [
                                {  # type: ignore[dict-item, list-item]
                                    "type": "text",
                                    "text": output,
                                }
                            ],
                            "isError": False,  # type: ignore[dict-item, list-item]
                        }
                        responses.append(_make_jsonrpc_response(req_id, result))
                    except Exception as e:
                        result = {
                            "content": [
                                {  # type: ignore[dict-item, list-item]
                                    "type": "text",
                                    "text": f"Error: {e}\n{traceback.format_exc()}",
                                }
                            ],
                            "isError": True,  # type: ignore[dict-item, list-item]
                        }
                        responses.append(_make_jsonrpc_response(req_id, result))

                else:
                    error = {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    }
                    responses.append(_make_jsonrpc_response(req_id, error=error))

            except Exception as e:
                error = {
                    "code": -32603,
                    "message": f"Internal error: {e}",
                }
                responses.append(_make_jsonrpc_response(req_id, error=error))

        if not responses:
            # Only notifications were sent — return 204
            return Response(status_code=204)

        # Return single response for single message, array for batch
        body_data = responses[0] if isinstance(msg, dict) else responses
        return JSONResponse(body_data)

    async def handle_health(request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse(
            {
                "status": "ok",
                "name": name,
                "tools": len(mcp_tool_list),
                "transport": "streamable-http",
            }
        )

    app = Starlette(
        routes=[
            Route("/message", endpoint=handle_message, methods=["POST"]),
            Route("/health", endpoint=handle_health),
        ],
    )

    print(
        f"click-to-mcp Streamable HTTP server starting: http://{host}:{port}",
        file=__import__("sys").stderr,
    )
    print(
        f"  Message endpoint: POST http://{host}:{port}/message",
        file=__import__("sys").stderr,
    )
    print(
        f"  Health check:     http://{host}:{port}/health",
        file=__import__("sys").stderr,
    )
    print(
        f"  Serving {len(mcp_tool_list)} tool(s) as '{name}'",
        file=__import__("sys").stderr,
    )
    print(
        "  Transport: Streamable HTTP (no SSE)",
        file=__import__("sys").stderr,
    )

    uvicorn.run(app, host=host, port=port, log_level="warning")
