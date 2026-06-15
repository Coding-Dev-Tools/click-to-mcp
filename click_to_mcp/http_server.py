"""
MCP Server: HTTP+SSE transport for Click-based CLI tools.

Implements the MCP HTTP transport using Starlette + uvicorn + sse-starlette.
This allows web-based MCP clients to connect to Click CLIs over HTTP.

Optional dependency — install with: pip install "click-to-mcp[http]"
"""

from __future__ import annotations

import json
import traceback
from collections.abc import AsyncGenerator
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
    try:
        from sse_starlette.sse import EventSourceResponse  # noqa: F401
    except ImportError:
        missing.append("sse-starlette")
    if missing:
        raise ImportError(
            f"HTTP transport requires additional packages. "
            f"Install with: pip install 'click-to-mcp[http]' "
            f"(missing: {', '.join(missing)})"
        )


def serve_http(
    cli_group,
    name: str = "cli",
    description: str = "",
    prefix: str = "",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Start an MCP HTTP+SSE server that exposes a Click CLI as MCP tools.

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
    from sse_starlette.sse import EventSourceResponse
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


    def _make_jsonrpc_response(request_id: Any, result: Any = None, error: dict | None = None) -> dict:
        resp: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
        if error:
            resp["error"] = error
        else:
            resp["result"] = result
        return resp

    async def handle_sse(request: Request) -> EventSourceResponse:
        """SSE endpoint for server-to-client messages."""
        async def event_generator() -> AsyncGenerator:
            yield {
                "event": "endpoint",
                "data": "/messages?session_id=default",
            }

        return EventSourceResponse(event_generator())

    async def handle_messages(request: Request) -> Response:
        """Handle JSON-RPC messages over HTTP POST."""
        body = await request.body()
        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            return JSONResponse(
                _make_jsonrpc_response(None, error={"code": -32700, "message": "Parse error"}),
                status_code=400,
            )

        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": server_info,
                }
                return JSONResponse(_make_jsonrpc_response(req_id, result))

            elif method == "tools/list":
                result = {"tools": mcp_tool_list}  # type: ignore[dict-item, list-item]
                return JSONResponse(_make_jsonrpc_response(req_id, result))

            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})

                if tool_name not in tool_map:
                    error = {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}",
                    }
                    return JSONResponse(_make_jsonrpc_response(req_id, error=error))

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
                    return JSONResponse(_make_jsonrpc_response(req_id, result))
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
                    return JSONResponse(_make_jsonrpc_response(req_id, result))

            elif method == "ping":
                # MCP spec: respond with empty result
                result = {}
                return JSONResponse(_make_jsonrpc_response(req_id, result))

            elif method == "notifications/initialized":
                return Response(status_code=204)

            else:
                error = {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                }
                return JSONResponse(_make_jsonrpc_response(req_id, error=error))

        except Exception as e:
            error = {
                "code": -32603,
                "message": f"Internal error: {e}",
            }
            return JSONResponse(_make_jsonrpc_response(req_id, error=error))

    async def handle_health(request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "name": name,
            "tools": len(mcp_tool_list),
            "transport": "http+sse",
        })

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=handle_health),
        ],
    )

    print(f"click-to-mcp HTTP server starting: http://{host}:{port}", file=__import__("sys").stderr)
    print(f"  SSE endpoint:    http://{host}:{port}/sse", file=__import__("sys").stderr)
    print(f"  Messages:        POST http://{host}:{port}/messages", file=__import__("sys").stderr)
    print(f"  Health check:    http://{host}:{port}/health", file=__import__("sys").stderr)
    print(f"  Serving {len(mcp_tool_list)} tool(s) as '{name}'", file=__import__("sys").stderr)

    uvicorn.run(app, host=host, port=port, log_level="warning")
