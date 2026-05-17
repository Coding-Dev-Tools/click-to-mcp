## Title: Turn any Python CLI into an MCP server in 30 seconds (open source)

**Subreddit**: r/Python

I built click-to-mcp — a tool that auto-wraps any Click/typer CLI as an MCP (Model Context Protocol) server with zero code changes.

**Why this matters**: The MCP ecosystem is exploding (66M+ FastMCP downloads), and every AI coding agent now supports it. But until now, making a CLI tool MCP-compatible meant writing a separate server for each one.

click-to-mcp parses your CLI at runtime, maps every command/flag/argument to MCP tool definitions, and generates schemas automatically. No new dependencies in your CLI tool.

```bash
pip install click-to-mcp
click-to-mcp discover            # Find all Click CLIs in your env
click-to-mcp serve your-cli      # Serve as MCP server (stdio)
click-to-mcp serve-http your-cli --port 8000  # Or over HTTP
```

Once served, Claude Desktop, Cursor, Claude Code, Codex, and any MCP client can call your CLI tools directly.

Open source, MIT: https://github.com/Coding-Dev-Tools/click-to-mcp

Would love feedback! What Python CLIs do you wish had MCP support?
