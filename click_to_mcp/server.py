"""
MCP Server: JSON-RPC over stdio for Click-based CLI tools.
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any

from ._version import __version__
from .adapter import CliToolDef, cli_to_mcp_tools


def _make_jsonrpc_response(request_id: Any, result: Any = None, error: dict | None = None) -> str:
    """Build a JSON-RPC 2.0 response."""
    resp: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error:
        resp["error"] = error
    else:
        resp["result"] = result
    return json.dumps(resp)


def serve_stdio(
    cli_group, name: str = "cli", description: str = "", prefix: str = "",
) -> None:
    """Start an MCP stdio server that exposes a Click CLI as MCP tools.

    Args:
        cli_group: A click.Group instance.
        name: Server name (used in initialize response).
        description: Server description.
        prefix: Optional prefix for tool names.
    """
    tools: list[CliToolDef] = cli_to_mcp_tools(cli_group, prefix=prefix)
    tool_map = {t.name: t for t in tools}

    # Build the tools list for MCP list_tools response
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

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        try:
            if method == "initialize":
                # Respond with capabilities
                response = _make_jsonrpc_response(req_id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": server_info,
                })
                sys.stdout.write(response + "\n")
                sys.stdout.flush()

            elif method == "tools/list":
                response = _make_jsonrpc_response(req_id, {
                    "tools": mcp_tool_list,
                })
                sys.stdout.write(response + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})

                if tool_name not in tool_map:
                    error = {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}",
                    }
                    response = _make_jsonrpc_response(req_id, error=error)
                    sys.stdout.write(response + "\n")
                    sys.stdout.flush()
                    continue

                tool = tool_map[tool_name]
                try:
                    output = tool.handler(**arguments)
                    # MCP tool result format
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": output,
                            }
                        ],
                        "isError": False,
                    }
                    response = _make_jsonrpc_response(req_id, result)
                except Exception as e:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: {e}\n{traceback.format_exc()}",
                            }
                        ],
                        "isError": True,
                    }
                    response = _make_jsonrpc_response(req_id, result)

                sys.stdout.write(response + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                # No response needed for notifications
                pass

            else:
                error = {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                }
                response = _make_jsonrpc_response(req_id, error=error)
                sys.stdout.write(response + "\n")
                sys.stdout.flush()

        except Exception as e:
            error = {
                "code": -32603,
                "message": f"Internal error: {e}",
            }
            response = _make_jsonrpc_response(req_id, error=error)
            sys.stdout.write(response + "\n")
            sys.stdout.flush()
