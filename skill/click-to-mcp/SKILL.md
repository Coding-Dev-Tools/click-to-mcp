---
name: click-to-mcp
description: Auto-wrap any Click or typer Python CLI as an MCP server with zero code changes. Use this skill whenever the user wants to expose a CLI tool to an AI agent via MCP, needs to convert a Click/typer app into an MCP server, wants to run an existing CLI through an LLM, or asks about bridging command-line tools and AI agents. Also use when the user mentions MCP server creation from CLIs, CLI-to-MCP conversion, or making Python tools AI-accessible.
license: Apache-2.0
compatibility: Requires Python 3.10+ and click or typer. Install via pip, uvx, or npm.
metadata:
  author: Coding-Dev-Tools
  version: "1.0"
  repository: "https://github.com/Coding-Dev-Tools/click-to-mcp"
---

# click-to-mcp: Turn CLIs into MCP Servers

## Overview

click-to-mcp automatically wraps any Python CLI built with Click or typer as an MCP (Model Context Protocol) server. No code changes required — every CLI command becomes an MCP tool that AI agents can call directly.

This works because Click and typer CLIs already define structured interfaces (commands, arguments, options, help text). click-to-mcp reflects on those interfaces and generates MCP tool definitions at runtime.

## When to Use

- User has a Click/typer CLI and wants it callable from Claude, Cursor, or any MCP client
- User wants to build an MCP server without writing boilerplate
- User asks "how do I make my CLI work with AI agents?"
- User mentions MCP, Click, typer, or CLI-to-agent bridging

## Quick Start

### 1. Install

```bash
pip install click-to-mcp
# or: uvx click-to-mcp
# or: npm install -g click-to-mcp
```

### 2. Discover available CLIs

```bash
click-to-mcp discover
```

This scans installed Python packages for Click/typer CLIs and lists them with their commands and options.

### 3. Serve a CLI as an MCP server (stdio)

```bash
click-to-mcp serve <package.module:cli_object>
```

Example: `click-to-mcp serve my_app.cli:app`

### 4. Serve over HTTP+SSE

```bash
click-to-mcp serve-http <package.module:cli_object> --port 8080
```

### 5. Serve over Streamable HTTP

```bash
click-to-mcp serve-http-streamable <package.module:cli_object> --port 8080
```

## How It Works

1. **Import**: Loads the CLI object from the specified Python module path
2. **Reflect**: Inspects all commands, subcommands, arguments, and options
3. **Map**: Converts each CLI command into an MCP tool with a matching input schema
4. **Serve**: Starts an MCP server exposing all tools via the chosen transport

CLI option types are mapped to JSON Schema types:
- `click.STRING` → `string`
- `click.INT` → `integer`
- `click.FLOAT` → `number`
- `click.BOOL` → `boolean`
- `click.Path` → `string` (with format hint)
- `click.Choice` → `string` (with enum)

## Transport Options

| Transport | Command | Use Case |
|-----------|---------|----------|
| stdio | `serve` | Local MCP clients (Claude Code, IDE extensions) |
| HTTP+SSE | `serve-http` | Remote access, web integrations |
| Streamable HTTP | `serve-http-streamable` | Modern HTTP transport, stateless JSON |

## Claude Code Plugin

click-to-mcp is also installable as a Claude Code plugin:

```
/plugin install click-to-mcp@Coding-Dev-Tools/click-to-mcp
```

This runs the built-in demo CLI as an MCP server, exposing `greet`, `calculate`, and `config` tools.

## Common Patterns

### Wrap an existing CLI

```bash
# If your CLI is installed as a package
click-to-mcp serve mypackage.cli:main

# If it's a local script
PYTHONPATH=/path/to/project click-to-mcp serve mymodule:app
```

### Multiple CLIs

You can serve different CLIs on different ports:

```bash
click-to-mcp serve-http app1.cli:main --port 8001 &
click-to-mcp serve-http app2.cli:main --port 8002 &
```

### With environment variables

CLI options that accept `envvar` are supported. The MCP tool will accept the option as a parameter, falling back to the environment variable if not provided.

## Troubleshooting

- **ImportError**: Ensure the package is installed and the module path is correct. Use `click-to-mcp discover` to find available CLIs.
- **"No Click groups found"**: The module path must point to a Click Group (not a bare command). For typer, use the `.cli` attribute: `my_app:app.cli`
- **Transport errors**: For HTTP modes, ensure the port is free and the client supports the chosen transport (SSE vs Streamable HTTP).

## Pitfalls

- The CLI must use Click or typer — argparse-only CLIs are not supported
- Subcommand groups are flattened into top-level tools (e.g., `db migrate` becomes tool `db_migrate`)
- File-path options are passed as strings; the server does not validate file existence
- Commands with `is_eager=True` options may behave differently when called as MCP tools

## Scripts

- [`discover`](./scripts/discover) — Scan installed Python packages for Click/typer CLIs
- [`serve`](./scripts/serve) — Serve a CLI as an MCP server (stdio transport)

## Reference Files

- [CLI Discovery Guide](./references/discovery-guide.md) — How discover scans and identifies CLIs
- [MCP Transport Details](./references/transports.md) — Deep dive into stdio, SSE, and Streamable HTTP modes
