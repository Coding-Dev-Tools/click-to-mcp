# click-to-mcp

[![GitHub stars](https://img.shields.io/github/stars/Coding-Dev-Tools/click-to-mcp?style=social)](https://github.com/Coding-Dev-Tools/click-to-mcp/stargazers)
[![PyPI](https://img.shields.io/pypi/v/click-to-mcp)](https://pypi.org/project/click-to-mcp/)
[![Open Source Alternative](https://img.shields.io/badge/Open_Source_Alternative-%E2%87%92-blue?logo=opensourceinitiative)](https://www.opensourcealternative.to/project/click-to-mcp)
[![LibHunt](https://img.shields.io/badge/LibHunt-%E2%87%92-blue?logo=codeigniter)](https://www.libhunt.com/r/Coding-Dev-Tools/click-to-mcp)
[![TensorBlock Awesome MCP](https://img.shields.io/badge/TensorBlock_Awesome_MCP-%E2%87%92-blue?logo=github)](https://github.com/TensorBlock/awesome-mcp-servers)
[![Punkpeye Awesome MCP](https://img.shields.io/badge/Punkpeye_Awesome_MCP-%E2%87%92-grey?logo=github)](https://github.com/punkpeye/awesome-mcp-servers)<!-- pending PR #6496 -->

Auto-wrap any [Click](https://click.palletsprojects.com/)/[typer](https://typer.tiangolo.com/) CLI as an [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) server.

> â­ **Star this repo** if you use MCP with Python CLIs â€” it helps others discover click-to-mcp!

Part of the [Revenue Holdings](https://coding-dev-tools.github.io/revenueholdings.dev/) developer tool ecosystem.

## Why?

AI coding agents (Claude Code, Codex, Cursor) use MCP to interact with tools. 
Instead of rewriting your CLI tools as MCP servers, use click-to-mcp to wrap them automatically.

Works great with [Revenue Holdings CLI tools](https://coding-dev-tools.github.io/revenueholdings.dev/) â€” wrap `api-contract-guardian`, `json2sql`, `deploydiff`, or `configdrift` as MCP servers with zero code changes.

## Quick Start

Install directly from GitHub (PyPI coming soon):

```bash
pip install git+https://github.com/Coding-Dev-Tools/click-to-mcp.git
```

Or install via Homebrew (macOS/Linux):
```bash
brew tap Coding-Dev-Tools/tap
brew install click-to-mcp
```

Or install via Scoop (Windows):
```bash
scoop bucket add Coding-Dev-Tools https://github.com/Coding-Dev-Tools/scoop-bucket
scoop install click-to-mcp
```

For HTTP+SSE transport (web-based MCP clients), install with the `http` extra:

```bash
pip install "click-to-mcp[http] @ git+https://github.com/Coding-Dev-Tools/click-to-mcp.git"
```

```bash
# Discover all Click/typer CLIs installed in your environment
click-to-mcp discover

# Serve a specific CLI as an MCP server (stdio transport)
click-to-mcp serve api-contract-guardian

# Serve over HTTP+SSE (for web-based MCP clients)
click-to-mcp serve-http api-contract-guardian --port 8000

# Or serve the built-in demo
click-to-mcp demo            # stdio
click-to-mcp demo-http       # HTTP+SSE on port 8000
```

Then configure your MCP client to connect via stdio or HTTP.

## How It Works

click-to-mcp introspects your Click/typer CLI at runtime and maps every command to an MCP tool:

| Click Concept | MCP Mapping |
|---|---|
| `@click.command()` | MCP tool |
| `@click.argument()` | Required input property |
| `@click.option()` | Optional input property with default |
| `click.Choice` | JSON Schema `enum` |
| `click.INT/FLOAT` | JSON Schema `integer`/`number` |
| `click.BOOL` / `is_flag` | JSON Schema `boolean` |
| Nested `click.Group` | Prefixed tools (e.g. `config_show`) |

No annotations, no decorators, no boilerplate. Your existing Click CLI *is* the MCP server.

## MCP Workflow with AI Coding Agents

This section shows how to integrate click-to-mcp with popular AI coding tools so your CLIs become first-class tools that AI agents can invoke directly.

### Claude Code

Add your CLI as an MCP server in your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "api-contract-guardian": {
      "command": "click-to-mcp",
      "args": ["serve", "api-contract-guardian"]
    },
    "json2sql": {
      "command": "click-to-mcp",
      "args": ["serve", "json2sql"]
    },
    "deploydiff": {
      "command": "click-to-mcp",
      "args": ["serve", "deploydiff"]
    }
  }
}
```

Now when you ask Claude Code to "validate my API contracts", it will automatically call the `acg_validate` MCP tool with the right arguments â€” no manual command-line invocation needed.

### Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "api-contract-guardian": {
      "command": "click-to-mcp",
      "args": ["serve", "api-contract-guardian"]
    }
  }
}
```

### Cline / VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "api-contract-guardian": {
      "command": "click-to-mcp",
      "args": ["serve", "api-contract-guardian"]
    }
  }
}
```

### Custom Integration (Programmatic)

For CLIs that aren't installed as entry points, use the library API:

```python
# my_mcp_server.py
from click_to_mcp import run
from my_cli import app  # Your Click/typer CLI

run(app, prefix="my-cli", name="my-cli-mcp")
```

Then reference the script directly:

```json
{
  "mcpServers": {
    "my-cli": {
      "command": "python",
      "args": ["my_mcp_server.py"]
    }
  }
}
```

### What the Agent Sees

When your MCP server is configured, the AI agent sees your CLI commands as native tools. For example, with api-contract-guardian:

```
Agent: "I need to validate the API contract against the staging server."
â†’ Calls MCP tool: acg_validate
  Arguments: { "spec_file": "openapi.yaml", "base_url": "https://staging.api.com", "strict": true, "output_format": "json" }
â† Result: "Validating openapi.yaml against https://staging.api.com...\nâœ“ All contracts pass"
```

The agent doesn't need to know shell syntax, argument flags, or command names. It just calls the tool with structured arguments, and click-to-mcp handles the rest.

## Examples

### Quick Start (3 lines)

```python
import click
from click_to_mcp import run

@click.group()
def my_cli():
    """My awesome CLI tool."""
    pass

@my_cli.command()
@click.argument("name")
@click.option("--loud", is_flag=True, help="Shout the greeting")
def hello(name: str, loud: bool):
    """Say hello to someone."""
    msg = f"Hello, {name}!"
    if loud:
        msg = msg.upper()
    click.echo(msg)

if __name__ == "__main__":
    run(my_cli, prefix="my-cli", name="my-cli-mcp")
```

See [examples/quick_start.py](examples/quick_start.py) for the full runnable example.

### Wrapping api-contract-guardian

See [examples/api_contract_guardian_mcp.py](examples/api_contract_guardian_mcp.py) for a demo showing how to wrap API Contract Guardian as an MCP server with `validate`, `extract`, and `monitor` commands.

## Usage

### CLI â€” Discover and Serve

```bash
# List all installed Click/typer CLIs
click-to-mcp discover

# Serve a specific CLI as an MCP server over stdio
click-to-mcp serve <name>

# Serve over HTTP+SSE (requires pip install "click-to-mcp[http]")
click-to-mcp serve-http <name> --port 8000

# Serve the built-in demo
click-to-mcp demo            # stdio
click-to-mcp demo-http       # HTTP+SSE

# Version info
click-to-mcp --version
```

### Library â€” Integrate directly

```python
# my_cli.py
import click
from click_to_mcp import serve_stdio

@click.group()
def cli():
    """My CLI tool."""
    pass

@cli.command()
@click.argument("file")
@click.option("--verbose", is_flag=True)
def validate(file: str, verbose: bool) -> None:
    """Validate a file."""
    click.echo(f"Validating {file}...")

# Run as MCP server
serve_stdio(cli, name="my-cli", description="My CLI as MCP server")
```

### Library â€” High-level `run()` API

```python
from click_to_mcp import run
from my_cli import app

# Automatically detects Click/typer instances
run(app, prefix="my-cli")
```

## Features

- **Auto-discovery**: `click-to-mcp discover` scans `console_scripts` entry points for Click/typer CLIs
- **Serve any CLI**: `click-to-mcp serve <name>` wraps any discovered CLI as an MCP server
- **HTTP+SSE transport**: `click-to-mcp serve-http <name>` serves over HTTP for web-based clients (v0.3.0+)
- **Supports both Click and Typer**: Full compatibility with both frameworks
- **Nested command groups**: Handles subcommand groups recursively with prefixed tool names
- **Parameter introspection**: Correctly maps Click options, arguments, types, enums, defaults, and help text to JSON Schema
- **Full MCP protocol**: Implements `initialize`, `tools/list`, `tools/call` over stdio and HTTP+SSE
- **Health endpoint**: HTTP servers expose `/health` for monitoring and load balancers

## Transports

### Stdio (default)

Best for local CLI-based MCP clients (Claude Code, Cursor, Cline). No extra dependencies needed.

```bash
click-to-mcp serve <name>
```

### HTTP+SSE (v0.3.0+)

Best for web-based MCP clients, remote access, and multi-user setups. Requires the `[http]` extra.

```bash
# Install HTTP dependencies
pip install "click-to-mcp[http]"

# Start an HTTP+SSE server
click-to-mcp serve-http <name> --host 127.0.0.1 --port 8000
```

Endpoints:
| Endpoint | Method | Description |
|---|---|---|
| `/sse` | GET | SSE stream (server-to-client events) |
| `/messages` | POST | JSON-RPC message endpoint |
| `/health` | GET | Health check (JSON status) |

Configure your MCP client with the SSE URL:
```json
{
  "mcpServers": {
    "my-cli": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

## MCP Protocol

Click-to-MCP implements the standard MCP protocol with:

- `initialize` â€” protocol handshake (returns server capabilities)
- `tools/list` â€” discover all CLI commands as MCP tools with JSON Schema inputs
- `tools/call` â€” invoke a CLI command with typed arguments

## Integration with Existing CLIs

Add an MCP server entry point to any Click/typer CLI:

```python
# cli.py â€” add a subcommand to run as MCP server
import typer
from click_to_mcp import run

app = typer.Typer(...)

@app.command()
def mcp():
    """Run as an MCP server over stdio."""
    from click_to_mcp import run
    run(app)
```

Then agents can use it as: `your-cli mcp`

## Development

```bash
git clone https://github.com/Coding-Dev-Tools/click-to-mcp
cd click-to-mcp
pip install -e ".[dev,http]"
python -m pytest tests/ -v          # 23 tests (12 stdio + 11 HTTP)
click-to-mcp demo                    # starts MCP stdio server for demo CLI
click-to-mcp demo-http               # starts MCP HTTP+SSE server on port 8000
```

## Pricing

click-to-mcp is **free and open source** under MIT. No license key required, no rate limits, no telemetry.

It also works with any [Revenue Holdings](https://coding-dev-tools.github.io/revenueholdings.dev/) CLI tool â€” even on the free tier.

## License

MIT

---

<sub>Part of [Revenue Holdings](https://coding-dev-tools.github.io/revenueholdings.dev/) â€” developer CLI tools built by autonomous AI agents.</sub>

