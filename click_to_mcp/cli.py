"""click-to-mcp meta-CLI — discover and serve Click/typer CLIs as MCP servers.

Usage:
    click-to-mcp discover            # List all discoverable CLIs
    click-to-mcp serve <name>        # Serve a specific CLI (stdio)
    click-to-mcp serve --all         # Serve all discoverable CLIs (stdio)
    click-to-mcp serve-http <name>   # Serve a CLI over HTTP+SSE
    click-to-mcp demo                # Run the demo CLI as MCP server (stdio)
    click-to-mcp demo-http           # Run the demo CLI as HTTP+SSE server
"""

from __future__ import annotations

import sys

import click

from . import __version__, serve_stdio
from .discover import load_cli, scan_entry_points


@click.group()
@click.version_option(version=__version__, prog_name="click-to-mcp")
def cli() -> None:
    """Auto-wrap any Click/typer CLI as an MCP (Model Context Protocol) server."""
    pass


@cli.command()
def discover() -> None:
    """List all installed Click/typer CLIs that can be served as MCP tools."""
    clis = scan_entry_points()

    if not clis:
        click.echo("No Click/typer CLIs found in installed packages.")
        click.echo("Install a Click/typer-based CLI and run this command again.")
        return

    click.echo(f"Found {len(clis)} Click/typer CLI(s):")
    click.echo("")

    for i, cli_info in enumerate(clis, 1):
        type_tag = "[Typer]" if cli_info.is_typer else "[Click]"
        summary = cli_info.summary[:80] if cli_info.summary else "(no description)"
        click.echo(f"  {i}. {type_tag} {cli_info.name}")
        click.echo(f"       Package: {cli_info.package_name} {cli_info.package_version}")
        click.echo(f"       Module:  {cli_info.module_path}:{cli_info.attr_name}")
        click.echo(f"       Summary: {summary}")
        click.echo("")

    click.echo("Usage:  click-to-mcp serve <name>")
    click.echo("        click-to-mcp serve --all")


@cli.command()
@click.argument("name", required=False, default=None)
@click.option("--all", "serve_all", is_flag=True, help="Serve all discoverable CLIs")
def serve(name: str | None, serve_all: bool) -> None:
    """Serve a CLI as an MCP server over stdio.

    Specify a CLI NAME from 'click-to-mcp discover', or use --all.
    """
    if not name and not serve_all:
        click.echo("Error: Specify a CLI name or --all", err=True)
        sys.exit(1)

    if serve_all:
        clis = scan_entry_points()
        if not clis:
            click.echo("No CLIs found to serve.", err=True)
            sys.exit(1)
        # Serve the first one as primary — MCP stdio is single-server.
        # For --all we could eventually multiplex, but for now serve the first.
        click.echo(f"Multiple CLIs found. Serving the first one: {clis[0].name}", err=True)
        target_cli = load_cli(clis[0].name)
        if target_cli is None:
            click.echo(f"Error: Could not load CLI '{clis[0].name}'", err=True)
            sys.exit(1)
        serve_stdio(target_cli, name=clis[0].name)
        return

    target_cli = load_cli(name or "")
    if target_cli is None:
        click.echo(f"Error: CLI '{name}' not found.", err=True)
        click.echo("Run 'click-to-mcp discover' to see available CLIs.", err=True)
        sys.exit(1)

    serve_stdio(target_cli, name=name or "")


@cli.command()
@click.argument("name", required=False, default=None)
@click.option("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
@click.option("--port", default=8000, type=int, help="Port to bind (default: 8000)")
@click.option("--all", "serve_all", is_flag=True, help="Serve all discoverable CLIs")
def serve_http(name: str | None, host: str, port: int, serve_all: bool) -> None:
    """Serve a CLI as an MCP server over HTTP+SSE.

    Specify a CLI NAME from 'click-to-mcp discover', or use --all.
    Requires optional HTTP dependencies: pip install 'click-to-mcp[http]'
    """
    if not name and not serve_all:
        click.echo("Error: Specify a CLI name or --all", err=True)
        sys.exit(1)

    # Try to import HTTP deps early for a clear error message
    try:
        from .http_server import serve_http as _serve_http
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if serve_all:
        clis = scan_entry_points()
        if not clis:
            click.echo("No CLIs found to serve.", err=True)
            sys.exit(1)
        click.echo(f"Multiple CLIs found. Serving the first one: {clis[0].name}", err=True)
        target_cli = load_cli(clis[0].name)
        if target_cli is None:
            click.echo(f"Error: Could not load CLI '{clis[0].name}'", err=True)
            sys.exit(1)
        _serve_http(target_cli, name=clis[0].name, host=host, port=port)
        return

    target_cli = load_cli(name or "")
    if target_cli is None:
        click.echo(f"Error: CLI '{name}' not found.", err=True)
        click.echo("Run 'click-to-mcp discover' to see available CLIs.", err=True)
        sys.exit(1)

    _serve_http(target_cli, name=name or "", host=host, port=port)


@cli.command("list-tools")
@click.argument("name", required=False, default=None)
@click.option("--all", "list_all", is_flag=True, help="List tools from all discoverable CLIs")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON (for scripting/CI)")
def list_tools(name: str | None, list_all: bool, json_output: bool) -> None:
    """List the MCP tools that would be exposed from a CLI.

    Shows tool names, descriptions, and parameter schemas without starting
    a server. Useful for debugging, CI validation, and documentation.
    """
    import json as _json

    from .adapter import cli_to_mcp_tools

    if not name and not list_all:
        click.echo("Error: Specify a CLI name or --all", err=True)
        sys.exit(1)

    if list_all:
        clis = scan_entry_points()
        if not clis:
            click.echo("No CLIs found.", err=True)
            sys.exit(1)
        all_tools = []
        for cli_info in clis:
            target_cli = load_cli(cli_info.name)
            if target_cli is None:
                continue
            tools = cli_to_mcp_tools(target_cli, prefix=cli_info.name)
            all_tools.extend(tools)
    else:
        target_cli = load_cli(name or "")
        if target_cli is None:
            click.echo(f"Error: CLI '{name}' not found.", err=True)
            click.echo("Run 'click-to-mcp discover' to see available CLIs.", err=True)
            sys.exit(1)
        all_tools = cli_to_mcp_tools(target_cli, prefix=name or "")

    if not all_tools:
        click.echo("No MCP tools found for the specified CLI.", err=True)
        sys.exit(1)

    if json_output:
        output = []
        for tool in all_tools:
            output.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            })
        click.echo(_json.dumps(output, indent=2))
    else:
        click.echo(f"Found {len(all_tools)} MCP tool(s):")
        click.echo()
        for tool in all_tools:
            click.echo(f"  {tool.name}")
            click.echo(f"    {tool.description[:100]}")
            params = tool.input_schema.get("properties", {})
            required = tool.input_schema.get("required", [])
            if params:
                click.echo(f"    Parameters: {', '.join(params.keys())}")
                if required:
                    click.echo(f"    Required: {', '.join(required)}")
            click.echo()


@cli.command()
def demo() -> None:
    """Run the built-in demo CLI as an MCP server (stdio)."""
    from .demo import cli as demo_cli

    serve_stdio(demo_cli, name="click-to-mcp-demo")


@cli.command("demo-http")
@click.option("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
@click.option("--port", default=8000, type=int, help="Port to bind (default: 8000)")
def demo_http(host: str, port: int) -> None:
    """Run the built-in demo CLI as an HTTP+SSE MCP server.

    Requires optional HTTP dependencies: pip install 'click-to-mcp[http]'
    """
    try:
        from .http_server import serve_http as _serve_http
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    from .demo import cli as demo_cli

    _serve_http(demo_cli, name="click-to-mcp-demo", host=host, port=port)


@cli.command("serve-http-streamable")
@click.argument("name", required=False, default=None)
@click.option("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
@click.option("--port", default=8001, type=int, help="Port to bind (default: 8001)")
@click.option("--all", "serve_all", is_flag=True, help="Serve all discoverable CLIs")
def serve_http_streamable(name: str | None, host: str, port: int, serve_all: bool) -> None:
    """Serve a CLI as an MCP server over Streamable HTTP (no SSE).

    Uses a single POST /message endpoint — simpler than HTTP+SSE, compatible
    with more MCP clients. Default port is 8001 (different from serve-http).
    Requires: pip install 'click-to-mcp[http]'
    """
    if not name and not serve_all:
        click.echo("Error: Specify a CLI name or --all", err=True)
        sys.exit(1)

    try:
        from .streamable_http import serve_http_streamable as _serve
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if serve_all:
        clis = scan_entry_points()
        if not clis:
            click.echo("No CLIs found to serve.", err=True)
            sys.exit(1)
        click.echo(f"Multiple CLIs found. Serving the first one: {clis[0].name}", err=True)
        target_cli = load_cli(clis[0].name)
        if target_cli is None:
            click.echo(f"Error: Could not load CLI '{clis[0].name}'", err=True)
            sys.exit(1)
        _serve(target_cli, name=clis[0].name, host=host, port=port)
        return

    target_cli = load_cli(name or "")
    if target_cli is None:
        click.echo(f"Error: CLI '{name}' not found.", err=True)
        click.echo("Run 'click-to-mcp discover' to see available CLIs.", err=True)
        sys.exit(1)

    _serve(target_cli, name=name or "", host=host, port=port)


@cli.command("demo-http-streamable")
@click.option("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
@click.option("--port", default=8001, type=int, help="Port to bind (default: 8001)")
def demo_http_streamable(host: str, port: int) -> None:
    """Run the built-in demo CLI as a Streamable HTTP MCP server (no SSE).

    Requires: pip install 'click-to-mcp[http]'
    """
    try:
        from .streamable_http import serve_http_streamable as _serve
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    from .demo import cli as demo_cli

    _serve(demo_cli, name="click-to-mcp-demo", host=host, port=port)


@cli.command("config")
@click.argument("name", required=False, default=None)
@click.option("--client", "-c", type=click.Choice(
    ["claude-desktop", "cursor", "vscode", "windsurf", "cline"],
    case_sensitive=False,
), default="claude-desktop", help="MCP client to generate config for (default: claude-desktop)")
@click.option("--transport", "-t", type=click.Choice(
    ["stdio", "http", "streamable-http"],
    case_sensitive=False,
), default="stdio", help="Transport type (default: stdio)")
@click.option("--host", default="127.0.0.1", help="Host for HTTP transport (default: 127.0.0.1)")
@click.option("--port", default=8000, type=int, help="Port for HTTP transport (default: 8000; streamable-http: 8001)")
@click.option("--all", "config_all", is_flag=True, help="Generate config for all discoverable CLIs")
@click.option("--copy", "copy_to_clipboard", is_flag=True, help="Copy to clipboard instead of stdout")
def config(name: str | None, client: str, transport: str, host: str, port: int,
           config_all: bool, copy_to_clipboard: bool):
    """Generate MCP client configuration JSON.

    Prints the JSON snippet to add to your MCP client config file.
    Supports Claude Desktop, Cursor, VS Code Copilot, Windsurf, and Cline.

    Examples:
        click-to-mcp config my-cli
        click-to-mcp config my-cli --client cursor
        click-to-mcp config my-cli --transport http --port 9000
        click-to-mcp config --all --client vscode
    """
    import json as _json

    if not name and not config_all:
        click.echo("Error: Specify a CLI name or --all", err=True)
        sys.exit(1)

    # Collect CLI names
    cli_names: list[str] = []
    if config_all:
        clis = scan_entry_points()
        if not clis:
            click.echo("No CLIs found.", err=True)
            sys.exit(1)
        cli_names = [c.name for c in clis]
    else:
        # Verify the CLI exists
        target_cli = load_cli(name or "")
        if target_cli is None:
            click.echo(f"Error: CLI '{name}' not found.", err=True)
            click.echo("Run 'click-to-mcp discover' to see available CLIs.", err=True)
            sys.exit(1)
        cli_names = [name or ""]

    # Build MCP server configs
    server_configs: dict[str, dict] = {}
    for cli_name in cli_names:
        if transport == "stdio":
            server_configs[cli_name] = {
                "command": "click-to-mcp",
                "args": ["serve", cli_name],
            }
        elif transport == "http":
            server_configs[cli_name] = {
                "url": f"http://{host}:{port}/sse",
            }
        elif transport == "streamable-http":
            server_configs[cli_name] = {
                "url": f"http://{host}:{port}/message",
            }

    # Format output based on client
    client_key = client.lower()
    if client_key == "claude-desktop" or client_key == "cursor":
        output = {"mcpServers": server_configs}
    elif client_key == "vscode":
        # VS Code Copilot uses "inputs" and "servers" at top level
        output = {"mcp": {"servers": server_configs}}
    elif client_key == "windsurf" or client_key == "cline":
        output = {"mcpServers": server_configs}
    else:
        output = {"mcpServers": server_configs}

    output_json = _json.dumps(output, indent=2)

    if copy_to_clipboard:
        import subprocess as _sp
        try:
            platform_cmds = {
                "win32": ["clip"],
                "darwin": ["pbcopy"],
            }
            cmd = platform_cmds.get(sys.platform, ["xclip", "-selection", "clipboard"])
            proc = _sp.Popen(cmd, stdin=_sp.PIPE)
            proc.communicate(output_json.encode())
            if proc.returncode == 0:
                click.echo("Configuration copied to clipboard!")
            else:
                click.echo(output_json)
        except Exception:
            click.echo(output_json)
    else:
        click.echo(output_json)

    # Print helpful instructions
    click.echo("", err=True)
    config_paths = {
        "claude-desktop": "~/Library/Application Support/Claude/claude_desktop_config.json (macOS)\n  %APPDATA%\\Claude\\claude_desktop_config.json (Windows)",
        "cursor": ".cursor/mcp.json (in project root)",
        "vscode": ".vscode/mcp.json (in project root)",
        "windsurf": ".windsurf/mcp.json (in project root)",
        "cline": "~/.cline/mcp_config.json or via Cline settings",
    }
    click.echo(f"Add this to your {client} config file:", err=True)
    click.echo(f"  {config_paths.get(client_key, 'client config file')}", err=True)
    if transport != "stdio":
        transport_cmd = "serve-http-streamable" if transport == "streamable-http" else "serve-http"
        click.echo(f"\nNote: Start the server first: click-to-mcp {transport_cmd} {cli_names[0]} --port {port}", err=True)


def main() -> None:
    """Entry point for the click-to-mcp CLI."""
    cli()


if __name__ == "__main__":
    main()
