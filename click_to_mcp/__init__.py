"""
click-to-mcp — Auto-wrap any Click/typer CLI as an MCP (Model Context Protocol) server.

Usage:
    pip install click-to-mcp
    click-to-mcp discover            # List all Click/typer CLIs
    click-to-mcp serve <name>        # Serve a specific CLI as MCP
    click-to-mcp serve --all         # Serve first discoverable CLI
    click-to-mcp demo                # Run built-in demo

Or use as a library:
    from click_to_mcp import run, serve_stdio, cli_to_mcp_tools
    from my_cli import app
    run(app, prefix="my-cli")
"""

from __future__ import annotations

from typing import Any

from ._version import __version__
from .adapter import CliToolDef, cli_to_mcp_tools
from .discover import DiscoveredCLI, find_our_clis, load_cli, scan_entry_points
from .server import serve_stdio


def _resolve_server_meta(app: Any, prefix: str = "", name: str = "") -> tuple[str, str, str]:
    """Extract server name and description from a Click/typer app.

    Args:
        app: A click.Group or typer.Typer instance.
        prefix: Optional tool name prefix.
        name: Optional server name (overrides auto-detection).

    Returns:
        Tuple of (name, description, prefix).
    """
    if not name:
        name = getattr(app, "name", None) or "cli"
    desc = ""
    if hasattr(app, "info"):
        info_desc = getattr(app.info, "help", None)
        if info_desc and "DefaultPlaceholder" not in str(type(info_desc)):
            desc = str(info_desc)
    if not desc:
        desc = getattr(app, "help", None) or ""
    if not isinstance(desc, str):
        desc = str(desc) if desc else ""
    return name, desc, prefix


def run(app: Any, prefix: str = "", name: str = "") -> None:
    """High-level entry point: serve a Click/typer app as an MCP server over stdio.

    This is the primary API for integrating click-to-mcp into your CLI tool.
    Call it from your mcp subcommand or mcp_server.py module.

    Args:
        app: A click.Group or typer.Typer instance.
        prefix: Optional tool name prefix (e.g. 'acg' for api-contract-guardian).
        name: Optional server name (defaults to app name or 'cli').
    """
    name, desc, prefix = _resolve_server_meta(app, prefix, name)
    serve_stdio(
        app,
        name=name,
        description=desc,
        prefix=prefix,
    )


def run_http(app: Any, prefix: str = "", name: str = "",
             host: str = "127.0.0.1", port: int = 8000) -> None:
    """High-level entry point: serve a Click/typer app as an MCP server over HTTP+SSE.

    Requires optional dependencies: pip install 'click-to-mcp[http]'

    Args:
        app: A click.Group or typer.Typer instance.
        prefix: Optional tool name prefix.
        name: Optional server name (defaults to app name or 'cli').
        host: Host to bind (default: 127.0.0.1).
        port: Port to bind (default: 8000).
    """
    from .http_server import serve_http

    name, desc, prefix = _resolve_server_meta(app, prefix, name)
    serve_http(
        app,
        name=name,
        description=desc,
        prefix=prefix,
        host=host,
        port=port,
    )


def run_http_streamable(app: Any, prefix: str = "", name: str = "",
                        host: str = "127.0.0.1", port: int = 8001) -> None:
    """High-level entry point: serve a Click/typer app as an MCP Streamable HTTP server.

    Uses a single POST /message endpoint — no SSE required. Simpler than the
    HTTP+SSE transport, compatible with more MCP clients.

    Requires optional dependencies: pip install 'click-to-mcp[http]'

    Args:
        app: A click.Group or typer.Typer instance.
        prefix: Optional tool name prefix.
        name: Optional server name (defaults to app name or 'cli').
        host: Host to bind (default: 127.0.0.1).
        port: Port to bind (default: 8001).
    """
    from .streamable_http import serve_http_streamable

    name, desc, prefix = _resolve_server_meta(app, prefix, name)
    serve_http_streamable(
        app,
        name=name,
        description=desc,
        prefix=prefix,
        host=host,
        port=port,
    )


__all__ = [
    "__version__",
    "cli_to_mcp_tools", "CliToolDef", "serve_stdio", "run", "run_http",
    "run_http_streamable",
    "scan_entry_points", "load_cli", "find_our_clis", "DiscoveredCLI",
]
