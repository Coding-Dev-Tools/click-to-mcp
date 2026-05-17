# Show HN: click-to-mcp — Auto-wrap any CLI as an MCP server with zero code changes

Hi HN,

I built click-to-mcp because I was tired of rewriting CLI tools as MCP servers every time I wanted AI agents to use them.

**The problem**: MCP (Model Context Protocol) is exploding — 66M+ FastMCP downloads, every AI coding agent supports it. But making a CLI tool MCP-compatible currently means writing a separate server for each tool.

**The solution**: click-to-mcp auto-discovers all Click/typer CLIs in your environment and wraps them as MCP servers. No code changes, no new dependencies in your CLI tool.

```bash
# Install
pip install click-to-mcp

# Discover CLIs available in your environment
click-to-mcp discover

# Serve any CLI as an MCP server (stdio mode)
click-to-mcp serve my-cli

# Or over HTTP for remote/web-based MCP clients
click-to-mcp serve-http my-cli --port 8000
```

Once served, any MCP client (Claude Desktop, Cursor, Claude Code, Codex) can call your CLI tools as native MCP tools.

**How it works**: click-to-mcp parses the Click/typer command tree at runtime, maps commands/flags/arguments to MCP tool definitions, and generates schemas automatically. It supports:
- Click CLIs (argparse-based)
- Typer CLIs
- Nested command groups
- All parameter types (options, arguments, flags, choices)
- Custom validation patterns
- Stdio and HTTP+SSE transport

**Current status**: Open source under MIT. Part of the Revenue Holdings ecosystem. Works with Python 3.9+.

Would love feedback — what CLIs do you wish were MCP-servable?

---

*Why I built this**: Our team runs 10 CLI tools built entirely by autonomous AI agents. When we added MCP support to each one individually, it was painful. click-to-mcp lets us (and anyone else) MCP-enable their entire CLI suite with one command.
